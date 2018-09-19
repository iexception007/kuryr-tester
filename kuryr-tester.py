#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging

def init_logger():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(filename)s:[%(lineno)5d] - %(levelname)s: %(message)s')


from keystoneauth1 import identity
from keystoneauth1 import session
from neutronclient.v2_0 import client as neutron
from pprint import pprint
from novaclient import client as nova


class OpenstackClient():
    def __init__(self):
        username = 'admin'
        password = 'admin'
        project_name = 'admin'
        project_domain_id = 'default'
        user_domain_id = 'default'
        auth_url = 'http://10.0.0.11:35357/v3' # /etc/hosts 10.0.0.11 controller

        auth = identity.Password(auth_url=auth_url,
                          username=username,
                          password=password,
                          project_name=project_name,
                          project_domain_id=project_domain_id,
                          user_domain_id=user_domain_id)

        sess = session.Session(auth=auth)
        self.neutron = neutron.Client(session=sess)
        self.nova = nova.Client("2.6", session=sess)

    def list_networks(self):
        return self.neutron.list_networks()
        #pprint(networks)

    def list_subnets(self):
        subnets = self.neutron.list_subnets()
        #pprint(subnets)

    def list_ports(self):
        ports = self.neutron.list_ports()
        #pprint(ports)
        return ports

    def show_port(self, port_id):
        port = self.neutron.show_port(port_id)
        pprint(port)

    def get_lb(self):
        pass
    def get_pool(self):
        pass
    def get_member(self):
        pass
    def get_haproxy(self):
        pass

    #nova boot --flavor m1.nano --image cirros --nic net-id=502e4324-07e4-4c0d-a499-fc09d0de784e vm1
    def list_vms(self):
        print self.nova.flavors.list()
        print self.nova.glance.list()
        vms = self.nova.servers.list()
        print vms
        return vms

    def create_vm(self, name, image, flavor, net_id):
        img = self.nova.glance.find_image(image)
        print img.id
        #flavors = self.nova.flavors.list()
        print flavor
        ret = self.nova.servers.create(name=name, image=img.id, flavor="0", nics=[{'net-id': net_id}] )
        print ret


    def delete_vm(self, vm_id):
        print self.nova.servers.delete(vm_id)

    def set_vm_nic(self):
        pass
    def ping_vm(self):
        pass
    def curl_vm(self):
        pass



import yaml
import os
import commands
import time
from os import path
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pprint import pprint

class KubernetesClient():
    def __init__(self):
        config.load_kube_config("./conf/.kube/config")
        self.v1 = client.CoreV1Api()

    def kubectl_get_pod(self, namespace="default"):
        cmd_text = "./kubectl_mac --kubeconfig ./conf/.kube/config -n %s get pod" % (namespace)
        # status output
        ret = commands.getstatusoutput(cmd_text)
        print ret[0]
        #print ret[1]

    def kubectl_apply(self, yaml_file, namespace="default"):
        cmd_text = "./kubectl_mac --kubeconfig ./conf/.kube/config -n %s apply -f %s" % (namespace, yaml_file)
        ret = commands.getstatusoutput(cmd_text)
        print ret[0]
        #print ret[1]

    def kubectl_create(self, yaml_file, namespace="default"):
        cmd_text = "./kubectl_mac --kubeconfig ./conf/.kube/config -n %s create -f %s" % (namespace, yaml_file)
        ret = commands.getstatusoutput(cmd_text)
        print ret[0]
        #print ret[1]

    def kubectl_delete(self, yaml_file, namespace="default"):
        cmd_text = "./kubectl_mac --kubeconfig ./conf/.kube/config -n %s delete -f %s" % (namespace, yaml_file)
        ret = commands.getstatusoutput(cmd_text)
        print ret[0]
        #print ret[1]

    def list_namespace(self):
        for ns in self.v1.list_namespace().items:
            logging.info(ns.metadata.name)

    def list_svc(self):
        print("Listing All services with their info:\n")
        ret = self.v1.list_service_for_all_namespaces(watch=False)
        for i in ret.items:
            print("%s \t%s \t%s \t%s \t%s \n" % (
                    i.kind,
                    i.metadata.namespace,
                    i.metadata.name,
                    i.spec.cluster_ip,
                    i.spec.ports))

    def list_pod(self):
        print("Listing pods with their IPs:")
        ret = self.v1.list_pod_for_all_namespaces(watch=False)
        for i in ret.items:
            print("%s\t%s\t%s\n\t\t\t%s\t\t\t%s\t%s" % (
                                            i.metadata.namespace,
                                            i.metadata.name,
                                            i.status.pod_ip,
                                            i.status.phase,
                                            i.status.reason,
                                            i.status.message))


    def create_deploy(self, yaml_file, namespace="default", wait=False):
        with open(path.join(path.dirname(__file__), yaml_file)) as f:
            deploy = yaml.load(f)
            k8s_beta = client.ExtensionsV1beta1Api()
            print deploy['metadata']['name']
            deploy_name = deploy['metadata']['name']
            try:
                res = k8s_beta.read_namespaced_deployment(deploy_name, namespace)
            except Exception as e:
                print "not find %s, error %s" % (deploy_name, e.message)

                resp = k8s_beta.create_namespaced_deployment(body=deploy, namespace=namespace)
                while wait:
                    print "..."
                    time.sleep(1)
                    if resp.status.replicas == resp.status.available_replicas:
                        break
            print("Deployment created.")


    def status_deploy(self, deploy_name, namespace="default"):
        k8s_beta = client.ExtensionsV1beta1Api()
        res = k8s_beta.read_namespaced_deployment(name=deploy_name, namespace=namespace)
        print res.status.replicas
        print res.status.available_replicas
        if res.status.replicas == res.status.available_replicas:
            return True
        return False

    def __delete_deploy(self, deploy_name, namespace="default"):
        # get replica and get pod
        # get svc and get endpoint
        # delete is crazy.
        #self.delete_pod(pod_name, namespace)

        k8s_beta = client.ExtensionsV1beta1Api()
        api_response = k8s_beta.delete_namespaced_deployment(
            name=deploy_name,
            namespace=namespace,
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=5))
        print("Deployment deleted. status='%s'" % str(api_response.status))




    def delete_deploy(self, deploy_name, namespace="default"):
        cmd_text = "./kubectl_mac --kubeconfig ./conf/.kube/config -n %s delete deploy %s" %(namespace, deploy_name)
        os.system(cmd_text)

    def create_svc(self):
        pass

    def delete_svc(self, svc_name, namespace="default"):
        cmd_text = "./kubectl_mac --kubeconfig ./conf/.kube/config -n %s delete svc %s" % (namespace, svc_name)
        os.system(cmd_text)

    def get_svc_ip(self, svc_name, namespace="default"):
        api_instance = client.CoreV1Api()
        res = api_instance.read_namespaced_service(svc_name, namespace)
        print res.spec.cluster_ip

    def get_svc_labels(self, svc_name, namespace="default"):
        api_instance = client.CoreV1Api()
        res = api_instance.read_namespaced_service(svc_name, namespace)
        print res.metadata

    def get_endpoint(self):
        try:
            res = self.v1.list_endpoints_for_all_namespaces()
            #print res
            for i in res.items:
                print "------------------------"
                print "labels: %s" % i.metadata.labels
                if None == i.subsets:
                    continue
                for s in i.subsets:
                    if None == s.addresses:
                        continue
                    for a in s.addresses:
                        print a.ip
                    for p in s.ports:
                        print p.port
                print "========================"

            #pprint(api_response)
        except ApiException as e:
            print("Exception when calling CoreV1Api->list_endpoints_for_all_namespaces: %s\n" % e)
        pass

    def create_pod(self, yaml_file, namespace="default", wait=False):
        with open(path.join(path.dirname(__file__), yaml_file)) as f:
            body = yaml.load(f)
            pod_name = body['metadata']['name']
            api_instance = client.CoreV1Api()
            try:
                res = api_instance.read_namespaced_pod(pod_name, namespace)
                print "%s -- %s" %(pod_name,res.status.phase)
            except Exception as e:
                print "not find %s, error %s" % (pod_name, e.message)
                res = api_instance.create_namespaced_pod(namespace, body)
                print res

                while wait:
                    time.sleep(1)
                    print "..."
                    pod = api_instance.read_namespaced_pod(pod_name, namespace)
                    if pod.status.phase == "Running":
                        break

    def delete_pod(self, pod_name, namespace='default'):
        api_instance = client.CoreV1Api()
        body = client.V1DeleteOptions()
        res = api_instance.delete_namespaced_pod(pod_name, namespace, body)
        print res

    def get_pod_label(self, pod_name, namespace="default"):
        api_instance = client.CoreV1Api()
        res = api_instance.read_namespaced_pod(pod_name, namespace)
        print res.metadata.labels


    def get_pod_status(self, pod_name, namespace="default"):
        api_instance = client.CoreV1Api()
        res = api_instance.read_namespaced_pod(pod_name, namespace)
        print res.status.phase



def main():
    init_logger()
    logging.info("Openstack client api")
    openstack_client = OpenstackClient()
    networks = openstack_client.list_networks()
    pprint(networks)

    openstack_client.list_subnets()
    ports = openstack_client.list_ports()
    for port in ports['ports']:
        id =  port['id']
        print id
        openstack_client.show_port(id)

    vms = openstack_client.list_vms()
    for vm in vms:
        #print type(vm)
        print vm.name
        print vm.id
        openstack_client.delete_vm(vm.id)

    openstack_client.create_vm(name="vm3", image="cirros", flavor="m1.nano", net_id="502e4324-07e4-4c0d-a499-fc09d0de784e")
    openstack_client.create_vm(name="vm4", image="cirros", flavor="m1.nano", net_id="502e4324-07e4-4c0d-a499-fc09d0de784e")
    openstack_client.create_vm(name="vm5", image="cirros", flavor="m1.nano", net_id="502e4324-07e4-4c0d-a499-fc09d0de784e")
    vms = openstack_client.list_vms()
    for vm in vms:
        print vm.name

    logging.info("kubernetes client api")

    client = KubernetesClient()
    logging.info("------kubectl_mac --------")
    client.kubectl_create("./yaml/deploy.yaml")
    client.kubectl_delete("./yaml/svc.yaml")
    client.kubectl_create("./yaml/svc.yaml")
    client.kubectl_create("./yaml/pod.yaml")
    # client.kubectl_get_pod()
    # client.kubectl_delete("./yaml/deploy.yaml")
    # client.kubectl_delete("./yaml/svc.yaml")
    # client.kubectl_delete("./yaml/pod.yaml")


    logging.info("------svc------")
    #client.list_svc()
    client.get_svc_ip("wise2c-svc")
    client.get_svc_labels("wise2c-svc")


    logging.info("------namespaces------")
    #client.list_namespace()


    logging.info("------pod------")
    #client.list_pod()

    logging.info("------endpoint------")
    #client.get_endpoint()

    logging.info("------create_deploy-----")
    #client.create_deploy("./yaml/deploy.yaml", wait=True)
    logging.info("------delete_deploy-----")
    #client.delete_deploy("wise2c-nginx")



    logging.info("------create_pod-------")
    # client.create_pod("./yaml/pod.yaml", wait=True)
    # client.get_pod_label("wisecloud-pod")
    # client.get_pod_status("wisecloud-pod")
    # client.delete_pod("wisecloud-pod")

if __name__ == '__main__':
    main()