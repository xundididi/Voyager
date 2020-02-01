import datetime

from flask import render_template
from flask import request
from flask import redirect
from flask import jsonify
from flask import url_for
from flask import session

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from app.blueprint import admin
from app.blueprint import admin_required
from app import mongo


@admin.route("/add")
def add():
    name = "luffy"
    password = "s1riu5"

    if mongo.db.users.find_one({'name': name}) == None:
        user = {'name': name, 'age': 18, 'password_hash': generate_password_hash(password=password)}
        mongo.db.users.insert_one(user)

    return "OK"


@admin.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form.get('username', None)
        password = request.form.get('password', None)

        user = mongo.db.users.find_one({'name': username})

        if user is None:
            result = {"status": 403, "msg": "用户名或者是密码错误"}
            return jsonify(result)

        if check_password_hash(pwhash=user["password_hash"], password=password):
            session["admin"] = username

            data = {"status": 200, "url_jump": "/"}
            return jsonify(data)


        else:

            result = {"status": 403, "msg": "用户名或者是密码错误"}
            return jsonify(result)

    return render_template('login.html')


@admin.route("/")
@admin_required
def index():
    if request.method == "GET":
        return render_template('index.html')


@admin.route("/welcome")
@admin_required
def welcome():
    if request.method == "GET":
        current_time = datetime.datetime.now()
        items_count = mongo.db.items.count_documents({})
        tasks_count = mongo.db.tasks.count_documents({})
        domains_count = mongo.db.subdomains.count_documents({})
        ports_count = mongo.db.ports.count_documents({})
        vuls_count = mongo.db.vuls.count_documents({})

        return render_template('welcome.html', **locals())


@admin.route("/logout")
@admin_required
def logout():
    session.pop('admin')
    return redirect(url_for('admin.login'))


@admin.route("/change_pwd", methods=["GET", "POST"])
@admin_required
def change_passwd():
    # 修改密码的视图函数

    if request.method == "GET":
        return render_template('change_pwd.html')

    if request.method == "POST":

        old_pass = request.form.get('old_passwd', None)
        new_pass = request.form.get('new_password', None)
        new_confirm = request.form.get('new_confirm', None)

        username = session.get("admin")

        user = mongo.db.users.find_one({'name': username})

        if not check_password_hash(pwhash=user["password_hash"], password=old_pass):
            data = {"status": 403, "msg": "旧密码错误"}
            return jsonify(data)

        if new_pass != new_confirm:
            data = {"status": 403, "msg": "新密码不匹配"}
            return jsonify(data)

        mongo.db.users.update_one(
            {'name': username},
            {'$set': {
                'password_hash': generate_password_hash(password=new_pass)

            }
            }
        )

        data = {"status": 200, "msg": "密码修改成功"}
        return jsonify(data)
