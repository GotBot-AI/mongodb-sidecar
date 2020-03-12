import os
import time
from member import Member


class Watcher:

    def __init__(self, kube, mongo, members, ipaddress):
        self.kube = kube
        self.mongo = mongo
        self.members = members
        self.pods = []
        self.sidecarIP = ipaddress
        self.primary = False

    def Start(self):
        while True:
            try:
                self.pods = self.kube.GetPods()
                exists = self.CheckForPrimaryMongo()
                if exists == True:
                    print('Watcher.CheckForPrimaryMongo: PRIMARY ALREADY IN REPLICASET')
                    self.primary = False
                elif exists == False:
                    member = Member(_id=None, IP='127.0.0.1', priority=None)
                    alive = member.CheckIfAlive()
                    if alive == True:
                        primary = member.CheckIfPodIsPrimary()
                        if primary == True:
                            self.primary = True
                            print('Watcher.CheckForPrimaryMongo: POD IS PRIMARY')
                        elif primary == False:
                            print('Watcher.CheckForPrimaryMongo: NO PRIMARY IN REPLICASET')
                            self.mongo.HoldElection(self)
                if self.primary == True:
                    self.CheckCurrentMongoPods()
                time.sleep(5)
            except Exception as error:
                print('Watcher.Start: ERROR - {}'.format(error))
                time.sleep(5)

    def CheckForPrimaryMongo(self):
        try:
            exists = False
            for pod in self.pods.items:
                if pod.status.pod_ip != None:
                    if pod.status.phase.lower() == 'running':
                        if self.sidecarIP != pod.status.pod_ip:
                            member = Member(
                                _id=None,
                                IP=pod.status.pod_ip,
                                priority=None
                            )
                            alive = member.CheckIfAlive()
                            if alive == True:
                                primary = member.CheckIfPrimary()
                                if primary == True:
                                    return True
            return False
        except Exception as error:
            print('Watcher.CheckForPrimaryMongo: ERROR - {}'.format(error))

    def CheckCurrentMongoPods(self):
        try:
            for pod in self.pods.items:
                print(
                    '{}\t{}\t{}\t'.format(
                        pod.status.pod_ip,
                        pod.metadata.name,
                        pod.status.phase,
                    )
                )
                if pod.status.pod_ip != None:
                    if pod.status.phase.lower() == 'running':
                        exists = self.CheckIfPodExistsInMembers(
                            pod.status.pod_ip
                        )
                        if exists == False:
                            state = self.members.AddMember(
                                pod.status.pod_ip
                            )
                            if state == True:
                                self.mongo.ReconfigureReplicaSet()
                    else:
                        exists = self.CheckIfPodExistsInMembers(
                            pod.status.pod_ip
                        )
                        if exists == True:
                            state = self.members.RemoveMember(
                                pod.status.pod_ip
                            )
                            if state == True:
                                self.mongo.ReconfigureReplicaSet()
            self.CheckIfAllMembersPodsRunning()
        except Exception as error:
            print('Watcher.CheckCurrentMongoPods: ERROR - {}'.format(error))

    def CheckIfPodExistsInMembers(self, podIP):
        for member in self.members.members:
            if member.IP == podIP:
                return True
        return False

    def CheckIfAllMembersPodsRunning(self):
        try:
            removed = False
            remove = []
            podIPs = []
            for pod in self.pods.items:
                if pod.status.pod_ip != None and pod.status.phase.lower() == 'running':
                    podIPs.append(pod.status.pod_ip)
            for member in self.members.members:
                if member.IP not in podIPs:
                    remove.append(member.IP)
            print('Watcher.CheckIfAllMembersPodsRunning: REMOVE LIST - {}'.format(remove))
            for memberIP in remove:
                state = self.members.RemoveMember(memberIP)
                if state == True:
                    removed == True
            if removed == True:
                self.mongo.ReconfigureReplicaSet()
        except Exception as error:
            print('Watcher.CheckIfAllMembersPodsRunning: ERROR - {}'.format(error))
