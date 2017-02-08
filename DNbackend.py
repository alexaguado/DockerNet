__author__ = 'alejandroaguado'

import redis, logging, sys, json, time
import netifaces as ni
from subprocess import check_output
from docker import Client
import traceback

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

docky=Client(base_url='unix://var/run/docker.sock')

def load_state():
    r=redis.StrictRedis(host="0.0.0.0",port=6379,db=0)
    n=r.get("dockernet")
    nets={}
    if None!=n:
        nets=json.loads(n)
    return nets

def save_state(n):
    r=redis.StrictRedis(host="0.0.0.0",port=6379,db=0)
    logger.info("Saving status")
    r.set("dockernet",json.dumps(n))
    logger.info("Saved")

def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def add_node(t,n):
    try:
        if n['type']=="OVS":
            check_output(["sudo","ovs-vsctl","add-br",n['id']])
            if "controller" in t.keys():
                logger.info("Adding controller "+t['controller']['ip']+" to "+n['id'])
                time.sleep(0.5)
                check_output(["sudo","ovs-vsctl","set-controller",n['id'],"tcp:"+t['controller']['ip']+":6633"])
            fakedpid=check_output(["sudo", "ovs-vsctl", "get", "bridge", n['id'], "datapath-id"]).replace('"',"")
            j=0
            dpid=""
            while j<len(fakedpid)-1:
                dpid+=fakedpid[j:j+2]+":"
                j+=2
            dpid=dpid[:-1]
            n['dpid']=dpid
        elif n['type']=="LC":
            hc=docky.create_host_config(privileged=True)
            docky.create_container(image=n['image'], stdin_open=True, tty=True,command="/bin/bash", name=n['id'], detach=True, host_config=hc)
            docky.start(n['id'])
    except:
        logger.warn("Error adding node: "+n['id'])


#TODO: add first the node information in the node if required (editing)!!!!!!!!!
def add_edge(t,e):
    try:
        if t['nodes'][e['src']['id']]['type']=="LC" and t['nodes'][e['dst']['id']]['type']=="LC":
            logger.warn("LC to LC edge not supported :(")
        elif t['nodes'][e['src']['id']]['type']=="LC":
            ibef=check_output(["sudo","ovs-vsctl","list-ifaces",e['dst']['id']]).split("\n")
            check_output(['sudo', 'ovs-docker', 'add-port', ''+e['dst']['id']+'', e['src']['intf'], ''+e['src']['id']+'', '--ipaddress='+t['nodes'][e['src']['id']]['intf'][e['src']['intf']]['ip']+'/24'])
            iaft=check_output(["sudo","ovs-vsctl","list-ifaces",e['dst']['id']]).split("\n")
            pname=list(set(iaft) - set(ibef))[0]
            port=str(json.loads(check_output(["sudo","ovs-vsctl","--columns=ofport","--format=json","list","interface", pname]))["data"][0][0])
            t['nodes'][e['src']['id']]['intf'][e['src']['intf']]['attpoint']=t['nodes'][e['dst']['id']]['dpid']+"|"+port
            mac=""
            try:
                mac=check_output(["./get_intf_mac.sh",e['src']['id'],e['src']['intf']])[:-1]
            except:
                print "mac not found..."
            t['nodes'][e['src']['id']]['intf'][e['src']['intf']]["mac"]=mac
            info=docky.exec_create(e['src']['id'],"ping "+t['nodes'][e['src']['id']]['intf'][e['src']['intf']]['gw']+" -c 5")
            exid=info['Id']
            docky.exec_start(exid,detach=True)
            #print ["sudo", "ovs-vsctl","set", "port", pname, "tag="+e['src']['vlan']]
            if "vlan" in e['src'].keys():
                check_output(["sudo", "ovs-vsctl","set", "port", pname, "tag="+e['src']['vlan']])
        elif t['nodes'][e['dst']['id']]['type']=="LC":
            ibef=check_output(["sudo","ovs-vsctl","list-ifaces",e['src']['id']]).split("\n")
            check_output(['sudo', 'ovs-docker', 'add-port', ''+e['src']['id']+'', e['dst']['intf'], ''+e['dst']['id']+'', '--ipaddress='+t['nodes'][e['dst']['id']]['intf'][e['dst']['intf']]['ip']+'/24'])
            iaft=check_output(["sudo","ovs-vsctl","list-ifaces",e['src']['id']]).split("\n")
            pname=list(set(iaft) - set(ibef))[0]
            port=str(json.loads(check_output(["sudo","ovs-vsctl","--columns=ofport","--format=json","list","interface", pname]))["data"][0][0])
            t['nodes'][e['dst']['id']]['intf'][e['dst']['intf']]['attpoint']=t['nodes'][e['src']['id']]['dpid']+"|"+port
            mac=""
            try:
                mac=check_output(["./get_intf_mac.sh",e['dst']['id'],e['dst']['intf']])[:-1]
            except:
                print "mac not found..."
            t['nodes'][e['dst']['id']]['intf'][e['dst']['intf']]["mac"]=mac
            info=docky.exec_create(e['dst']['id'],"ping "+t['nodes'][e['dst']['id']]['intf'][e['dst']['intf']]['gw']+" -c 5")
            exid=info['Id']
            docky.exec_start(exid,detach=True)
            #print ["sudo", "ovs-vsctl","set", "port", pname, "tag="+e['dst']['vlan']]
            if "vlan" in e['dst'].keys():
                check_output(["sudo", "ovs-vsctl","set", "port", pname, "tag="+e['dst']['vlan']])
        elif t['nodes'][e['src']['id']]['type']=="OVS" and t['nodes'][e['dst']['id']]['type']=="OVS":
            check_output(["sudo", "ovs-vsctl", "add-port", e['src']['id'], "from_"+e['src']['id']+"_to_"+e['dst']['id']])
            check_output(["sudo", "ovs-vsctl", "add-port", e['dst']['id'], "from_"+e['dst']['id']+"_to_"+e['src']['id']])
            check_output(["sudo","ovs-vsctl", "set", "interface", "from_"+e['src']['id']+"_to_"+e['dst']['id'], "type=patch", "options:peer="+"from_"+e['dst']['id']+"_to_"+e['src']['id']])
            check_output(["sudo","ovs-vsctl", "set", "interface", "from_"+e['dst']['id']+"_to_"+e['src']['id'], "type=patch", "options:peer="+"from_"+e['src']['id']+"_to_"+e['dst']['id']])
        else:
            logger.warn("Link error: Technologies not found")
    except:
        logger.warn("Error adding edge: "+json.dumps(e))
        logger.warn(traceback.format_exc())


def del_edge(t,e):
    try:
        if t['nodes'][e['src']['id']]['type']=="LC" and t['nodes'][e['dst']['id']]['type']=="LC":
            logger.warn("LC to LC edge not supported :(")
        elif t['nodes'][e['src']['id']]['type']=="LC":
            check_output(['sudo', 'ovs-docker', 'del-port', ''+e['dst']['id']+'', e['src']['intf'], ''+e['src']['id']+'', '--ipaddress='+t['nodes'][e['src']['id']]['intf'][e['src']['intf']]['ip']+'/24'])
        elif t['nodes'][e['dst']['id']]['type']=="LC":
            check_output(['sudo', 'ovs-docker', 'del-port', ''+e['src']['id']+'', e['dst']['intf'], ''+e['dst']['id']+'', '--ipaddress='+t['nodes'][e['dst']['id']]['intf'][e['dst']['intf']]['ip']+'/24'])
        elif t['nodes'][e['src']['id']]['type']=="OVS" and t['nodes'][e['dst']['id']]['type']=="OVS":
            check_output(["sudo", "ovs-vsctl", "del-port", e['src']['id'], "from_"+e['src']['id']+"_to_"+e['dst']['id']])
            check_output(["sudo", "ovs-vsctl", "del-port", e['dst']['id'], "from_"+e['dst']['id']+"_to_"+e['src']['id']])
        else:
            logger.warn("Link error: Technologies not found")
    except:
        logger.warn("Error adding edge: "+json.dumps(e))


def del_node(t,n):
    try:
        if n['type']=="OVS":
            tobedel=[]
            for e in t['edges']:
                if n['id'] in [e['src']['id'],e['dst']['id']]:
                    print "DELETING EDGE!!!"+json.dumps(e)
                    del_edge(t,e)
                    tobedel.append(e)
            for e in tobedel:
                if t['nodes'][e['src']['id']]['type']=="LC":
                    del t['nodes'][e['src']['id']]['intf'][e['src']['intf']]
                if t['nodes'][e['dst']['id']]['type']=="LC":
                    del t['nodes'][e['dst']['id']]['intf'][e['dst']['intf']]
                t['edges'].remove(e)
            check_output(["sudo","ovs-vsctl","del-br",n['id']])
        elif n['type']=="LC":
            tobedel=[]
            for e in t['edges']:
                if n['id'] in [e['src']['id'],e['dst']['id']]:
                    del_edge(t,e)
                    tobedel.append(e)
            for e in tobedel:
                if t['nodes'][e['src']['id']]['type']=="LC":
                    del t['nodes'][e['src']['id']]['intf'][e['src']['intf']]
                if t['nodes'][e['dst']['id']]['type']=="LC":
                    del t['nodes'][e['dst']['id']]['intf'][e['dst']['intf']]
                t['edges'].remove(e)
            docky.stop(n['id'])
            docky.remove_container(n['id'])
    except:
        print n
        logger.warn("Error deleting node: "+n['id'])

def add_controller(t,ip, switch):
    check_output(["sudo","ovs-vsctl","set-controller",switch,"tcp:"+ip+":6633"])
    '''
    for n in t['nodes'].keys():
        if t['nodes'][n]['type']=="OVS":
            try:
                check_output(["sudo","ovs-vsctl","set-controller",n,"tcp:"+ip+":6633"])
            except:
                logger.warn("Error adding controller to "+n)
    '''
    t['nodes'][switch]['controller']=ip
    #t['controller']={"ip":ip}

def create_topology_from_data(t):
    #It's assumed that at this point the topology has been checked through "validate_input_data(t)"
    for k in t['nodes'].keys():
        add_node(t,t['nodes'][k])
    for e in t['edges']:
        add_edge(t,e)
    for k in t['nodes'].keys():
        if "controller" in t['nodes'][k].keys():
            add_controller(t,t['nodes'][k]['controller']['ip'], k)
    i=0
    if "attachPoints" in t.keys():
        for ap in t['attachPoints']:
            try:
                check_output(["sudo","ovs-vsctl","add-port",ap['switch'],ap['interface']])
                i+=1
            except:
                logger.warn("Error adding attachment point: "+json.dumps(ap))
                del t[i]

dnet=load_state()
if dnet=={}:
    dnet={"nodes":{}, "edges":[]}