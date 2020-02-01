from app import mongo
from app.config import DOCKER_CLIENT
from app.lib.utils.tools import get_uuid
from app.lib.core import formatnum
from app.lib.handler.decorator import threaded
from app.lib.thirdparty.wafcheck import waf_check

import time
import queue
import datetime
import threading

THREADS = 10


class ControllerPocs():
    # 控制并发线程数
    threads_queue = queue.Queue(maxsize=THREADS)
    for i in range(THREADS):
        threads_queue.put_nowait(" ")

    # 存放目标线程数
    target_queue = queue.Queue()

    list_queue = queue.Queue()

    def __init__(self, task_name, project, pid):

        self.task_name = task_name
        self.project = project
        self.pid = pid

    # waf检查函数
    def _waf_check(self):

        ports = mongo.db.ports.find({"parent_name": self.task_name})
        domains = mongo.db.subdomains.find({"parent_name": self.task_name})

        print(ports.count(), domains.count())

        for j in ports:
            self.target_queue.put_nowait(j)

        for k in domains:
            self.target_queue.put_nowait(k)

        while True:

            target_list = list()

            if self.target_queue.qsize() == 0:
                break

            if self.target_queue.qsize() >= THREADS:

                # 使用攻击对象attactObject的线程数来控制是否要启动新的线程
                for index in range(0, THREADS):
                    self.threads_queue.get()
                    param = self.target_queue.get()
                    attacker = threading.Thread(target=waf_check, args=(param, self.list_queue))
                    attacker.start()
                    target_list.append(attacker)


            else:
                for index in range(0, self.target_queue.qsize()):
                    self.threads_queue.get()
                    param = self.target_queue.get()
                    attacker = threading.Thread(target=waf_check, args=(param, self.list_queue))
                    attacker.start()
                    target_list.append(attacker)

            for t in target_list:
                t.join(3)

                self.threads_queue.put(" ")

        return list(self.list_queue.queue)

    # cms指纹识别函数
    def _cms_finger(self, target_list):
        return target_list

    def create_attack_task(self, target_list):
        """
        该函数用来进行POC扫描
        :param target_list:
        :return:
        """

        attack_list_xunfeng = []
        attack_list_s1riu5 = []
        attack_list_kunpeng = []
        attack_list_bugscan = []

        pocs = mongo.db.pocs.find({})

        pocs_list = list()

        for i in pocs:
            pocs_list.append(i)

        for m in pocs_list:
            for n in target_list:

                if m["flag"] == "xunfeng":

                    if n["service"] == m["vul_service"]:
                        new_dict = {}
                        new_dict["ip"] = n["address"]
                        new_dict["port"] = n["port"]
                        new_dict["poc"] = m["poc_name"]
                        new_dict["keyword"] = m["vul_service"]
                        new_dict["type_file"] = m["file_type"]
                        new_dict["project_name"] = self.project
                        attack_list_xunfeng.append(new_dict)

                    if "tag" in n:
                        if n["tag"] == m["vul_service"]:
                            new_dict = {}
                            new_dict["ip"] = n["address"]
                            new_dict["port"] = n["port"]
                            new_dict["poc"] = m["poc_name"]
                            new_dict["keyword"] = m["vul_service"]
                            new_dict["type_file"] = m["file_type"]
                            new_dict["project_name"] = self.project
                            attack_list_xunfeng.append(new_dict)

                elif m["flag"] == "kunpeng":

                    if "subdomain_name" in n:
                        attack_dict = {'type': 'web', 'target': "web", 'netloc': n["http_address"],
                                       "parent_name": self.project}
                        if attack_dict not in attack_list_kunpeng:
                            attack_list_kunpeng.append(attack_dict)
                    else:

                        if n["service"] in ["http", "ssl", "https"]:
                            if 'http' in n["service"]:
                                scheme = 'http'
                                if n["service"] in ['https', 'ssl'] or n["port"] == 443:
                                    scheme = 'https'
                                ip_url = '{}://{}:{}'.format(scheme, n["address"], n["port"])
                                attack_dict = {'type': 'web', 'target': "web", 'netloc': ip_url,
                                               "parent_name": self.project}
                                if attack_dict not in attack_list_kunpeng:
                                    attack_list_kunpeng.append(attack_dict)

                        else:

                            attack_dict = {'type': 'service', 'target': n["service"],
                                           'netloc': n["address"] + ':' + str(n["port"]), "parent_name": self.project}

                            if attack_dict not in attack_list_kunpeng:
                                attack_list_kunpeng.append(attack_dict)
                        #
                        # if n["service"] in ["http", "ssl", "https"]:
                        #     attack_dict = {'type': 'web', 'target': "web", 'netloc': n["http_address"],
                        #                    "parent_name": self.project}
                        #     if attack_dict not in attack_list_kunpeng:
                        #         attack_list_kunpeng.append(attack_dict)
                        #
                        # else:
                        #
                        #     attack_dict = {'type': 'service', 'target': n["service"],
                        #                    'netloc': n["http_address"], "parent_name": self.project}
                        #
                        #     if attack_dict not in attack_list_kunpeng:
                        #         attack_list_kunpeng.append(attack_dict)

                elif m["flag"] == "bugscan":

                    """
                    m: {'_id': ObjectId('5e2858f3a5c1fe4f0152e6c3'), 'cretae_date': datetime.datetime(2020, 1, 22, 22, 15, 15, 693000), 'vul_type': 'Null', 'file_type': 'py', 'vul_service': 'php168', 'flag': 'bugscan', 'id': '2acda09e-0964-4c52-b06f-c4188f5eeaf5', 'vul_name': 'Null', 'vul_info': 'Null', 'poc_name': 'exp_1170.py', 'vul_level': 'Null'}
                    n: {'_id': ObjectId('5e28ef328cd7cf0e4b791990'), 'id': '12adf194-e1ef-46ee-b552-645733f31e16', 'address': '127.0.0.1', 'mac': 'Null', 'vendor': 'Null', 'port': 8080, 'hostname': 'Null', 'create_date': datetime.datetime(2020, 1, 23, 8, 56, 18, 322000), 'end_time': datetime.datetime(2020, 1, 23, 8, 56, 18, 322000), 'parent_name': ' 测试项目', 'pid': '15ddb1f9-7792-4471-a084-2e6bfd3cc821', 'http_address': 'http://127.0.0.1', 'fofa': 'phpmyadmin,jquery,jquery-ui', 'category': 'phpmyadmin', 'service': 'http'}

                    """

                    if m["vul_service"] in n["service"]:

                        attack_dict = {'netloc': n["http_address"], "poc": m["poc_name"], "keyword": n["service"],
                                       "parent_name": self.project}
                        if attack_dict not in attack_list_bugscan:
                            attack_list_bugscan.append(attack_dict)

                    if m["vul_service"] in n["category"]:

                        attack_dict = {'netloc': n["http_address"], "poc": m["poc_name"], "keyword": n["category"],
                                       "parent_name": self.project}
                        if attack_dict not in attack_list_bugscan:
                            attack_list_bugscan.append(attack_dict)

        poc_num = attack_list_xunfeng + attack_list_kunpeng


        sess = mongo.db.tasks.find_one({"id": self.pid})

        # 项目被删除的时候
        if sess == None:
            return True

        if len(poc_num) == 0:
            mongo.db.tasks.update_one(
                {"id": self.pid},
                {'$set': {
                    'progress': "100.00%",
                    'status': 'Finished',
                    'end_time': datetime.datetime.now(),
                    'total_host': 0,

                }
                }
            )

            return True

        target_dict = {}
        target_dict["xunfeng"] = attack_list_xunfeng
        target_dict["kunpeng"] = attack_list_kunpeng
        # target_dict["bugscan"] = attack_list_bugscan

        for i in target_dict.items():

            if len(i[1]) != 0:
                vul_id = get_uuid()
                vul = {"id": vul_id, "parent_name": self.project, "progress": "0.00%", "total_num": len(i[1]),
                       "create_date": datetime.datetime.now(), "end_time": "Null",
                       "status": "Running",
                       "target": str(i[1]), "flag": i[0], "pid": self.pid}

                mongo.db.vuldocker.insert_one(vul)

                contain = DOCKER_CLIENT.containers.run(f"ap0llo/poc:{i[0]}", ["attack", vul_id], detach=True,
                                                       network="host", auto_remove=True)

                mongo.db.vuldocker.update_one(
                    {"id": self.pid},
                    {'$set': {
                        "contain_id": contain.id
                    }
                    }
                )

        while True:
            count = mongo.db.vuldocker.find({"pid": self.pid}).count()

            now_progress = 0

            for i in mongo.db.vuldocker.find({"pid": self.pid}):
                progress_ = formatnum(i["progress"])
                now_progress = now_progress + progress_

            progress = now_progress / count

            progress = '%.2f' % (progress)
            percent = f"{progress}%"

            if percent == "100.00%":

                mongo.db.tasks.update_one(
                    {"id": self.pid},
                    {'$set': {
                        'progress': "100.00%",
                        'status': 'Finished',
                        'end_time': datetime.datetime.now(),
                        'total_host': mongo.db.vuls.find({'pid': self.pid}).count(),

                    }
                    }
                )

                return True
            else:
                mongo.db.tasks.update_one(
                    {"id": self.pid},
                    {'$set': {
                        'progress': percent,
                        "total_host": mongo.db.vuls.find({'pid': self.pid}).count(),

                    }
                    }
                )

            time.sleep(3)

    @classmethod
    @threaded
    def thread_start(cls, task_name, project, pid):
        app = cls(task_name=task_name, project=project, pid=pid)
        # 类http标签进行waf检查
        info = app._waf_check()

        # 类http标签进行cms识别
        last_tag = app._cms_finger(info)

        # 正式开始运行
        app.create_attack_task(last_tag)

    @classmethod
    def start(cls, task_name, project, pid):
        app = cls(task_name, project=project, pid=pid)
        # 类http标签进行waf检查
        info = app._waf_check()

        # 类http标签进行cms识别
        last_tag = app._cms_finger(info)

        # 正式开始运行
        app.create_attack_task(last_tag)
