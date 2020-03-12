import os
import socket
import re
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure


class MongoHandler:

    def __init__(self, kube):
        self._members = None
        self._kube = kube
        self.host = '127.0.0.1'
        self.port = int(os.getenv('MONGO_PORT'))
        self.replicaSetName = os.getenv('REPLICA_SET_NAME')
        self.username = os.getenv('MONGO_USERNAME')
        self.password = os.getenv('MONGO_PASSWORD')
        self.db = MongoClient(
            self.host,
            self.port,
            replicaset=self.replicaSetName,
            serverSelectionTimeoutMS=100,
            username=self.username,
            password=self.password
        )
        self.ipaddress = socket.gethostbyname(socket.gethostname())

    def setMembers(self, members):
        self._members = members

    def members(self):
        '''
        Returns serialized version of all the members for mongo config
        '''
        return self._members.Serialize()

    def GetReplicaSetStatus(self):
        try:
            status = self.db.admin.command('replSetGetStatus')
            return status
        except Exception as error:
            if error.args[0] == 'No replica set members match selector "Primary()"':
                pass
            if error.args[0] == 'Our replica set config is invalid or we are not a member of it':
                pass
            print(error)
            return None

    def HoldElection(self, watcher):
        winner = self._kube.Election()
        print('MongoHandler.HoldElection: IP {} WON ELECTION'.format(winner))
        if winner == self.ipaddress:
            watcher.primary = True
            print('MongoHandler.HoldElection: POD WON ELECTION')
            self.InitializeReplicaSet()

    def InitializeReplicaSet(self):
        try:
            print('MongoHandler.InitializeReplicaSet: INITIALIZING')
            self._members.members = []
            self._members.AddPrimaryMember(self.ipaddress)
            self.db = MongoClient(
                self.host,
                self.port,
                serverSelectionTimeoutMS=100,
                username=self.username,
                password=self.password
            )
            res = self.db.admin.command('replSetInitiate', {}, force=True)
            self.ReconfigureReplicaSet()
        except OperationFailure as error:
            print(error)
            if error.args[0] == 'already initialized':
                self.ReconfigureReplicaSet()

    def ReconfigureReplicaSet(self):
        try:
            print('MongoHandler.ReconfigureReplicaSet: ATTEMPTING')
            conf = self.db.admin.command('replSetGetConfig', 1)
            for member in conf['config']['members']:
                for selfMember in self._members.members:
                    if selfMember.IP in member['host']:
                        selfMember._id = member['_id']
            conf['config']['version'] += 1
            conf['config']['protocolVersion'] = 1
            conf['config']['members'] = self.members()
            resp = self.db.admin.command(
                'replSetReconfig',
                conf['config'],
                force=True
            )
            if (resp['ok'] == 1.0):
                print('MongoHandler.ReconfigureReplicaSet: SUCCESS')
            else:
                print('MongoHandler.ReconfigureReplicaSet: FAILED')
        except OperationFailure as error:
            print('MongoHandler.ReconfigureReplicaSet: ERROR - {}'.format(error))

    def GetPrimary(self):
        try:
            status = self.db.admin.command('replSetGetStatus')
            if len(status["members"]) > 0:
                for member in status["members"]:
                    if member["state"] == 1:
                        return member["name"].split(':')[0]
        except Exception as error:
            print('MongoHandler.GetPrimaryError: {}'.format(error))
            return None
