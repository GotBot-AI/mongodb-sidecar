import os
import socket
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure


class Member:

    def __init__(self, _id, IP, priority):
        self._id = _id
        self.IP = IP
        self.port = int(os.getenv('MONGO_PORT'))
        self.priority = priority
        self.primary = False
        self.sideCarIP = socket.gethostbyname(socket.gethostname())
        self.username = os.getenv('MONGO_USERNAME')
        self.password = os.getenv('MONGO_PASSWORD')

    def CheckIfAlive(self):
        try:
            db = MongoClient(
                self.IP,
                self.port,
                serverSelectionTimeoutMS=100,
                username=self.username,
                password=self.password
            )
            ping = db.admin.command('ping')
            print('Member.CheckIfAlive.ping: {}'.format(ping['ok']))
            if ping['ok'] == 1.0:
                return True
            else:
                return False
        except ServerSelectionTimeoutError as error:
            print('Member.CheckIfAlive: ServerSelectionTimeoutError - {}'.format(error))
            db.close()
            return True
        except Exception as error:
            print('Member.CheckIfAlive: ERROR - {}'.format(error))
            db = None
            return False

    def CheckIfPrimary(self):
        try:
            db = MongoClient(
                self.IP,
                self.port,
                replicaset=os.getenv('REPLICA_SET_NAME'),
                serverSelectionTimeoutMS=100,
                username=self.username,
                password=self.password
            )
            primary = db.admin.command('ismaster')['primary']
            print('Member.CheckIfPrimary.is_primary: {}'.format(primary))
            if self.sideCarIP in primary:
                print('Member.CheckIfPrimary: POD IS PRIMARY')
                return primary
            elif self.IP in primary:
                db.close()
                self.primary = True
                print('Member.CheckIfPrimary: POD {} IS PRIMARY'.format(self.IP))
                return True
            else:
                db.close()
                self.primary = False
                return False
        except ServerSelectionTimeoutError as error:
            print('Member.CheckIfPrimary: ServerSelectionTimeoutError - {}'.format(error))
            db.close()
            return False
        except Exception as error:
            print('Member.CheckIfPrimary: ERROR - {}'.format(error))
            db = None
            return False

    def CheckIfPodIsPrimary(self):
        try:
            db = MongoClient(
                self.IP,
                self.port,
                replicaset=os.getenv('REPLICA_SET_NAME'),
                serverSelectionTimeoutMS=100,
                username=self.username,
                password=self.password
            )
            primary = db.admin.command('ismaster')['primary']
            print('Member.CheckIfPrimary.is_primary: {}'.format(primary))
            if self.sideCarIP in primary:
                db.close()
                self.primary = True
                return True
            else:
                db.close()
                self.primary = False
                return False
        except ServerSelectionTimeoutError as error:
            print('Member.CheckIfPrimary: ServerSelectionTimeoutError - {}'.format(error))
            db.close()
            return False
        except Exception as error:
            print('Member.CheckIfPrimary: ERROR - {}'.format(error))
            db = None
            return False

    def Serialize(self):
        return {
            "_id": self._id,
            "host": '{}:{}'.format(self.IP, self.port),
            "priority": self.priority
        }
