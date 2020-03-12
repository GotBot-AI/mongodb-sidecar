import socket
import os
from kubernetes import client


class KubeHandler:

    def __init__(self):
        self.api = client.CoreV1Api()
        self.namespace = os.getenv('NAMESPACE')
        self.podLabel = os.getenv('MONGO_LABEL')
        self.pods = []

    def GetPods(self):
        pods = self.api.list_namespaced_pod(
            self.namespace,
            label_selector=self.podLabel,
            watch=False
        )
        self.pods = pods
        return pods

    def Election(self):
        IPs = []
        if len(self.pods.items) > 0:
            for pod in self.pods.items:
                if pod.status.pod_ip != None and pod.status.phase.lower() == 'running':
                    IPs.append(pod.status.pod_ip)
            sortedIPs = sorted(IPs, key=lambda ip: socket.inet_aton(ip))
            return sortedIPs[0]
        else:
            return None
