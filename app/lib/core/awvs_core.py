import requests
import json
import time
import queue
import datetime
import threading
import zipfile

from app.lib.utils.data import conf
from app.lib.utils.tools import get_uuid
from app.lib.handler.decorator import threaded
from app.lib.thirdparty.wafcheck import waf_check

from app.config import AWVS_API_KEY
from app.config import AWVS_HOST_ADDRESS
from app.extensions import mongo
from app.config import BASE_DIR

# 禁用HTTPS报警
requests.packages.urllib3.disable_warnings()

AWVS_HEADER = {"X-Auth": AWVS_API_KEY, "content-type": "application/json"}


class AWVS():

    def add_task(self, target):
        """
        向添加任务的函数
        :param target: http://127.0.0.1
        :return:e723c824-724c-4ae5-b0e0-1679c3d6aacf
        """
        data = {"address": target, "description": target, "criticality": "10"}
        try:
            response = requests.post(AWVS_HOST_ADDRESS + "/api/v1/targets", data=json.dumps(data), headers=AWVS_HEADER,
                                     timeout=30,
                                     verify=False)
            result = json.loads(response.content)

            self.target_id_list.append(result['target_id'])

            return result['target_id']
        except Exception as e:
            print(str(e))
            return

    def start_task(self, url):

        # 开始扫描的任务函数
        '''
        11111111-1111-1111-1111-111111111112    High Risk Vulnerabilities
        11111111-1111-1111-1111-111111111115    Weak Passwords
        11111111-1111-1111-1111-111111111117    Crawl Only
        11111111-1111-1111-1111-111111111116    Cross-site Scripting Vulnerabilities
        11111111-1111-1111-1111-111111111113    SQL Injection Vulnerabilities
        11111111-1111-1111-1111-111111111118    quick_profile_2 0   {"wvs": {"profile": "continuous_quick"}}
        11111111-1111-1111-1111-111111111114    quick_profile_1 0   {"wvs": {"profile": "continuous_full"}}
        11111111-1111-1111-1111-111111111111    Full Scan   1   {"wvs": {"profile": "Default"}}
        '''

        # 获取全部的扫描状态
        data = {
            # "excluded_paths": ["manager", "phpmyadmin", "testphp"],
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
            "custom_headers": ["Accept: */*", "Referer:" + url, "Connection: Keep-alive"],
            # "custom_cookies": [{"url": url,
            #                     "cookie": "UM_distinctid=15da1bb9287f05-022f43184eb5d5-30667808-fa000-15da1bb9288ba9; PHPSESSID=dj9vq5fso96hpbgkdd7ok9gc83"}],
            # "scan_speed": "moderate",  # sequential/slow/moderate/fast more and more fast
            # "technologies": ["PHP"],  # ASP,ASP.NET,PHP,Perl,Java/J2EE,ColdFusion/Jrun,Python,Rails,FrontPage,Node.js
            # # 代理
            # "proxy": {
            #     "enabled": False,
            #     "address": "127.0.0.1",
            #     "protocol": "http",
            #     "port": 8080,
            #     "username": "aaa",
            #     "password": "bbb"
            # },
            # # 无验证码登录
            # "login": {
            #     "kind": "automatic",
            #     "credentials": {
            #         "enabled": False,
            #         "username": "test",
            #         "password": "test"
            #     }
            # },
            # # 401认证
            # "authentication": {
            #     "enabled": False,
            #     "username": "test",
            #     "password": "test"
            # }
        }

        target_id = self.add_task(url)

        requests.patch(AWVS_HOST_ADDRESS + "api/v1/targets/" + str(target_id) + "/configuration",
                       data=json.dumps(data),
                       headers=AWVS_HEADER, timeout=30 * 4, verify=False)

        data = {"target_id": target_id, "profile_id": "11111111-1111-1111-1111-111111111111",
                "schedule": {"disable": False, "start_date": None, "time_sensitive": False}}
        try:
            response = requests.post(AWVS_HOST_ADDRESS + "api/v1/scans", data=json.dumps(data),
                                     headers=AWVS_HEADER, timeout=30,
                                     verify=False)

            result = json.loads(response.content)

            return result['target_id']
        except Exception as e:
            print(str(e))
            return

    def get_scan_id(self, target_id):

        try:
            response = requests.get(f"{AWVS_HOST_ADDRESS}api/v1/targets/{target_id}",
                                    headers=AWVS_HEADER, verify=False)
            results = json.loads(response.content)

            return results["last_scan_id"]

        except Exception as e:
            print(e)

            return False

    def get_download_address(self, download_url):
        """
        根据下载地址获取下载连接
        :param download_url: /api/v1/reports/cdff6a34-eefa-42c7-89ce-6f80c5041436
        :return:
        """

        try:

            while True:
                response = requests.get(f"{AWVS_HOST_ADDRESS}{download_url}",
                                        headers=AWVS_HEADER, verify=False)

                if json.loads(response.content)["status"] != "completed":
                    time.sleep(3)
                else:
                    break

            return json.loads(response.content)["download"][1], json.loads(response.content)["report_id"]

        except Exception as e:
            print(e)
            return

    def get_scan_status(self, scan_id):
        # 获取scan_id的扫描状况
        try:

            response = requests.get(AWVS_HOST_ADDRESS + "api/v1/scans/" + str(scan_id), headers=AWVS_HEADER,
                                    timeout=30, verify=False)
            result = json.loads(response.content)

            status = result['current_session']['status']

            # 如果是completed 表示结束.可以生成报告
            if status == "completed" or status == "failed":

                if result["current_session"]["severity_counts"]["high"] > 0:
                    mongo.db.tasks.update_one(
                        {"id": conf.awvs.pid},
                        {'$set': {
                            'live_host': mongo.db.tasks.find_one({"id": conf.awvs.pid})["live_host"] +
                                         result["current_session"]["severity_counts"]["high"],

                        }
                        }
                    )

                """

                info = {'criticality': 10, 'current_session': {'event_level': 0, 'progress': 0,
                                                               'scan_session_id': 'b5ed8b4b-7551-4258-b411-b43a86db6d11',
                                                               'severity_counts': {'high': 0, 'info': 0, 'low': 0,
                                                                                   'medium': 0},
                                                               'start_date': '2020-01-29T02:54:22.423351+00:00',
                                                               'status': 'completed', 'threat': 0},
                        'manual_intervention': False, 'next_run': None,
                        'profile_id': '11111111-1111-1111-1111-111111111111', 'profile_name': 'Full Scan',
                        'report_template_id': None, 'scan_id': 'd564f6c4-4542-4ce9-8c2f-38768d0d130a',
                        'schedule': {'disable': False, 'history_limit': None, 'recurrence': None, 'start_date': None,
                                     'time_sensitive': False},
                        'target': {'address': 'http://127.0.0.1', 'criticality': 10, 'description': 'http://127.0.0.1',
                                   'type': 'default'}, 'target_id': '08d77f26-312e-4710-a585-767160976acb'}
                """
                self.id_dict_list.append({"scan_id": result["scan_id"], "target_id": result["target_id"]})
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    @staticmethod
    def delete_task(scan_id):
        # 删除scan_id的扫描
        try:
            response = requests.delete(AWVS_HOST_ADDRESS + "/api/v1/scans/" + str(scan_id), headers=AWVS_HEADER,
                                       timeout=30,
                                       verify=False)
            # 如果是204 表示删除成功
            if response.status_code == "204":
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return

    @classmethod
    def delete_target(cls, target_id):
        # 删除scan_id的扫描
        try:
            response = requests.delete(AWVS_HOST_ADDRESS + "api/v1/targets/" + str(target_id), headers=AWVS_HEADER,
                                       timeout=30,
                                       verify=False)
            # 如果是204 表示删除成功
            if response.status_code == "204":
                return True
            else:
                return False
        except Exception as e:
            print(str(e))
            return

    def getreports(self, scan_id):
        # 获取scan_id的扫描报告
        '''
        11111111-1111-1111-1111-111111111111    Developer
        21111111-1111-1111-1111-111111111111    XML
        11111111-1111-1111-1111-111111111119    OWASP Top 10 2013
        11111111-1111-1111-1111-111111111112    Quick
        '''
        data = {"template_id": "11111111-1111-1111-1111-111111111111",
                "source": {"list_type": "scans", "id_list": scan_id}}
        try:
            response = requests.post(AWVS_HOST_ADDRESS + "/api/v1/reports", data=json.dumps(data), headers=AWVS_HEADER,
                                     timeout=30,
                                     verify=False)

            result = response.headers["Location"]

            return result


        except Exception as e:
            print(e)
            return

    @staticmethod
    def get_all_status():
        # 获取全部的扫描状态

        try:
            response = requests.get(AWVS_HOST_ADDRESS + "api/v1/scans", headers=AWVS_HEADER, timeout=30, verify=False)
            results = json.loads(response.content)

            return results
        except Exception as e:
            print(e)
            raise e

    def start(self, url):
        """
        创建并启动任务
        :param url:
        :return:
        """

        target_id = self.start_task(url=url["http_address"])

        time.sleep(3)
        scan_id = self.get_scan_id(target_id=target_id)

        while True:

            if mongo.db.tasks.find_one({"id": conf.awvs.pid}) == None:
                break

            if self.get_scan_status(scan_id):
                break

            time.sleep(3)

    @threaded
    def init(self):

        self.target_queue = queue.Queue()
        self.new_queue = queue.Queue()

        THREADS = 10

        self.target_list = list()

        if conf.awvs.method == "adam":

            ports = mongo.db.ports.find({"parent_name": conf.awvs.child_name})
            domains = mongo.db.subdomains.find({"parent_name": conf.awvs.child_name})

            for i in domains:
                new_dict = dict()
                new_dict["http_address"] = i["http_address"]
                new_dict["parent_name"] = conf.awvs.parent_name
                new_dict["pid"] = i["id"]
                new_dict["flag"] = "domain"
                self.target_queue.put_nowait(new_dict)

            for j in ports:
                if any([j["service"] == "http", j["service"] == "http-proxy", j["service"] == "https"]) \
                        and j["http_address"] != "unknown" and "keydict" in j:
                    new_dict = dict()
                    new_dict["http_address"] = j["http_address"]
                    new_dict["flag"] = "port"
                    new_dict["parent_name"] = conf.awvs.parent_name
                    new_dict["pid"] = j["id"]

                    self.target_queue.put_nowait(new_dict)

            while True:
                new_list = list()

                if self.target_queue.qsize() == 0:
                    break

                if self.target_queue.qsize() > THREADS:
                    for i in range(THREADS):
                        info = self.target_queue.get()
                        t = threading.Thread(target=waf_check, args=(info, self.new_queue))
                        t.start()
                        new_list.append(t)

                else:
                    for i in range(self.target_queue.qsize()):
                        info = self.target_queue.get()
                        t = threading.Thread(target=waf_check, args=(info, self.new_queue))
                        t.start()
                        new_list.append(t)

                # And wait for them to all finish
                alive = True
                while alive:
                    alive = False
                    for thread in new_list:
                        if thread.is_alive():
                            alive = True
                            time.sleep(0.1)

            target_list = list(self.new_queue.queue)

            self.target_id_list = list()
            self.id_dict_list = list()

            for key, i in enumerate(target_list):

                self.start(i)

                mongo.db.tasks.update_one(
                    {"id": conf.awvs.pid},
                    {'$set': {
                        'progress': '{0:.2f}%'.format(((key + 1) / len(target_list)) * 100),

                    }
                    }
                )

                sess = mongo.db.tasks.find_one({"id": conf.awvs.pid})

                if sess == None:

                    if len(self.target_id_list) == 0:
                        break
                    else:
                        for k in self.target_id_list:
                            self.delete_target(k)

                        break

            mongo.db.tasks.update_one(
                {"id": conf.awvs.pid},
                {'$set': {
                    'progress': "100.00%",
                    'status': 'Finished',
                    'end_time': datetime.datetime.now(),
                    "hidden_host": json.dumps(self.target_id_list, ensure_ascii=False)

                }
                }
            )

        if conf.awvs.method == "lilith":

            url_list = mongo.db.tasks.find_one({"id": conf.awvs.pid})["target"]

            for i in json.loads(url_list):
                self.target_queue.put_nowait(i)

            while True:
                new_list = list()

                if self.target_queue.qsize() == 0:
                    break

                if self.target_queue.qsize() > THREADS:
                    for i in range(THREADS):
                        info = self.target_queue.get()
                        t = threading.Thread(target=waf_check, args=(info, self.new_queue))
                        t.start()
                        new_list.append(t)

                else:
                    for i in range(self.target_queue.qsize()):
                        info = self.target_queue.get()
                        t = threading.Thread(target=waf_check, args=(info, self.new_queue))
                        t.start()
                        new_list.append(t)

                # And wait for them to all finish
                alive = True
                while alive:
                    alive = False
                    for thread in new_list:
                        if thread.is_alive():
                            alive = True
                            time.sleep(0.1)

            target_list = list(self.new_queue.queue)

            self.target_id_list = list()
            self.id_dict_list = list()

            for key, i in enumerate(target_list):

                self.start(i)

                mongo.db.tasks.update_one(
                    {"id": conf.awvs.pid},
                    {'$set': {
                        'progress': '{0:.2f}%'.format(((key + 1) / len(target_list)) * 100),

                    }
                    }
                )

                sess = mongo.db.tasks.find_one({"id": conf.awvs.pid})

                if sess == None:

                    if len(self.target_id_list) == 0:
                        break
                    else:
                        for k in self.target_id_list:
                            self.delete_target(k)

                        break

            mongo.db.tasks.update_one(
                {"id": conf.awvs.pid},
                {'$set': {
                    'progress': "100.00%",
                    'status': 'Finished',
                    'end_time': datetime.datetime.now(),
                    "hidden_host": json.dumps(self.id_dict_list, ensure_ascii=False)

                }
                }
            )

    @threaded
    def generate_pdf(self, target_list, uid):
        info = [i["scan_id"] for i in target_list]

        link_download = self.getreports(info)

        pdf_url, report_id = self.get_download_address(link_download)
        pdf_path = f"{BASE_DIR}/app/static/downloads/{get_uuid()}.pdf"

        response = requests.get(f"{AWVS_HOST_ADDRESS}{pdf_url}", stream=True, headers=AWVS_HEADER, verify=False)
        with open(pdf_path, 'wb') as f:
            f.write(response.content)

        mongo.db.exports.update_one(
            {"id": uid},
            {'$set': {
                'status': 'Finished',
                "full_path": pdf_path,
                "file_path": pdf_path.replace(f"{BASE_DIR}/app", "")

            }
            }
        )


if __name__ == '__main__':
    info = "api/v1/reports/bd8c8161-43f8-422e-8314-961a1a79937a"

    response = requests.delete(f"{AWVS_HOST_ADDRESS}{info}",
                               headers=AWVS_HEADER, verify=False)

    print(response.content.decode("utf-8"))
