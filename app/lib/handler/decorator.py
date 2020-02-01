import threading
import datetime


# 用来在线程中启动函数的装饰器
def threaded(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


# 用来计算运行时间的装饰器
def time_count(func):
    def wrapper(*args, **kwargs):
        start_time = datetime.datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.datetime.now()
        print(f"消耗时间{end_time - start_time}")

        return result

    return wrapper
