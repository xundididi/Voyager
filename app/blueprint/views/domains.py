import math
import datetime

from flask import render_template
from flask import request
from flask import jsonify
from flask import session

from app.blueprint import admin
from app.blueprint import admin_required
from app.lib.utils.tools import get_page
from app.lib.utils.tools import get_uuid
from app.lib.utils.tools import json_to_excel
from app.lib.core.agent import Controller
from app.extensions import mongo


@admin.route("/domian_lists", methods=["GET"])
@admin_required
def domains():
    if request.method == "GET":

        p = request.args.get('p')
        show_status = 0
        if not p:
            p = 1
        else:
            p = int(p)
            if p > 1:
                show_status = 1

        limit_start = (p - 1) * 20
        coll = mongo.db.tasks
        result = coll.find({"hack_type": "域名扫描"}).sort([("create_date", -1)]).limit(20).skip(limit_start)
        '''总页数'''
        total = coll.find({}).count()
        page_total = int(math.ceil(total / 20))
        page_list = get_page(page_total, p)

        datas = {
            'data_list': result,
            'p': p,
            'page_total': page_total,
            'show_status': show_status,
            'page_list': page_list
        }

        return render_template('domain/domians_list.html', datas=datas)


@admin.route("/domian_add", methods=["GET"])
@admin_required
def domains_add():
    if request.method == "GET":
        items = mongo.db.items.find({})
        new_list = list()
        for i in items:
            new_list.append(i["project"])
        return render_template('domain/domains_add.html', items=new_list)


@admin.route("/domains_controllers", methods=["POST"])
@admin_required
def domains_controllers():
    if request.method == "POST":
        domain_name = request.form.get('domain', None)
        project = request.form.get('project', None)
        task_id = request.form.get('task_id', None)
        action = request.form.get('action', None)

        if action == "add":
            if project == None or domain_name == None or len(project) == 0:
                result = {"status": 403, "msg": "值不能为空"}
                return jsonify(result)

            if mongo.db.tasks.find({'parent_name': project, "hack_type": "域名扫描"}).count() > 0:
                result = {"status": 403, "msg": "域名扫描项目已存在"}
                return jsonify(result)

            new_list = [ii for ii in domain_name.split("\n") if len(ii) > 0]

            target_name = ",".join(new_list)

            task_id = get_uuid()

            task = {"id": task_id, "create_date": datetime.datetime.now(), "parent_name": project,
                    "target": target_name, "task_type": "即时任务", "hack_type": "域名扫描", "status": "Running",
                    "progress": "0.00%", "contain_id": "Null", "end_time": "Null",
                    "live_host": len(new_list), "hidden_host": "{}", "total_host": 0,
                    "user": session.get("admin")}

            mongo.db.tasks.insert_one(task)

            Controller.subdomain_scan(task_id)

            data = {"status": 200, "msg": "项目添加成功"}
            return jsonify(data)

        if action == "delete":
            task = mongo.db.tasks.find_one({'id': task_id})
            if task["contain_id"] != "Null":
                Controller.stop_contain(task["contain_id"])

            mongo.db.tasks.delete_one({'id': task_id})
            mongo.db.subdomains.delete_many({'pid': task_id})
            mongo.db.exports.delete_many({'pid': task_id})

            data = {"status": 200, "msg": "项目删除成功"}
            return jsonify(data)

        if action == "export":
            if mongo.db.tasks.find_one({'id': task_id})["status"] != "Finished":
                result = {"status": 403, "msg": "任务还没有完成"}
                return jsonify(result)

            new_target = []

            subdomains = mongo.db.subdomains.find(
                {'parent_name': mongo.db.tasks.find_one({'id': task_id})["parent_name"]})

            for i in subdomains:
                new_dict = dict()
                new_dict["父级项目"] = i["parent_name"]
                new_dict["域名"] = i["subdomain_name"]
                new_dict["时间"] = i["create_date"].strftime("%Y-%m-%d %H:%M:%S")
                new_dict["端口"] = i["port"]
                new_dict["IP地址"] = i["ips"]
                new_dict["标题"] = i["title"]
                new_dict["指纹"] = i["banner"]

                new_target.append(new_dict)

            if len(new_target) == 0:
                result = {"status": 403, "msg": "没有域名结果"}
                return jsonify(result)

            if mongo.db.exports.find_one({"pid": task_id}) != None:
                result = {"status": 403, "msg": "任务已存在，请前往导出页面查看"}
                return jsonify(result)

            else:

                # 得到即将下载文件的路径和名称
                path, full_path = json_to_excel(new_target)

                log = {"id": get_uuid(), "hack_type": "域名扫描",
                       "parent_name": mongo.db.tasks.find_one({'id': task_id})["parent_name"], "file_path": path,
                       "status": "Finished", "user": session.get("admin"), "create_date": datetime.datetime.now(),
                       "full_path": full_path}

                mongo.db.exports.insert(log)

                result = {"status": 200, "file_url": path}
                return jsonify(result)

        data = {"status": 403, "msg": "操作失败"}
        return jsonify(data)
