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
from app import mongo


@admin.route("/items")
@admin_required
def items():
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
        coll = mongo.db.items
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

        return render_template('items/items_list.html', datas=datas)


@admin.route("/items_add", methods=["GET"])
@admin_required
def items_add():
    if request.method == "GET":
        return render_template('items/items_add.html')


@admin.route("/items_controllers", methods=["POST"])
@admin_required
def items_controllers():
    if request.method == "POST":
        item_name = request.form.get('project', None)
        action = request.form.get('action', None)

        if action == "add":
            item = mongo.db.items.find_one({'project': item_name})

            if item != None:
                data = {"status": 403, "msg": "项目已存在"}
                return jsonify(data)

            item_id = get_uuid()
            item = {'project': item_name, 'create_date': datetime.datetime.now(), "id": item_id,
                    "user": session.get("admin")}
            mongo.db.items.insert_one(item)

            data = {"status": 200, "msg": "项目添加成功"}
            return jsonify(data)

        if action == "delete":
            mongo.db.items.delete_one({'project': item_name})
            mongo.db.tasks.delete_many({"parent_name": item_name})
            mongo.db.ports.delete_many({"parent_name": item_name})
            mongo.db.subdomains.delete_many({"parent_name": item_name})
            mongo.db.vuls.delete_many({"parent_name": item_name})
            mongo.db.dir_vuls.delete_many({"parent_name": item_name})

            data = {"status": 200, "msg": "项目删除成功"}
            return jsonify(data)

        data = {"status": 403, "url_jump": "任务添加失败"}
        return jsonify(data)
