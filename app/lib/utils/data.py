from app.lib.core.datatype import AttribDict

conf = AttribDict({"THREADS": 10})

if __name__ == '__main__':
    task = {"id": "shadow", "pid": "pifd"}

    conf.finger = AttribDict(task)

    print(conf.finger.id)
