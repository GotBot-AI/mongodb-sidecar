import socket
import sys
import os
import time
from kubernetes import config
from mongo import MongoHandler
from kube import KubeHandler
from members import Members
from watcher import Watcher
from dotenv import load_dotenv
load_dotenv()


def main():
    try:
        # Get pods ip address
        ipaddr = socket.gethostbyname(socket.gethostname())
        print('main: POD IP {}'.format(ipaddr))
        config.load_incluster_config()
        kube = KubeHandler()
        mongo = MongoHandler(kube)
        members = Members(mongo.db)
        mongo.setMembers(members)
        watcher = Watcher(kube, mongo, members, ipaddr)
        watcher.Start()
    except KeyboardInterrupt:
        pass
    except Exception as error:
        print('main: ERROR - {}'.format(error))
    finally:
        print("main: SHUTDOWN")
        sys.exit(0)


if __name__ == '__main__':
    main()
