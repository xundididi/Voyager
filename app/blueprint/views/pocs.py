import datetime
import math

from flask import request
from flask import jsonify
from flask import render_template
from flask import session

from app.extensions import mongo
from app.blueprint import admin
from app.blueprint import admin_required
from app.lib.utils.tools import get_page

from app.lib.core.agent import Controller
from app.lib.core.agent_poc import ControllerPocs
from app.lib.utils.tools import get_uuid
from app.lib.utils.tools import json_to_excel


# POC漏洞扫描的逻辑
@admin.route("/poc_lists", methods=["GET"])
@admin_required
def pocs():
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
        result = coll.find({"hack_type": "POC扫描"}).sort([("create_date", -1)]).limit(20).skip(limit_start)

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

        return render_template('pocs/pocs_list.html', datas=datas)


@admin.route("/pocs_add", methods=["GET", "POST"])
@admin_required
def pocs_add():
    if request.method == "GET":
        items = mongo.db.items.find({})
        new_list = list()
        for i in items:
            new_list.append(i["project"])

        return render_template('pocs/pocs_add.html', items=new_list)

    if request.method == "POST":

        project_all = list()
        new_list = list()
        tasks = mongo.db.tasks.find(
            {'status': "Finished", "$or": [{"hack_type": "端口扫描"}, {"hack_type": "域名扫描"}, {"hack_type": "指纹识别"}]})
        for i in tasks:
            if i['total_host'] > 0 and i['parent_name'] not in project_all:
                project_all.append(i['parent_name'])

        # 如果没有子域名扫描项目
        if len(project_all) == 0:
            result = {"status": 200, "list_info": new_list}
            return jsonify(result)

        for i in project_all:
            new_dict = dict()
            new_dict["project_name"] = i
            # new_dict["task_id"] = mongo.db.tasks.find_one({'parent_name': i, "hack_type": "端口扫描"})["id"]
            new_list.append(new_dict)

        result = {"status": 200, "list_info": new_list}
        return jsonify(result)


@admin.route("/pocs_controllers", methods=["POST"])
@admin_required
def pocs_controllers():
    if request.method == "POST":

        action = request.form.get("action", None)
        project = request.form.get("project", None)
        target_name = request.form.get("target_name", None)
        task_id = request.form.get("task_id", None)

        if action == "add":
            if project == None or action == None or target_name == None:
                result = {"status": 403, "msg": "值不能为空"}
                return jsonify(result)

            uid = get_uuid()
            task = {"id": uid, "create_date": datetime.datetime.now(), "parent_name": project,
                    "target": "Null", "task_type": "即时任务", "hack_type": "POC扫描", "status": "Running",
                    "progress": "0.00%", "contain_id": "Null", "end_time": "Null",
                    "live_host": 0, "hidden_host": 0, "total_host": 0, "user": session.get("admin")}

            mongo.db.tasks.insert_one(task)

            ControllerPocs.thread_start(target_name, project, uid)

            data = {"status": 200, "msg": "项目添加成功"}
            return jsonify(data)

        if action == "delete":

            task = mongo.db.tasks.find_one({'id': task_id})

            if task == None:
                result = {"status": 403, "msg": "任务不存在"}
                return jsonify(result)

            if task["contain_id"] != "Null":
                Controller.stop_contain(task["contain_id"])
            mongo.db.tasks.delete_one({'id': task_id})
            mongo.db.pocs.delete_many({'pid': task_id})
            mongo.db.vuldocker.delete_many({'pid': task_id})
            mongo.db.vuls.delete_many({'pid': task_id})

            result = {"status": 200, "msg": "任务删除成功"}
            return jsonify(result)

        if action == "export":
            if mongo.db.tasks.find_one({'id': task_id})["status"] != "Finished":
                result = {"status": 403, "msg": "任务还没有完成"}
                return jsonify(result)

            new_target = []

            vuls = mongo.db.vuls.find({"pid": task_id})

            for i in vuls:
                new_dict = dict()
                new_dict["父级项目"] = i["parent_name"]
                new_dict["时间"] = i["create_date"].strftime("%Y-%m-%d %H:%M:%S")
                new_dict["IP地址"] = i["ip_address"]
                new_dict["端口"] = i["port"]
                new_dict["漏洞信息"] = i["vul_info"]
                new_dict["漏洞名称"] = i["vul_name"]

                new_target.append(new_dict)

            if len(new_target) == 0:
                result = {"status": 403, "msg": "没有漏洞"}
                return jsonify(result)

            if mongo.db.exports.find_one({"pid": task_id}) != None:
                result = {"status": 403, "msg": "任务已存在，请前往导出页面查看"}
                return jsonify(result)

            else:

                # 得到即将下载文件的路径和名称
                path, full_path = json_to_excel(new_target)

                log = {"id": get_uuid(), "hack_type": "漏洞扫描",
                       "parent_name": mongo.db.tasks.find_one({'id': task_id})["parent_name"], "file_path": path,
                       "status": "Finished", "user": session.get("admin"), "create_date": datetime.datetime.now(),
                       "full_path": full_path}

                mongo.db.exports.insert(log)

                result = {"status": 200, "file_url": path}
                return jsonify(result)

        data = {"status": 403, "msg": "操作失败"}
        return jsonify(data)
