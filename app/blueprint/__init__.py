from flask import Blueprint
from flask import session
from flask import redirect
from flask import url_for
from functools import wraps

admin = Blueprint("admin", __name__)


# 管理员登陆装饰器
def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if session.get('admin', None) is None:
            # 如果session中未找到该键，则用户需要登录
            return redirect(url_for('admin.login'))
        return func(*args, **kwargs)

    return decorated_function


from app.blueprint.views import pocs
from app.blueprint.views import ports
from app.blueprint.views import domains
from app.blueprint.views import dirs
from app.blueprint.views import finger
from app.blueprint.views import initiative
from app.blueprint.home import logs
from app.blueprint.home import items
from app.blueprint.home import index
