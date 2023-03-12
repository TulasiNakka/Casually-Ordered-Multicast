import marshal,multiprocessing,socket,threading,time,itertools,os
from typing import NamedTuple


PORTS = []
for i in range(3):
    PORTS.append(10000 + i)


class Event(NamedTuple):
    sharedObject : int
    pid : int


def vector(id, sharedObject, sock, list):
    while True:
        data = sock.recvfrom(1024)
        msg = marshal.loads(data[0])
        list.append(msg)
        index = []
        for x in list:
            for y in range(3):
                if x["pid"] != id and y != x["pid"] and x["sharedObject"][x["pid"]] != sharedObject[x["pid"]] + 1 and x["sharedObject"][x["pid"]] > sharedObject[x["pid"]]:
                    continue
            index.append(list.index(x))
            print("P{}: Processed event P{}.{} and updated vector clock ->{}".format(id, x["pid"], x["sharedObject"][x["pid"]],x["sharedObject"]))
        for i in index[::-1]:
            list.pop(i)
        for id in range(3):
            sharedObject[id] = max(sharedObject[id], msg["sharedObject"][id])


def pro(id, sharedObject, lock, sock):
    threadSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    threadSock.bind(("localhost", PORTS[id]))
    list = []
    vector1 = threading.Thread(target=vector, args=(id, sharedObject, threadSock, list))
    vector2 = threading.Thread(target=vector, args=( id, sharedObject, threadSock, list))
    vector1.start()
    vector2.start()

    time.sleep(1)
    for _ in range(3):
        time.sleep(0.01)
        with lock:  # lock is handled by context manager to avoid deadlock and,so that no other process can access out shared object when one process is accessing it
            sharedObject[id] += 1
        msg = dict(pid =id, sharedObject=sharedObject)
        data = marshal.dumps(msg)
        for port in PORTS:
            sock.sendto(data, ("localhost", port))
        print(f"P{id}: sending event P{id}.{msg['sharedObject']}")


def createProcess():
    # creating and starting the processes later we are waiting to for process to complete and joining them
    sharedObject = list(itertools.repeat(0,3))
    lock = multiprocessing.Lock()

    p = []
    for i in range(3):
        p.append(multiprocessing.Process(target=pro, args=(i, sharedObject, lock, socket.socket(socket.AF_INET, socket.SOCK_DGRAM))))

    for elements in p:
        elements.start()
        time.sleep(0.01)

    for elements in p:
        elements.join()


if __name__ == "__main__":

    createProcess()