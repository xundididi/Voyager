from app.lib.thirdparty.wafcheck import waf_check
from app import mongo

import queue
from multiprocessing.pool import Pool


def formatnum(str):
    try:
        if str == "" or str == None:
            return 0
        str = str.replace("%", "")
        str = float(str)
        return str
    except:
        return 0




def run_check(check_list, pid):
    queues = queue.Queue()

    pool = Pool(10)  # 创建一个线程池，10个线程数

    for fn in check_list:

        if mongo.db.tasks.find_one({"id": pid}) == None:
            pool.terminate()
            pool.close()
            return False

        print(fn)

        pool.apply_async(waf_check, (fn, queues))

    pool.close()  # 关闭进程池，不再接受新的进程
    pool.join()  # 主进程阻塞等待子进程的退出

    checkd_list = list(queues.queue)

    return checkd_list
