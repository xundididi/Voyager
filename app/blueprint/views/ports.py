import math
import datetime
import re

from flask import render_template
from flask import request
from flask import jsonify
from flask import session

from app.lib.utils.tools import json_to_excel
from app.lib.utils.tools import get_ip_list
from app.lib.utils.tools import get_list_ip
from app.lib.utils.tools import list_duplicate
from app.lib.utils.tools import get_port_list
from app.lib.utils.tools import get_page
from app.lib.utils.tools import get_uuid
from app.lib.core.agent import Controller
from app.blueprint import admin
from app.blueprint import admin_required
from app.extensions import mongo


@admin.route("/port_lists", methods=["GET"])
@admin_required
def ports():
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
        result = coll.find({"hack_type": "端口扫描"}).sort([("create_date", -1)]).limit(20).skip(limit_start)
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

        return render_template('ports/ports_list.html', datas=datas)


@admin.route("/ports_add", methods=["GET", "POST"])
@admin_required
def ports_add():
    if request.method == "GET":
        items = mongo.db.items.find({})
        new_list = list()
        for i in items:
            new_list.append(i["project"])
        return render_template('ports/ports_add.html', items=new_list)

    if request.method == "POST":

        project_all = list()
        tasks = mongo.db.tasks.find({'status': "Finished", "hack_type": "域名扫描"})
        for i in tasks:
            project_all.append(i['parent_name'])
        new_list = list()

        # 如果没有子域名扫描项目
        if len(project_all) == 0:
            result = {"status": 200, "list_info": new_list}
            return jsonify(result)

        for i in project_all:
            new_dict = dict()
            new_dict["project_name"] = i
            new_dict["task_id"] = mongo.db.tasks.find_one({'parent_name': i})["id"]
            new_list.append(new_dict)

        result = {"status": 200, "list_info": new_list}
        return jsonify(result)


@admin.route("/ports_controllers", methods=["POST"])
@admin_required
def ports_controllers():
    if request.method == "POST":

        action = request.form.get("action", None)
        project = request.form.get("project", None)
        target_id = request.form.get("target_id", None)
        ip_address = request.form.get("ip_address", None)
        ports = request.form.get("ports", None)
        task_id = request.form.get("task_id", None)
        option = request.form.get('option', None)  # full each

        if action == "add":
            if ports == None or action == None:
                result = {"status": 403, "msg": "值不能为空"}
                return jsonify(result)

            if mongo.db.tasks.find({'parent_name': project, "hack_type": "端口扫描"}).count() > 0:
                result = {"status": 403, "msg": "项目已存在"}
                return jsonify(result)

            if target_id == None and len(ip_address) > 0:
                port = ",".join(ports.split("\n"))
                # target = str([",".join(ip_address.split("\n")), port])
                target = str([",".join([i for i in ip_address.split("\n") if len(i) > 0]), port])

                len_ip = get_ip_list(ip_address.split("\n"))

                if not len_ip:
                    result = {"status": 403, "msg": "IP地址格式错误"}
                    return jsonify(result)

                if not get_port_list(ports.split("\n")):
                    result = {"status": 403, "msg": "端口地址格式错误"}
                    return jsonify(result)

                uid = get_uuid()

                task = {"id": uid, "create_date": datetime.datetime.now(), "parent_name": project,
                        "target": target, "task_type": "即时任务", "hack_type": "端口扫描", "status": "Running",
                        "progress": "0.00%", "contain_id": "Null", "end_time": "Null",
                        "live_host": 0, "hidden_host": len_ip, "total_host": 0, "user": session.get("admin")}

                mongo.db.tasks.insert_one(task)

                Controller.ports_scan(uid)

                result = {"status": 200, "msg": "任务创建成功"}
                return jsonify(result)

            if target_id != None and len(ip_address) == 0:

                task_subdomain = mongo.db.subdomains.find({"pid": target_id})

                new_list = []

                for i in task_subdomain:

                    lm = i["ips"]
                    ips = lm.split(",")
                    # 如果一个域名解析出了五个及以上的地址就认为是有CDN
                    if len(ips) < 5:
                        new_list = new_list + ips

                ips_list = list_duplicate(new_list)

                if option == "each":

                    port = ports.split("\n")

                    ip_lists = [','.join(get_list_ip(ips_list)), ",".join(port)]
                    len_ip = get_ip_list(ips_list)

                    if not len_ip:
                        result = {"status": 403, "msg": "IP地址格式错误"}
                        return jsonify(result)

                    if not get_port_list(ports.split("\n")):
                        result = {"status": 403, "msg": "端口地址格式错误"}
                        return jsonify(result)

                    uid = get_uuid()
                    task = {"id": uid, "create_date": datetime.datetime.now(), "parent_name": project,
                            "target": str(ip_lists), "task_type": "即时任务", "hack_type": "端口扫描", "status": "Running",
                            "progress": "0.00%", "contain_id": "Null", "end_time": "Null",
                            "live_host": 0, "hidden_host": len_ip, "total_host": 0, "user": session.get("admin")}

                    mongo.db.tasks.insert_one(task)

                    Controller.ports_scan(uid)

                    result = {"status": 200, "msg": "任务创建成功"}
                    return jsonify(result)

                if option == "full":

                    port = ports.split("\n")

                    new_c_list = []

                    for i in ips_list:

                        if not re.match(
                                r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
                                i):
                            continue

                        ip1, ip2, ip3, ip4 = i.split(".")
                        c_ip = f"{ip1}.{ip2}.{ip3}.1/24"
                        new_c_list.append(c_ip)

                    new_target_ip = list_duplicate(new_c_list)
                    target = [','.join(new_target_ip), ",".join(port)]

                    port = ports.split("\n")
                    len_ip = get_ip_list(new_target_ip)

                    if not len_ip:
                        result = {"status": 403, "msg": "IP地址格式错误"}
                        return jsonify(result)

                    if not get_port_list(ports.split("\n")):
                        result = {"status": 403, "msg": "端口地址格式错误"}
                        return jsonify(result)

                    uid = get_uuid()
                    task = {"id": uid, "create_date": datetime.datetime.now(), "parent_name": project,
                            "target": target, "task_type": "即时任务", "hack_type": "端口扫描", "status": "Running",
                            "progress": "0.00%", "contain_id": "Null", "end_time": "Null",
                            "live_host": 0, "hidden_host": 0, "total_host": len_ip, "user": session.get("admin")}

                    mongo.db.tasks.insert_one(task)

                    Controller.ports_scan(uid, port)

                    result = {"status": 200, "msg": "任务创建成功"}
                    return jsonify(result)

                result = {"status": 403, "msg": "任务失败"}
                return jsonify(result)

            else:

                result = {"status": 403, "msg": "任务失败"}
                return jsonify(result)

        if action == "delete":

            task = mongo.db.tasks.find_one({'id': task_id})

            if task == None:
                mongo.db.tasks.delete_one({'id': task_id})
                mongo.db.ports.delete_many({'pid': task_id})
                mongo.db.exports.delete_one({'id': task_id})

                result = {"status": 200, "msg": "任务删除成功"}
                return jsonify(result)

            if task["contain_id"] != "Null":
                Controller.stop_contain(task["contain_id"])

            mongo.db.tasks.delete_one({'id': task_id})
            mongo.db.ports.delete_many({'pid': task_id})
            mongo.db.exports.delete_many({'pid': task_id})

            result = {"status": 200, "msg": "任务删除成功"}
            return jsonify(result)

        if action == "export":
            if mongo.db.tasks.find_one({'id': task_id})["status"] != "Finished":
                result = {"status": 403, "msg": "任务还没有完成"}
                return jsonify(result, safe=False)

            new_target = []

            ports = mongo.db.ports.find({'pid': task_id})

            for i in ports:
                new_dict = dict()
                new_dict["父级项目"] = i["parent_name"]
                new_dict["IP地址"] = i["address"]
                new_dict["端口"] = i["port"]
                new_dict["服务"] = i["service"]
                new_dict["指纹"] = i["banner"]
                new_dict["创建时间"] = i["start"]
                new_dict["结束时间"] = i["end"]

                if "tag" in i:

                    new_dict["标签"] = i["tag"]
                else:
                    new_dict["标签"] = "Null"

                if "title" in i:
                    new_dict["标题"] = i["title"]
                else:
                    new_dict["标题"] = "Null"

                new_dict["服务"] = i["service"]

                new_target.append(new_dict)

            if mongo.db.exports.find_one({"pid": task_id}) != None:
                result = {"status": 403, "msg": "任务已存在，请前往导出页面查看"}
                return jsonify(result)

            else:
                # 得到即将下载文件的路径和名称
                path, full_path = json_to_excel(new_target)

                log = {"id": get_uuid(), "hack_type": "端口扫描",
                       "parent_name": mongo.db.tasks.find_one({'id': task_id})["parent_name"], "file_path": path,
                       "status": "Finished", "pid": task_id, "user": session.get("admin"),
                       "create_date": datetime.datetime.now(), "full_path": full_path}

                mongo.db.exports.insert(log)

                result = {"status": 200, "file_url": path}
                return jsonify(result)
