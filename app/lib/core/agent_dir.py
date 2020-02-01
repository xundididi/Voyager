from app import mongo
from app.config import DOCKER_CLIENT
from app.lib.core import waf_check
from app.lib.handler.decorator import threaded
from app.lib.core import formatnum

import datetime
import threading
import time
import queue
import ast

THREADS = 10


class ControllerDirs():
    # # 控制并发线程数
    # threads_queue = queue.Queue(maxsize=THREADS)
    # for i in range(THREADS):
    #     threads_queue.put_nowait(" ")

    # 存放目标线程数
    target_queue = queue.Queue()

    list_queue = queue.Queue()

    def __init__(self, method, task_name, project, pid):

        self.task_name = task_name
        self.project = project
        self.pid = pid

        self.method = method

    # waf检查函数
    def _waf_check(self):

        if self.method == "adam":

            ports = mongo.db.ports.find({"parent_name": self.task_name})
            domains = mongo.db.subdomains.find({"parent_name": self.task_name})

            for i in domains:
                new_dict = dict()
                new_dict["http_address"] = i["http_address"]
                new_dict["keydict"] = "asp.txt,common.txt,jsp.txt,php.txt"
                new_dict["parent_name"] = self.project
                new_dict["pid"] = self.pid
                self.target_queue.put_nowait(new_dict)

            for j in ports:
                if any([j["service"] == "http", j["service"] == "http-proxy", j["service"] == "https"]) \
                        and j["http_address"] != "unknown" and "keydict" in j:
                    new_dict = dict()
                    new_dict["http_address"] = j["http_address"]
                    new_dict["keydict"] = j["keydict"]
                    new_dict["parent_name"] = self.project
                    new_dict["pid"] = self.pid

                    self.target_queue.put_nowait(new_dict)

            while True:

                sess = mongo.db.tasks.find_one({"id": self.pid})

                # 项目被删除的时候
                if sess == None:
                    return True

                target_list = list()

                if self.target_queue.qsize() == 0:
                    break

                if self.target_queue.qsize() >= THREADS:

                    # 使用攻击对象attactObject的线程数来控制是否要启动新的线程
                    for index in range(0, THREADS):
                        # self.threads_queue.get()
                        param = self.target_queue.get()
                        attacker = threading.Thread(target=waf_check, args=(param, self.list_queue))
                        attacker.start()
                        target_list.append(attacker)


                else:
                    for index in range(0, self.target_queue.qsize()):
                        # self.threads_queue.get()
                        param = self.target_queue.get()
                        attacker = threading.Thread(target=waf_check, args=(param, self.list_queue))
                        attacker.start()
                        target_list.append(attacker)

                # And wait for them to all finish
                alive = True
                while alive:
                    alive = False
                    for thread in target_list:
                        if thread.isAlive():
                            alive = True
                            time.sleep(0.1)

            return list(self.list_queue.queue)

        if self.method == "lilith":

            sess = mongo.db.tasks.find_one({"id": self.pid})

            # 项目被删除的时候
            if sess == None:
                return "flag"

            target_list = list()

            target_content = sess["target"]

            for k in ast.literal_eval(target_content):

                self.target_queue.put_nowait(k)

            while True:

                if self.target_queue.qsize() == 0:
                    break

                if self.target_queue.qsize() >= THREADS:

                    # 使用攻击对象attactObject的线程数来控制是否要启动新的线程
                    for index in range(0, THREADS):
                        # self.threads_queue.get()
                        param = self.target_queue.get()
                        attacker = threading.Thread(target=waf_check, args=(param, self.list_queue))
                        attacker.start()
                        target_list.append(attacker)


                else:
                    for index in range(0, self.target_queue.qsize()):
                        # self.threads_queue.get()
                        param = self.target_queue.get()
                        attacker = threading.Thread(target=waf_check, args=(param, self.list_queue))
                        attacker.start()
                        target_list.append(attacker)

                alive = True
                while alive:
                    alive = False
                    for thread in target_list:
                        if thread.isAlive():
                            alive = True
                            time.sleep(0.1)

            return list(self.list_queue.queue)

    def dir_scan(self, info):

        sess = mongo.db.tasks.find_one({"id": self.pid})

        # 项目被删除的时候
        if sess == None:
            return True

        if len(info) == 0:
            mongo.db.tasks.update_one(
                {"id": self.pid},
                {'$set': {
                    'progress': "100.00%",
                    'status': 'Finished',
                    'end_time': datetime.datetime.now(),
                    'live_host': 0,

                }
                }
            )

            return True

        mongo.db.tasks.update_one(
            {"id": self.pid},
            {'$set': {
                'target': str(info),
                'hidden_host': len(info),

            }
            }
        )

        contain = DOCKER_CLIENT.containers.run("ap0llo/dirsearch:0.3.9", [self.pid], detach=True,
                                               network="host", auto_remove=True)

        mongo.db.tasks.update_one(
            {"id": self.pid},
            {'$set': {
                'contain_id': contain.id

            }
            }
        )

        # 心跳线程用来更新任务状态
        while True:

            task_dir = mongo.db.tasks.find_one({"id": self.pid})
            if task_dir == None:
                return "flag"

            process_json = ast.literal_eval(task_dir["total_host"])

            if len(process_json) == 0:
                time.sleep(10)

            tasks_num = task_dir["hidden_host"]

            now_progress = 0
            # 统计总任务进度
            for k, v in process_json.items():
                progress_ = formatnum(v)
                now_progress = now_progress + progress_

            progress = '{0:.2f}%'.format(now_progress / tasks_num)

            if progress == "100.00%":
                mongo.db.tasks.update_one(
                    {"id": self.pid},
                    {'$set': {
                        'progress': "100.00%",
                        'status': 'Finished',
                        'end_time': datetime.datetime.now(),
                        'live_host': mongo.db.dir_vuls.find({'pid': self.pid}).count(),

                    }
                    }
                )
                return True

            else:
                mongo.db.tasks.update_one(
                    {"id": self.pid},
                    {'$set': {
                        'progress': progress

                    }
                    }
                )

            time.sleep(3)

    @classmethod
    @threaded
    def thread_start(cls, method, task_name, project, pid):
        app = cls(method=method, task_name=task_name, project=project, pid=pid)
        # 类http标签进行waf检查
        info = app._waf_check()
        if info == "flag":
            mongo.db.tasks.update_one(
                {"id": pid},
                {'$set': {
                    'progress': "100.00%",
                    'status': 'Finished',
                    'end_time': datetime.datetime.now(),
                    'live_host': 0,

                }
                }
            )

            return True

        app.dir_scan(info)
