import uuid
import re
import os

import ipaddress
import xlsxwriter
import hashlib

from app.config import BASE_DIR


def get_uuid():
    return str(uuid.uuid4())


# 分页函数
def get_page(total, p):
    show_page = 5  # 显示的页码数
    pageoffset = 2  # 偏移量
    start = 1  # 分页条开始
    end = total  # 分页条结束

    if total > show_page:
        if p > pageoffset:
            start = p - pageoffset
            if total > p + pageoffset:
                end = p + pageoffset
            else:
                end = total
        else:
            start = 1
            if total > show_page:
                end = show_page
            else:
                end = total
        if p + pageoffset > total:
            start = start - (p + pageoffset - end)
    # 用于模版中循环
    dic = range(start, end + 1)
    return dic


def json_to_excel(mess_list):
    """
    :param mess_list: [{'address': '10.6.20.25', 'mac': '', 'vendor': '', 'hostname': '', 'start_time': '2019-10-24 14:09:39', 'end_time': '2019-10-24 14:10:37', 'ostype': 'OS/2', 'osversion': 'IBM OS/2 Warp 2.0 87%|HP LaserJet 4000 printer 86%|IBM AIX 7.1 86%', 'project': '测试任务一', '@timestamp': '2019-10-24 14:10:38.046172', 'banner': 'Microsoft Windows RPC', 'port': '135', 'service': 'msrpc'}, {'address': '10.6.20.25', 'mac': '', 'vendor': '', 'hostname': '', 'start_time': '2019-10-24 14:09:39', 'end_time': '2019-10-24 14:10:37', 'ostype': 'OS/2', 'osversion': 'IBM OS/2 Warp 2.0 87%|HP LaserJet 4000 printer 86%|IBM AIX 7.1 86%', 'project': '测试任务一', '@timestamp': '2019-10-24 14:10:38.046172', 'banner': 'Microsoft Windows netbios-ssn', 'port': '139', 'service': 'netbios-ssn'}]
    :return:
    """

    uid = str(uuid.uuid4())
    path = f"{BASE_DIR}/app/static/downloads/{uid}.xlsx"

    head_list = list(mess_list[0].keys())

    list3 = []
    for l in mess_list:
        list2 = []
        for m, n in l.items():
            list2.append(n)

        list3.append(list2)

    # #新建excel表
    workbook = xlsxwriter.Workbook(path)

    # 新建sheet（sheet的名称为"sheet1"）
    worksheet = workbook.add_worksheet()

    # 定义表头格式
    title_format = workbook.add_format({
        'bold': True,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#87CEFF'
    })

    worksheet.write_row('A1', head_list, title_format)

    i = 2
    for ECS in list3:
        worksheet.write_row('A' + str(i), ECS)
        i += 1

    workbook.close()

    file_path = path.replace(f"{BASE_DIR}/app", "")

    return file_path, path


# 解析IP地址
def get_ip_list(ip_list):
    """

    :param ip_list: ["192.168.20.1", "192.168.20.1/24"]
    :return:
    """

    ip_list_tmp = []

    if not type(ip_list) is list:
        return False

    for ip in ip_list:

        if "/" in ip:

            try:
                new_list = []

                ip_list_ = [str(ip) for ip in ipaddress.IPv4Network(ip, False)]
                for i in ip_list_:
                    if i[-2:] != ".0":
                        new_list.append(i)

                ip_list_tmp = ip_list_tmp + new_list


            except:
                return False

        elif "," in ip:

            for i in ip.split(","):
                if re.match(
                        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
                        i):
                    ip_list_tmp.append(i)
                else:

                    return False

        elif "-" in ip:
            ip_split = ip.split('-')

            try:
                ip1, ip2, ip3, ip4 = ip_split[0].split(".")
                ip1_1, ip2_2, ip3_3, ip4_4 = ip_split[1].split(".")

                if ip1 != ip1_1 or ip2 != ip2_2 or ip3 != ip3_3:
                    return False

                if int(ip4_4) > 0 and int(ip4_4) < 256:

                    for i in range(int(ip4), int(ip4_4)):
                        ip = "{}.{}.{}.{}".format(ip1, ip2, ip3, i)
                        ip_list_tmp.append(ip)

                else:

                    return False
            except:
                return False

        elif re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
                      ip):
            ip_list_tmp.append(ip)

        # else:
        #
        #     return False

    return len(ip_list_tmp)




# 解析IP地址
def get_list_ip(ip_list):
    """

    :param ip_list: ["192.168.20.1", "192.168.20.1/24"]
    :return:
    """

    ip_list_tmp = []

    if not type(ip_list) is list:
        return False

    for ip in ip_list:

        if "/" in ip:

            try:
                new_list = []

                ip_list_ = [str(ip) for ip in ipaddress.IPv4Network(ip, False)]
                for i in ip_list_:
                    if i[-2:] != ".0":
                        new_list.append(i)

                ip_list_tmp = ip_list_tmp + new_list


            except:
                return False

        elif "," in ip:

            for i in ip.split(","):
                if re.match(
                        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
                        i):
                    ip_list_tmp.append(i)
                else:

                    return False

        elif "-" in ip:
            ip_split = ip.split('-')

            try:
                ip1, ip2, ip3, ip4 = ip_split[0].split(".")
                ip1_1, ip2_2, ip3_3, ip4_4 = ip_split[1].split(".")

                if ip1 != ip1_1 or ip2 != ip2_2 or ip3 != ip3_3:
                    return False

                if int(ip4_4) > 0 and int(ip4_4) < 256:

                    for i in range(int(ip4), int(ip4_4)):
                        ip = "{}.{}.{}.{}".format(ip1, ip2, ip3, i)
                        ip_list_tmp.append(ip)

                else:

                    return False
            except:
                return False

        elif re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
                      ip):
            ip_list_tmp.append(ip)


    return ip_list_tmp


def get_port_list(port_list):
    try:
        ip_list_tmp = []

        if not type(port_list) is list:
            return False

        for port in port_list:

            if "," in port:
                try:
                    for i in port.split(","):
                        if int(i) > 0 and int(i) <= 65535:
                            ip_list_tmp.append(str(i))
                        else:
                            return False

                except Exception as e:
                    print(e)
                    return False

            elif "-" in port:
                begin, end = port.split('-')

                try:

                    if int(begin) > 0 and int(end) < 65536 and int(end) > int(begin):

                        for i in range(int(begin), int(end) + 1):
                            ip_list_tmp.append(str(i))

                    else:

                        return False
                except:
                    return False
            elif int(port) > 0 and int(port) < 65536:
                ip_list_tmp.append(str(port))


            else:
                return False

        return list(set(ip_list_tmp))

    except:
        return False


def list_duplicate(old_list):
    """
    列表去重函数和
    :param old_list: [1,2,3,3,2,1]
    :return:[1,2,3]
    """
    list2 = []

    for i in old_list:
        if i not in list2:
            list2.append(i)

    return list2


def checkFile(filename, raiseOnError=True):
    """
    Checks for file existence and readability
    sqlmap中用来判断文件是否存在以及文件是否可读的函数

    >>> checkFile(__file__)
    True
    """

    valid = True
    try:
        if filename is None or not os.path.isfile(filename):
            valid = False
    except:
        valid = False

    if valid:
        try:
            with open(filename, "rb"):
                pass
        except:
            valid = False

    if not valid and raiseOnError:
        raise False

    return valid


def get_md5(c):
    m = hashlib.md5()
    m.update(c)
    psw = m.hexdigest()
    return psw



# 判断是否为域名
def is_domain(domain):
    domain_regex = re.compile(
        r'(?:[A-Z0-9_](?:[A-Z0-9-_]{0,247}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,}(?<!-))\Z', re.IGNORECASE)
    return True if domain_regex.match(domain) else False


# 判断是否为ip
def is_host(host):
    ip_regex = re.compile(
        r'(^(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])$)',
        re.IGNORECASE)
    return True if ip_regex.match(host) else False

