import math
import datetime
import json

from flask import render_template
from flask import request
from flask import jsonify
from flask import session

from app.blueprint import admin
from app.blueprint import admin_required
from app.lib.utils.tools import get_page
from app.lib.utils.tools import get_uuid
from app.lib.utils.data import conf
from app.lib.core.datatype import AttribDict
from app.lib.core.awvs_core import AWVS
from app.extensions import mongo


@admin.route("/initiative_index")
@admin_required
def initiative_index():
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
        result = coll.find({"hack_type": "主动扫描"}).sort([("create_date", -1)]).limit(20).skip(limit_start)
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

        return render_template("initiative/initiative_list.html", datas=datas)


@admin.route("/initiative_add", methods=["GET", "POST"])
@admin_required
def initiative_add():
    if request.method == "GET":
        items = mongo.db.items.find({})
        new_list = list()
        for i in items:
            new_list.append(i["project"])

        return render_template('initiative/initiative_add.html', items=new_list)

    if request.method == "POST":

        project_all = list()
        new_list = list()
        tasks = mongo.db.tasks.find({'status': "Finished", "$or": [{"hack_type": "端口扫描"}, {"hack_type": "域名扫描"}]})
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
            new_list.append(new_dict)

        result = {"status": 200, "list_info": project_all}
        return jsonify(result)


@admin.route("/initiative_controllers", methods=["POST"])
@admin_required
def initiative_controller():
    if request.method == "POST":
        project = request.form.get('project', None)
        child_task_name = request.form.get('parent_project', None)
        ip_address = request.form.get("ip_address", None)
        task_id = request.form.get('task_id', None)
        action = request.form.get('action', None)

        if action == "add":

            if len(project) == 0:
                data = {"status": 403, "msg": "请指定项目名称"}
                return jsonify(data)

            if mongo.db.tasks.find_one({'hack_type': '主动扫描', 'status': "Running"}) != None:
                data = {"status": 403, "msg": "任务正在运行，请稍后添加"}
                return jsonify(data)

            if len(ip_address) != 0:
                # 输入文本的方案

                pid = get_uuid()
                target_list = list()
                for i in ip_address.split('\n'):

                    if len(i) > 0 and (i.startswith("http://") or i.startswith("https://")):
                        task_id = get_uuid()
                        new_dict = dict()
                        new_dict["http_address"] = i
                        new_dict["parent_name"] = project
                        new_dict["pid"] = task_id
                        new_dict["flag"] = "port"
                        target_list.append(new_dict)

                task = {"id": pid, "create_date": datetime.datetime.now(), "parent_name": project,
                        "target": json.dumps(target_list, ensure_ascii=False), "task_type": "即时任务", "hack_type": "主动扫描",
                        "status": "Running",
                        "progress": "0.00%", "contain_id": "Null", "end_time": "Null",
                        "live_host": 0, "hidden_host": "", "total_host": 0,
                        "user": session.get("admin")}

                conf.awvs = AttribDict(
                    {"method": "lilith", "pid": pid, "parent_name": project, "target": target_list})

                mongo.db.tasks.insert_one(task)
                awvs = AWVS()
                awvs.init()

                data = {"status": 200, "msg": "项目添加成功"}
                return jsonify(data)

            if child_task_name != None:
                # 从项目选择的方案
                task_id_new = get_uuid()
                task = {"id": task_id_new, "create_date": datetime.datetime.now(), "parent_name": project,
                        "target": "Null", "task_type": "即时任务", "hack_type": "主动扫描", "status": "Running",
                        "progress": "0.00%", "contain_id": "Null", "end_time": "Null",
                        "live_host": 0, "hidden_host": "", "total_host": "{}", "user": session.get("admin")}

                conf.awvs = AttribDict(
                    {"method": "adam", "pid": task_id_new, "parent_name": project, "child_name": child_task_name})
                mongo.db.tasks.insert_one(task)

                awvs = AWVS()
                awvs.init()

            data = {"status": 200, "msg": "项目添加成功"}
            return jsonify(data)

        if action == "delete":

            task = mongo.db.tasks.find_one({'id': task_id})
            if task == None:
                data = {"status": 200, "msg": "项目删除成功"}
                return jsonify(data)

            if len(task['hidden_host']) > 0:

                target = json.loads(task["hidden_host"])

                for i in target:
                    print(i)
                    AWVS.delete_target(i["target_id"])

            mongo.db.tasks.delete_one({'id': task_id})
            mongo.db.ports.delete_many({'pid': task_id})
            mongo.db.exports.delete_many({'pid': task_id})

            data = {"status": 200, "msg": "项目删除成功"}
            return jsonify(data)

        if action == "export":
            if mongo.db.tasks.find_one({'id': task_id})["status"] != "Finished":
                result = {"status": 403, "msg": "任务还没有完成"}
                return jsonify(result, safe=False)

            if mongo.db.exports.find_one({"pid": task_id}) != None:
                result = {"status": 403, "msg": "任务已存在，请前往导出页面查看"}
                return jsonify(result)

            else:
                uid = get_uuid()
                log = {"id": uid, "hack_type": "主动扫描",
                       "parent_name": mongo.db.tasks.find_one({'id': task_id})["parent_name"], "file_path": "Null",
                       "status": "Running", "user": session.get("admin"), "create_date": datetime.datetime.now(),
                       "full_path": "Null"}

                mongo.db.exports.insert(log)

                info = mongo.db.tasks.find_one({'id': task_id})["hidden_host"]

                AWVS().generate_pdf(json.loads(info), uid)

                result = {"status": 200, "msg": "任务建成，请前往导出页面"}
                return jsonify(result)

        data = {"status": 403, "msg": "操作失败"}
        return jsonify(data)
