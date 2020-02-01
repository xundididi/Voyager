from app.lib.utils.deps import findDynamicContent
from app.lib.utils.deps import removeDynamicContent
from app.lib.utils.deps import randomInt
from app.lib.utils.deps import randomStr
from app.lib.utils.deps import _comparison
from app.lib.utils.deps import removeReflectiveValues
from app.lib.thirdparty.wafcheck.config import IPS_WAF_CHECK_PAYLOAD
from app.lib.thirdparty.wafcheck.config import HACKER_AGENT
from app.lib.thirdparty.wafcheck.config import USER_AGENT

import requests


class Connect():
    """
    该类是用来检测网站是否是WAF保护的
    """

    @staticmethod
    def getPage(http_address, second=False):

        try:

            if second:
                UA = HACKER_AGENT
            else:
                UA = USER_AGENT

            burp0_url = http_address
            burp0_headers = {
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
                "Accept-Encoding": "gzip, deflate", "Connection": "close", "Upgrade-Insecure-Requests": "1"}
            response = requests.get(burp0_url, headers=burp0_headers, timeout=(3, 5))

            html = response.content.decode("utf-8")

            return html

        except:
            return False

    @staticmethod
    def queryPage(http_address):

        raw_url = f"{http_address}/?id={randomInt(2)}"
        first_page = Connect.getPage(raw_url)

        if first_page:

            payload = f"{randomInt(4)} {IPS_WAF_CHECK_PAYLOAD}"

            value = f"{raw_url}&{randomStr()}={payload}"

            second_page = Connect.getPage(value, second=True)

            if second_page:
                # 删除反射值
                value = removeReflectiveValues(second_page, payload)

                # 在正式对比前先排除一下动态数据的内容
                marks = findDynamicContent(first_page, second_page)
                response1 = removeDynamicContent(first_page, marks)
                response2 = removeDynamicContent(value, marks)

                _ratio = _comparison(response1, response2)
                if _ratio:
                    return "No"
                else:
                    return "Yes"


            else:
                return "Yes"

        else:
            return "Null"
