from app.config import DOCKER_CLIENT
from app.lib.handler.decorator import threaded
from app.lib.core import formatnum
from app import mongo

import time
import datetime
import ast


class Controller(object):
    """
    用来控制docker任务的核心函数
    """

    @staticmethod
    @threaded
    def stop_contain(contain_id):
        """
        用来终止启动的容器
        :param contain_id:8462ccf520899aff47b7bdb6b8f0fa65cc43f24c214a26dd94f2d58425bd6799
        :return:
        """

        try:

            if DOCKER_CLIENT.containers.get(contain_id).status == "running":
                docker_object = DOCKER_CLIENT.containers.get(contain_id)
                docker_object.stop()

                return True
            else:

                return True
        except:
            return False

    @staticmethod
    @threaded
    def subdomain_scan(uid):
        """
        添加域名扫描任务
        :param domain: example.com
        :param uid: c2385a01-bb0a-40a3-8694-05a31a440ba6
        :return:
        """
        # 有任务在执行的时候先暂停
        while True:

            task = mongo.db.tasks.find_one({'id': uid})

            if task == None:
                return True

            if mongo.db.tasks.find({'status': "Running"}).count() > 1:
                time.sleep(5)

            else:
                break

        contain = DOCKER_CLIENT.containers.run("ap0llo/oneforall:0.0.8", [uid], remove=True, detach=True,
                                               auto_remove=True,
                                               network="host")

        mongo.db.tasks.update_one({"id": uid}, {"$set": {"contain_id": contain.id}})


        # 心跳线程用来更新任务状态
        while True:

            task_dir = mongo.db.tasks.find_one({"id": uid})
            if task_dir == None:
                return True

            process_json = ast.literal_eval(task_dir["hidden_host"])

            if len(process_json) == 0:
                time.sleep(10)

            tasks_num = task_dir["live_host"]

            now_progress = 0
            # 统计总任务进度
            for k, v in process_json.items():
                progress_ = formatnum(v)
                now_progress = now_progress + progress_

            progress = '{0:.2f}%'.format(now_progress / tasks_num)


            if progress == "100.00%":
                mongo.db.tasks.update_one(
                    {"id": uid},
                    {'$set': {
                        'progress': "100.00%",
                        'status': 'Finished',
                        'end_time': datetime.datetime.now(),
                        'total_host': mongo.db.subdomains.find({'pid': uid}).count(),

                    }
                    }
                )
                return True

            else:
                mongo.db.tasks.update_one(
                    {"id": uid},
                    {'$set': {
                        'progress': progress

                    }
                    }
                )

            time.sleep(3)


    @staticmethod
    @threaded
    def ports_scan(uid):
        """
        添加域名扫描任务
        :param domain: example.com
        :param uid: c2385a01-bb0a-40a3-8694-05a31a440ba6
        :return:
        """

        # 有任务在执行的时候先暂停
        while True:

            task = mongo.db.tasks.find_one({'id': uid})

            if task == None:
                return True

            if mongo.db.tasks.find({'status': "Running"}).count() > 1:
                time.sleep(5)

            else:
                break

        contain = DOCKER_CLIENT.containers.run("ap0llo/nmap:7.80", [uid], remove=True, detach=True,
                                               auto_remove=True,
                                               network="host")

        mongo.db.tasks.update_one({"id": uid}, {"$set": {"contain_id": contain.id}})

        return True
