import ast
import operator
import re
import requests
import queue
import threading
import time
import datetime
import json

from app.lib.handler.decorator import threaded
from app.lib.utils.data import conf

from app.lib.utils.tools import get_md5
from app.extensions import mongo
from app.config import BASE_DIR

BUGSCAN_CMS = ['wordpress', 'weaver_oa', 'joomla', 'qibocms', 'skytech', 'discuz', 'phpcms', 'hanweb',
               'adtsec_gateway', 'pkpmbs', 'piaoyou', 'yongyou_nc', 'seentech_uccenter', 'metinfo',
               'yongyou_zhiyuan_a6', 'yongyou_u8', 'whezeip', 'topsec', 'libsys', 'dedecms', 'zte', 'yongyou_fe',
               'tianbo_train', 'strongsoft', 'ns-asg', 'fangwei', 'tongdaoa', 'ruijie_router', 'huachuang_router',
               'hac_gateway', 'euse_study', 'ecshop', 'umail', 'southsoft', 'siteserver', 'shopex', 'shop7z', 'php168',
               'lianbangsoft', 'jcms', 'gobetter', 'fsmcms', 'anmai', '74cms', 'xplus', 'shopnum1', 'nongyou',
               'kingdee_oa', 'haohan', 'eyou', 'comexe_ras', 'cmseasy', 'zhonghaida_vnet', 'yuanwei_gateway',
               'yongyou_crm', 'xinyang', 'wholeton', 'sgc8000', 'phpwind', 'phpweb', 'lcecgap', 'kj65n_monitor',
               'hsort', 'dswjcms', 'd-link', 'appcms', 'zabbix', 'weaver_e-cology', 'viewgood', 'urp', 'tianrui_lib',
               'thinkphp', 'srun_gateway', 'shopnc', 'shopbuilder', 'ruvar_oa', 'rockoa', 'mallbuilder', 'hongzhi',
               'hishop', 'haitianoa', 'finecms', 'fangweituangou', 'enableq', 'emlog', 'electric_monitor', 'dfe_scada',
               'baiaozhi', 'acsoft', '5clib', '1caitong', 'zoomla', 'zhengfang', 'zblog', 'xycms', 'workyi_system',
               'wisedu_elcs', 'vicworl', 'v5shop', 'thinkox', 'terramaster', 'shuangyang_oa', 'shopxp', 'ruvarhrm',
               'qizhitong_manager', 'qht_study', 'pstar', 'phpyun', 'phpmywind', 'pageadmin', 'nitc', 'newedos',
               'mvmmall', 'mpsec', 'mainone_b2b', 'lezhixing_datacenter', 'kxmail', 'kinggate', 'jinpan', 'jienuohan',
               'jenkins', 'heeroa', 'extmail', 'es-cloud', 'easethink', 'dalianqianhao', 'dahua_dss', 'avcon6', 'zuitu',
               'zfsoft', 'yongyou_icc', 'xinzuobiao', 'weway_soft', 'wecenter', 'weblogic', 'wdcp', 'unis_gateway',
               'trs_wcm', 'trs_lunwen', 'trs_ids', 'totalsoft_lib', 'taodi', 'suyaxing2004', 'supesite', 'startbbs',
               'southidc', 'santang', 'redis', 'phpshe', 'phpmyadmin', 'phpmoadmin', 'panabit', 'netpower', 'ndstar',
               'mongodb', 'mailgard-webmail', 'maccms', 'landray', 'kingdee_eas', 'kesioncms', 'jinqiangui_p2p',
               'jindun_gateway', 'ipowercms', 'insight', 'imaginecms', 'hf_firewall', 'gowinsoft_jw', 'gnuboard',
               'gbcom_wlan', 'ftp', 'foosun', 'feiyuxing_router', 'fckeditor', 'fastmeeting', 'ewebs', 'espcms',
               'esccms', 'esafenet_dlp', 'empire_cms', 'eduplate', 'ecscms', 'drupal', 'dianyips', 'damall', 'cscms',
               'cmstop', 'bocweb', 'bluecms', 'apabi_tasi', 'able_g2s', 'NS-ASG', 'DVRDVS-Webs', '53kf', 'zrar_zw',
               'zhuofansoftsh', 'zhuhaigaoling_huanjingzaosheng', 'zhongruan_firewall', 'zhongqidonglicms',
               'zhongdongli_school', 'zfcgxt', 'zf_cms', 'zentao', 'zdsoft_cnet', 'yxlink', 'yuanwei_wangguan',
               'yonyou_u8', 'yongyou_ehr', 'yongyou_a8', 'yidacms', 'yabb', 'xuezi_ceping', 'xtcms',
               'xr_gatewayplatform', 'xinhaisoft', 'xdcms', 'wygxcms', 'wizbank', 'weixinpl', 'websphere',
               'websiterbaker', 'wdscms', 'visionsoft_velcro', 'vbulletin', 'v2_conference', 'uniportal', 'uniflows',
               'trs_inforadar', 'tp-link', 'topsec_ta-w', 'tipask', 'thinksns', 'telnet', 'tcexam', 'taocms',
               'sztaiji_zw', 'synjones_school', 'syncthru_web_service', 'suntown_pm', 'stcms', 'star-net', 'ssl',
               'speedcms', 'soullon_edu', 'soffice', 'socks5', 'smb', 'smartoa', 'sitefactory', 'sino_agri_sinda',
               'shenlan_jiandu', 'shadows-it', 'seawind', 'seagate_nas', 's8000', 'rsync', 'rpc', 'rockontrol',
               'qiangzhi_jw', 'postgresql', 'plc_router', 'phpwiki', 'phpvibe', 'phpmps', 'phpb2b', 'php_utility_belt',
               'ourphp', 'nsasg', 'niubicms', 'ng-ags', 'newvane_onlineexam', 'netoray_nsg', 'netcore', 'net110',
               'natshell', 'nanjing_shiyou', 'moxa_nport_router', 'mbbcms', 'maticsoftsns', 'maopoa', 'lvmaque',
               'luepacific', 'ltpower', 'looyu_live', 'linksys', 'liangjing', 'lbcms', 'klemanndesign',
               'kingosoft_xsweb', 'kingdee', 'kill_firewall', 'juniper_vpn', 'jumboecms', 'jingci_printer', 'jieqicms',
               'jeecms', 'jdeas', 'jboss', 'iwms', 'iwebshop', 'ikuai', 'igenus', 'idvr', 'iceflow_vpn_router',
               'iGenus', 'humhub', 'huashi_tv', 'huaficms', 'huachang_router', 'house5', 'horde_email',
               'hezhong_shangdao', 'hdwiki', 'gxwssb', 'gooine_sqjz', 'gn_consulting', 'gevercms', 'geditor', 'fscms',
               'feifeicms', 'etmdcp', 'ekucms', 'efuture', 'edutech', 'edusohocms', 'ecweb_shop', 'dubbo',
               'dreamgallery', 'dreamershop', 'douphp', 'dossm', 'dkcms', 'disucz', 'dircms', 'damicms', 'cnoa',
               'cicro', 'chengrui_edu', 'chamilo-lms', 'canon', 'bytevalue_router', 'bohoog', 'boblog', 'b2cgroup',
               'axis2', 'atripower', 'aspcms', 'alkawebs', 'Tour', 'B2Bbuilder', 'ATEN', '7stars', '686_weixin',
               '3gmeeting', '360shop', '1039_jxt', '08cms']


def _count(filename):
    try:
        file_path = f"{BASE_DIR}/app/lib/thirdparty/cmsfinger/{filename}"

        with open(file_path, "r") as f:
            conetnt = f.read()

            finger_list = ast.literal_eval(conetnt)

            sorted_x = sorted(finger_list, key=operator.itemgetter('hits'), reverse=True)

            return sorted_x

    except:
        return False

    finally:
        f.close()


def _check_rule(key, header, body, title):
    """指纹识别"""

    if 'title="' in key:
        if re.findall(r'title=\"(.*)\"', key)[0].lower() in title.lower():
            return True

    elif 'body=\"' in key:

        if re.findall(r'body=\"(.*)\"', key)[0].lower() in body.lower():
            return True

    elif "header=\"" in key:

        if re.findall(r'header=\"?(.*)\"?', key)[0].lower() in header.lower():
            return True


class FingerCMS():

    def __init__(self):
        self.fofa_finger = _count("fofa_finger.json")
        self.bugscan_finger = _count("cms_finger.json")
        self.target_queue = queue.Queue()
        self.error_queue = queue.Queue()

    def _check(self, _id):
        for i in self.fofa_finger:

            if i["id"] == _id["id"]:
                return i["name"], i["keys"]

    def bugscan_scanner(self, target, flag, pid):

        for i in self.bugscan_finger:

            finger_id = i["id"]
            finger_keyword = i["keyword"]
            finger_url = i["url"]
            finger_content = i["content"]
            finger_option = i["option"]

            # 连接失败超过20次自动结束
            count_pid = list(self.error_queue.queue).count(pid)

            if count_pid > 0:
                return True

            response_content, content_html, _ = self.get_info(target=target, que=self.error_queue, url=finger_url, pid=pid)

            if response_content:

                if finger_option == "md5":

                    if finger_content == get_md5(content_html):

                        # 执行完之后，相应的hits的要加1
                        for k in self.bugscan_finger:

                            if k["id"] == finger_id:
                                k["hits"] = k["hits"] + 1

                        if flag == "port":

                            mongo.db.ports.update_one(
                                {"id": pid},
                                {'$set': {
                                    'category': finger_keyword.lower()

                                }
                                }
                            )

                        elif flag == "domain":
                            mongo.db.subdomains.update_one(
                                {"id": pid},
                                {'$set': {
                                    'category': finger_keyword.lower()

                                }
                                }
                            )

                        return True

                elif finger_option == "keyword":

                    if finger_content.lower() in str(response_content).lower():

                        # 执行完之后，相应的hits的要加1
                        for k in self.bugscan_finger:

                            if k["id"] == finger_id:
                                k["hits"] = k["hits"] + 1

                        if flag == "port":

                            mongo.db.ports.update_one(
                                {"id": pid},
                                {'$set': {
                                    'category': finger_keyword.lower()

                                }
                                }
                            )

                        elif flag == "domain":
                            mongo.db.subdomains.update_one(
                                {"id": pid},
                                {'$set': {
                                    'category': finger_keyword.lower()

                                }
                                }
                            )

                        return True

                elif finger_option == "regx":
                    r = re.search(finger_content, response_content)
                    if r:

                        # 执行完之后，相应的hits的要加1
                        for k in self.bugscan_finger:

                            if k["id"] == finger_id:
                                k["hits"] = k["hits"] + 1

                        if flag == "port":

                            mongo.db.ports.update_one(
                                {"id": pid},
                                {'$set': {
                                    'category': finger_keyword.lower()

                                }
                                }
                            )

                        elif flag == "domain":
                            mongo.db.subdomains.update_one(
                                {"id": pid},
                                {'$set': {
                                    'category': finger_keyword.lower()

                                }
                                }
                            )
                        return True

    def get_info(self, target, que, pid, url="demo"):
        """获取web的信息"""
        try:

            if url == "demo":

                burp0_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:71.0) Gecko/20100101 Firefox/71.0",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
                    "Accept-Encoding": "gzip, deflate", "Connection": "close", "Upgrade-Insecure-Requests": "1"}

                response = requests.get(target, headers=burp0_headers, timeout=(7, 7))

                response.encoding = response.apparent_encoding

                html = response.text

                match_title = re.findall(r'<title.*?>(.*?)</title>', html)

                if len(match_title) == 0:
                    return str(response.headers), html.lower(), ""

                return str(response.headers), html.lower(), match_title[0]

            else:
                http_target = target + url

                burp0_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:71.0) Gecko/20100101 Firefox/71.0",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
                    "Accept-Encoding": "gzip, deflate", "Connection": "close", "Upgrade-Insecure-Requests": "1"}

                response = requests.get(http_target, headers=burp0_headers, timeout=(7, 7))

                response.encoding = response.apparent_encoding

                html = response.text

                return html, response.content, ""

        except:
            que.put_nowait(pid)
            return "", "", ""

    def handle(self, _id, header, body, title, pid, flag):

        name, key = self._check(_id)

        if '||' in key and '&&' not in key and not re.match(r".*\(.*?\|\|.*?\).*", key) and not re.match(
                r".*\(.*?&&.*?\).*", key):
            """
            header="Set-Cookie: phpMyAdmin=" || title="phpMyAdmin " || body="pma_password"
            """

            for echo_finger in key.split("||"):
                if _check_rule(echo_finger, header=header, body=body, title=title):
                    if flag == "port":
                        content = mongo.db.ports.find_one({"id": pid})["fofa"]

                        if len(content) == 0:
                            content = content
                        else:
                            content = content + ","
                        bug = mongo.db.ports.find_one({"id": pid})["category"]

                        if name.lower() in BUGSCAN_CMS and len(bug) == 0:

                            mongo.db.ports.update_one(
                                {"id": pid},
                                {'$set': {
                                    'fofa': content + name.lower(),
                                    'category': name.lower()

                                }
                                }
                            )
                        else:
                            mongo.db.ports.update_one(
                                {"id": pid},
                                {'$set': {
                                    'fofa': content + name.lower()

                                }
                                }
                            )

                    elif flag == "domain":
                        content = mongo.db.subdomains.find_one({"id": pid})["fofa"]

                        if len(content) == 0:
                            content = content
                        else:
                            content = content + ","
                        bug = mongo.db.subdomains.find_one({"id": pid})["category"]

                        if name.lower() in BUGSCAN_CMS and len(bug) == 0:

                            mongo.db.subdomains.update_one(
                                {"id": pid},
                                {'$set': {
                                    'fofa': content + name.lower(),
                                    'category': name.lower()

                                }
                                }
                            )
                        else:
                            mongo.db.subdomains.update_one(
                                {"id": pid},
                                {'$set': {
                                    'fofa': content + name.lower()

                                }
                                }
                            )
                    break



        elif '||' not in key and '&&' not in key and not re.match(r".*\(.*?\|\|.*?\).*", key) and not re.match(
                r".*\(.*?&&.*?\).*", key):

            if _check_rule(key, header=header, body=body, title=title):
                if flag == "port":
                    content = mongo.db.ports.find_one({"id": pid})["fofa"]

                    if len(content) == 0:
                        content = content
                    else:
                        content = content + ","
                    bug = mongo.db.ports.find_one({"id": pid})["category"]

                    if name.lower() in BUGSCAN_CMS and len(bug) == 0:

                        mongo.db.ports.update_one(
                            {"id": pid},
                            {'$set': {
                                'fofa': content + name.lower(),
                                'category': name.lower()

                            }
                            }
                        )
                    else:
                        mongo.db.ports.update_one(
                            {"id": pid},
                            {'$set': {
                                'fofa': content + name.lower()

                            }
                            }
                        )

                elif flag == "domain":
                    content = mongo.db.subdomains.find_one({"id": pid})["fofa"]

                    if len(content) == 0:
                        content = content
                    else:
                        content = content + ","
                    bug = mongo.db.subdomains.find_one({"id": pid})["category"]

                    if name.lower() in BUGSCAN_CMS and len(bug) == 0:

                        mongo.db.subdomains.update_one(
                            {"id": pid},
                            {'$set': {
                                'fofa': content + name.lower(),
                                'category': name.lower()

                            }
                            }
                        )
                    else:
                        mongo.db.subdomains.update_one(
                            {"id": pid},
                            {'$set': {
                                'fofa': content + name.lower()

                            }
                            }
                        )



        elif '&&' in key and '||' not in key and not re.match(r".*\(.*?\|\|.*?\).*", key) and not re.match(
                r".*\(.*?&&.*?\).*", key):
            """
            body="http://www.yuysoft.com/" && body="技术支持"
            """
            num = 0
            for rule in key.split('&&'):
                if _check_rule(rule, header, body, title):
                    num += 1
            if num == len(key.split('&&')):
                if flag == "port":
                    content = mongo.db.ports.find_one({"id": pid})["fofa"]

                    if len(content) == 0:
                        content = content
                    else:
                        content = content + ","
                    bug = mongo.db.ports.find_one({"id": pid})["category"]

                    if name.lower() in BUGSCAN_CMS and len(bug) == 0:

                        mongo.db.ports.update_one(
                            {"id": pid},
                            {'$set': {
                                'fofa': content + name.lower(),
                                'category': name.lower()

                            }
                            }
                        )
                    else:
                        mongo.db.ports.update_one(
                            {"id": pid},
                            {'$set': {
                                'fofa': content + name.lower()

                            }
                            }
                        )

                elif flag == "domain":
                    content = mongo.db.subdomains.find_one({"id": pid})["fofa"]

                    if len(content) == 0:
                        content = content
                    else:
                        content = content + ","
                    bug = mongo.db.subdomains.find_one({"id": pid})["category"]

                    if name.lower() in BUGSCAN_CMS and len(bug) == 0:

                        mongo.db.subdomains.update_one(
                            {"id": pid},
                            {'$set': {
                                'fofa': content + name.lower(),
                                'category': name.lower()

                            }
                            }
                        )
                    else:
                        mongo.db.subdomains.update_one(
                            {"id": pid},
                            {'$set': {
                                'fofa': content + name.lower()

                            }
                            }
                        )

        elif '||' in key and re.match(r".*\(.*?&&.*?\).*", key):

            and_match = re.findall(r'\((.*)\)', key)[0]

            for rule in key.split('||'):

                if '&&' in rule:
                    num = 0
                    for _rule in and_match.split("&&"):
                        if _check_rule(_rule, header, body, title):
                            num += 1
                    if num == len(rule.split('&&')):
                        if flag == "port":
                            content = mongo.db.ports.find_one({"id": pid})["fofa"]

                            if len(content) == 0:
                                content = content
                            else:
                                content = content + ","
                            bug = mongo.db.ports.find_one({"id": pid})["category"]

                            if name.lower() in BUGSCAN_CMS and len(bug) == 0:

                                mongo.db.ports.update_one(
                                    {"id": pid},
                                    {'$set': {
                                        'fofa': content + name.lower(),
                                        'category': name.lower()

                                    }
                                    }
                                )
                            else:
                                mongo.db.ports.update_one(
                                    {"id": pid},
                                    {'$set': {
                                        'fofa': content + name.lower()

                                    }
                                    }
                                )

                        elif flag == "domain":
                            content = mongo.db.subdomains.find_one({"id": pid})["fofa"]

                            if len(content) == 0:
                                content = content
                            else:
                                content = content + ","
                            bug = mongo.db.subdomains.find_one({"id": pid})["category"]

                            if name.lower() in BUGSCAN_CMS and len(bug) == 0:

                                mongo.db.subdomains.update_one(
                                    {"id": pid},
                                    {'$set': {
                                        'fofa': content + name.lower(),
                                        'category': name.lower()

                                    }
                                    }
                                )
                            else:
                                mongo.db.subdomains.update_one(
                                    {"id": pid},
                                    {'$set': {
                                        'fofa': content + name.lower()

                                    }
                                    }
                                )

                        break
                else:
                    if _check_rule(rule, header, body, title):
                        if flag == "port":
                            content = mongo.db.ports.find_one({"id": pid})["fofa"]

                            if len(content) == 0:
                                content = content
                            else:
                                content = content + ","
                            bug = mongo.db.ports.find_one({"id": pid})["category"]

                            if name.lower() in BUGSCAN_CMS and len(bug) == 0:

                                mongo.db.ports.update_one(
                                    {"id": pid},
                                    {'$set': {
                                        'fofa': content + name.lower(),
                                        'category': name.lower()

                                    }
                                    }
                                )
                            else:
                                mongo.db.ports.update_one(
                                    {"id": pid},
                                    {'$set': {
                                        'fofa': content + name.lower()

                                    }
                                    }
                                )

                        elif flag == "domain":
                            content = mongo.db.subdomains.find_one({"id": pid})["fofa"]

                            if len(content) == 0:
                                content = content
                            else:
                                content = content + ","
                            bug = mongo.db.subdomains.find_one({"id": pid})["category"]

                            if name.lower() in BUGSCAN_CMS and len(bug) == 0:

                                mongo.db.subdomains.update_one(
                                    {"id": pid},
                                    {'$set': {
                                        'fofa': content + name.lower(),
                                        'category': name.lower()

                                    }
                                    }
                                )
                            else:
                                mongo.db.subdomains.update_one(
                                    {"id": pid},
                                    {'$set': {
                                        'fofa': content + name.lower()

                                    }
                                    }
                                )

                        break

        elif "&&" in key and re.match(r".*\(.*?\|\|.*?\).*", key):
            """
            title="InvoicePlane" && (header="ip_session" || header="ci_session")
            """

            and_match = re.findall(r'\((.*)\)', key)[0]
            for rule in key.split('&&'):
                num = 0
                if '||' in rule:
                    for _rule in and_match.split('||'):
                        if _check_rule(_rule, title, body, header):
                            num += 1
                            break
                else:
                    if _check_rule(rule, title, body, header):
                        num += 1
                if num == len(key.split('&&')):
                    if flag == "port":
                        content = mongo.db.ports.find_one({"id": pid})["fofa"]

                        if len(content) == 0:
                            content = content
                        else:
                            content = content + ","
                        bug = mongo.db.ports.find_one({"id": pid})["category"]

                        if name.lower() in BUGSCAN_CMS and len(bug) == 0:

                            mongo.db.ports.update_one(
                                {"id": pid},
                                {'$set': {
                                    'fofa': content + name.lower(),
                                    'category': name.lower()

                                }
                                }
                            )
                        else:
                            mongo.db.ports.update_one(
                                {"id": pid},
                                {'$set': {
                                    'fofa': content + name.lower()

                                }
                                }
                            )

                    elif flag == "domain":
                        content = mongo.db.subdomains.find_one({"id": pid})["fofa"]

                        if len(content) == 0:
                            content = content
                        else:
                            content = content + ","
                        bug = mongo.db.subdomains.find_one({"id": pid})["category"]

                        if name.lower() in BUGSCAN_CMS and len(bug) == 0:

                            mongo.db.subdomains.update_one(
                                {"id": pid},
                                {'$set': {
                                    'fofa': content + name.lower(),
                                    'category': name.lower()

                                }
                                }
                            )
                        else:
                            mongo.db.subdomains.update_one(
                                {"id": pid},
                                {'$set': {
                                    'fofa': content + name.lower()

                                }
                                }
                            )

    def run(self, target, pid, flag):

        headers, body, title = self.get_info(target, self.error_queue, pid=pid)
        for _id in self.fofa_finger:
            self.handle(_id, header=headers, body=body, title=title, pid=pid, flag=flag)

        # if flag == "port":
        #     content = mongo.db.ports.find_one({"id": pid})["category"]
        #
        #     if len(content) == 0:
        #         print(target)
        #         self.bugscan_scanner(target, flag, pid)
        #
        # if flag == "domain":
        #     content = mongo.db.subdomains.find_one({"id": pid})["category"]
        #
        #     if len(content) == 0:
        #         self.bugscan_scanner(target, flag, pid)

    def thread_controller(self):
        THREADS = 10

        if conf.finger.method == "adam":

            ports = mongo.db.ports.find({"parent_name": conf.finger.child_name})
            domains = mongo.db.subdomains.find({"parent_name": conf.finger.child_name})

            for i in domains:
                new_dict = dict()
                new_dict["http_address"] = i["http_address"]
                new_dict["parent_name"] = conf.finger.parent_name
                new_dict["pid"] = i["id"]
                new_dict["flag"] = "domain"
                self.target_queue.put_nowait(new_dict)

            for j in ports:
                if any([j["service"] == "http", j["service"] == "http-proxy", j["service"] == "https"]) \
                        and j["http_address"] != "unknown" and "keydict" in j:
                    new_dict = dict()
                    new_dict["http_address"] = j["http_address"]
                    new_dict["flag"] = "port"
                    new_dict["parent_name"] = conf.finger.parent_name
                    new_dict["pid"] = j["id"]

                    self.target_queue.put_nowait(new_dict)

            conf.finger.target = list(self.target_queue.queue)

            while True:
                new_list = list()

                if self.target_queue.qsize() == 0:
                    break

                if self.target_queue.qsize() > THREADS:
                    for i in range(THREADS):
                        info = self.target_queue.get()
                        t = threading.Thread(target=self.run, args=(info["http_address"], info["pid"], info["flag"]))
                        t.start()
                        new_list.append(t)

                else:
                    for i in range(self.target_queue.qsize()):
                        info = self.target_queue.get()
                        t = threading.Thread(target=self.run, args=(info["http_address"], info["pid"], info["flag"]))
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

                total_num = len(conf.finger.target)
                now_pro = len(conf.finger.target) - self.target_queue.qsize()

                progress = '{0:.2f}%'.format((now_pro / total_num) * 100)

                mongo.db.tasks.update_one(
                    {"id": conf.finger.pid},
                    {'$set': {
                        'progress': progress,

                    }
                    }
                )

            if isinstance(self.bugscan_finger, list):
                json_str = json.dumps(self.bugscan_finger, ensure_ascii=False)

                file_path = f"{BASE_DIR}/app/lib/thirdparty/cmsfinger/cms_finger.json"
                with open(file_path, 'w') as json_file:
                    json_file.write(json_str)

            live_num = 0
            for i in mongo.db.ports.find({'pid': conf.finger.pid}):
                if len(i["category"]) > 0:
                    live_num = live_num + 1

            mongo.db.tasks.update_one(
                {"id": conf.finger.pid},
                {'$set': {
                    'progress': "100.00%",
                    'status': 'Finished',
                    'end_time': datetime.datetime.now(),
                    'live_host': live_num,

                }
                }
            )

        if conf.finger.method == "lilith":

            url_list = mongo.db.tasks.find_one({"id": conf.finger.pid})["target"]

            for i in ast.literal_eval(url_list):
                self.target_queue.put_nowait(i)

            while True:
                new_list = list()

                if self.target_queue.qsize() == 0:
                    break

                if self.target_queue.qsize() > THREADS:
                    for i in range(THREADS):
                        info = self.target_queue.get()
                        t = threading.Thread(target=self.run, args=(info["http_address"], info["pid"], info["flag"]))
                        t.start()
                        new_list.append(t)

                else:
                    for i in range(self.target_queue.qsize()):
                        info = self.target_queue.get()
                        t = threading.Thread(target=self.run, args=(info["http_address"], info["pid"], info["flag"]))
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

                total_num = len(conf.finger.target)
                now_pro = len(conf.finger.target) - self.target_queue.qsize()

                progress = '{0:.2f}%'.format((now_pro / total_num) * 100)

                mongo.db.tasks.update_one(
                    {"id": conf.finger.pid},
                    {'$set': {
                        'progress': progress,

                    }
                    }
                )

            live_num = 0
            for i in mongo.db.ports.find({'pid': conf.finger.pid}):
                if len(i["category"]) > 0:
                    live_num = live_num + 1

            mongo.db.tasks.update_one(
                {"id": conf.finger.pid},
                {'$set': {
                    'progress': "100.00%",
                    'status': 'Finished',
                    'end_time': datetime.datetime.now(),
                    'total_host': live_num,

                }
                }
            )

            if isinstance(self.bugscan_finger, list):
                json_str = json.dumps(self.bugscan_finger, ensure_ascii=False)

                file_path = f"{BASE_DIR}/app/lib/thirdparty/cmsfinger/cms_finger.json"
                with open(file_path, 'w') as json_file:
                    json_file.write(json_str)

    @classmethod
    @threaded
    def thread_start(cls):
        app = FingerCMS()
        app.thread_controller()


def unin_test_md5(target):
    http_target = target

    burp0_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:71.0) Gecko/20100101 Firefox/71.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Accept-Encoding": "gzip, deflate", "Connection": "close", "Upgrade-Insecure-Requests": "1"}

    response = requests.get(http_target, headers=burp0_headers, timeout=(7, 7))

    print(response.status_code)

    return get_md5(response.content)


if __name__ == '__main__':
    print(unin_test_md5("http://127.0.0.1/themes/pmahomme/img/logo_rk"))
