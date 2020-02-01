import docker
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOCKER_CLIENT = docker.from_env()

# AWVS配置相关
AWVS_API_KEY = ""
AWVS_HOST_ADDRESS = ""


# Flask配置文件
class BaseConfig(object):
    MONGO_URI = "mongodb://root:shad0wBrok3r@127.0.0.1:27017/pioneer1?authSource=admin"
    SECRET_KEY = "NEVEW"


class DevConfig(BaseConfig):
    DEBUG = True
