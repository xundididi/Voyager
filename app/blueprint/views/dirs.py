import math
import datetime
import ast

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
from app.lib.core.agent_dir import ControllerDirs
from app.extensions import mongo


@admin.route("/dir_lists", methods=["GET"])
@admin_required
def dirs():
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
        result = coll.find({"hack_type": "目录扫描"}).sort([("create_date", -1)]).limit(20).skip(limit_start)
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

        return render_template("dirs/dirs_list.html", datas=datas)


@admin.route("/dirs_add", methods=["GET", "POST"])
@admin_required
def dirs_add():
    if request.method == "GET":
        items = mongo.db.items.find({})
        new_list = list()
        for i in items:
            new_list.append(i["project"])
        return render_template('dirs/dirs_add.html', items=new_list)

    if request.method == "POST":

        project_all = list()
        tasks = mongo.db.tasks.find({'status': "Finished", "$or": [{"hack_type": "端口扫描"}, {"hack_type": "域名扫描"}]})
        for i in tasks:

            if i['parent_name'] not in project_all:
                project_all.append(i['parent_name'])

        # 如果没有子域名扫描项目
        if len(project_all) == 0:
            result = {"status": 200, "list_info": project_all}
            return jsonify(result)

        result = {"status": 200, "list_info": project_all}
        return jsonify(result)


@admin.route("/dirs_controllers", methods=["POST"])
@admin_required
def dirs_controller():
    if request.method == "POST":
        project = request.form.get('project', None)
        child_task_name = request.form.get('target_id', None)
        ip_address = request.form.get("ip_address", None)
        ext = request.form.get("ext", None)
        task_id = request.form.get('task_id', None)
        action = request.form.get('action', None)

        if action == "add":

            if len(ip_address) != 0:
                # 输入文本的方案

                # [{'http_address': 'http://192.168.3.2:8123', 'keydict': 'common.txt', 'parent_name': '齐鲁师范学院', 'pid': '141aa854-a78c-42fe-bbf4-99b7d0be37aa'},]
                pid = get_uuid()
                target_list = list()

                for i in ip_address.split('\n'):

                    if len(i) > 0:
                        new_dict = dict()
                        new_dict["http_address"] = i
                        new_dict["keydict"] = ",".join(ast.literal_eval(ext))
                        new_dict["parent_name"] = project
                        new_dict["pid"] = pid

                        target_list.append(new_dict)

                task = {"id": pid, "create_date": datetime.datetime.now(), "parent_name": project,
                        "target": str(target_list), "task_type": "即时任务", "hack_type": "目录扫描", "status": "Running",
                        "progress": "0.00%", "contain_id": "Null", "end_time": "Null",
                        "live_host": 0, "hidden_host": len(target_list), "total_host": "{}",
                        "user": session.get("admin")}

                mongo.db.tasks.insert_one(task)

                ControllerDirs.thread_start(method="lilith", project=project, task_name="s1riu5", pid=pid)

                data = {"status": 200, "msg": "项目添加成功"}
                return jsonify(data)

            if child_task_name != None:

                task_id_new = get_uuid()
                task = {"id": task_id_new, "create_date": datetime.datetime.now(), "parent_name": project,
                        "target": "Null", "task_type": "即时任务", "hack_type": "目录扫描", "status": "Running",
                        "progress": "0.00%", "contain_id": "Null", "end_time": "Null",
                        "live_host": 0, "hidden_host": 0, "total_host": "{}", "user": session.get("admin")}

                mongo.db.tasks.insert_one(task)

                ControllerDirs.thread_start(method="adam", project=project, task_name=child_task_name, pid=task_id_new)

            data = {"status": 200, "msg": "项目添加成功"}
            return jsonify(data)

        if action == "delete":
            task = mongo.db.tasks.find_one({'id': task_id})
            if task["contain_id"] != "Null":
                Controller.stop_contain(task["contain_id"])
            mongo.db.tasks.delete_one({'id': task_id})
            mongo.db.vul_dirs.delete_many({'pid': task_id})
            mongo.db.exports.delete_many({'pid': task_id})

            data = {"status": 200, "msg": "项目删除成功"}
            return jsonify(data)

        if action == "export":
            if mongo.db.tasks.find_one({'id': task_id})["status"] != "Finished":
                result = {"status": 403, "msg": "任务还没有完成"}
                return jsonify(result, safe=False)

            new_target = []

            subdomains = mongo.db.dir_vuls.find(
                {'pid': task_id})

            for i in subdomains:
                new_dict = dict()
                new_dict["父级项目"] = i["parent_name"]
                new_dict["地址"] = i["vul_path"]
                new_dict["状态"] = i["status_code"]
                new_dict["创建时间"] = i["create_date"]

                new_target.append(new_dict)

            if len(new_target) == 0:
                result = {"status": 403, "msg": "没有结果"}
                return jsonify(result)

            if mongo.db.exports.find_one({"pid": task_id}) != None:
                result = {"status": 403, "msg": "任务已存在，请前往导出页面查看"}
                return jsonify(result)

            else:

                # 得到即将下载文件的路径和名称
                path, full_path = json_to_excel(new_target)

                log = {"id": get_uuid(), "hack_type": "目录扫描",
                       "parent_name": mongo.db.tasks.find_one({'id': task_id})["parent_name"], "file_path": path,
                       "status": "Finished", "user": session.get("admin"), "create_date": datetime.datetime.now(),
                       "full_path": full_path}

                mongo.db.exports.insert(log)

                result = {"status": 200, "file_url": path}
                return jsonify(result)

        data = {"status": 403, "msg": "操作失败"}
        return jsonify(data)
