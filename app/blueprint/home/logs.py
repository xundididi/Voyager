import math
import os

from flask import render_template
from flask import request
from flask import jsonify

from app.blueprint import admin
from app.blueprint import admin_required
from app.lib.utils.tools import get_page
from app import mongo


@admin.route("/logs")
@admin_required
def logs():
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
        coll = mongo.db.exports
        result = coll.find({}).sort([("timestamp", -1)]).limit(20).skip(limit_start)

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

        return render_template('logs.html', datas=datas)


@admin.route("/logs_controllers", methods=["POST"])
@admin_required
def logs_controllers():
    if request.method == "POST":

        task_id = request.form.get('task_id', None)
        action = request.form.get('action', None)

        if action == "delete":
            file_object = mongo.db.exports.find_one({'id': task_id})
            file_path = file_object["full_path"]

            if os.path.exists(file_path):
                os.unlink(file_path)
            mongo.db.exports.delete_one({'id': task_id})

            data = {"status": 200, "msg": "日志删除成功"}
            return jsonify(data)

        if action == "export":

            if mongo.db.exports.find_one({'id': task_id})["status"] != "Finished":
                data = {"status": 403, "msg": "任务尚未完成"}
                return jsonify(data)

            file_object = mongo.db.exports.find_one({'id': task_id})
            file_path = file_object["file_path"]

            data = {"status": 200, "file_url": file_path}
            return jsonify(data)
