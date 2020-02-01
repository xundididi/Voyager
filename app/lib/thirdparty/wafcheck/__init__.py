from app.lib.thirdparty.wafcheck.actions import Connect


def waf_check(target, que):
    try:
        if "http_address" in target:

            info = Connect.queryPage(target["http_address"])

            if info == "No":
                que.put(target)


        else:
            que.put(target)

        return True
    except:
        return False
