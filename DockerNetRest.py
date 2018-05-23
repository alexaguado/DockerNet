__author__ = 'alejandroaguado'

import web, time
from  httpResponses import *
from DNbackend import *
import netifaces as ni

rooturl='/dockernet/rest/'

urls = (
  rooturl+'topology', 'topologymgmt',
  rooturl+'nodes/(.*)', 'nodemgmt',
  rooturl+'edges/(.*)', 'edgemgmt',
  rooturl+'attachPoints', 'attPoint',
  rooturl+'vxlantunnel', 'vxlantunnel',
  rooturl+'controller', 'controller',
  rooturl+'images', 'images',
  rooturl+'interfaces', 'interfaces',
  rooturl+'stats/(.*)', 'stats'
)

class MyApplication(web.application):

    def run(self, port=8080, *middleware):
        #self.events=dict(events)
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))


#-------- Topo MGMT --------

class topologymgmt:

    def GET(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Topo MGMT ::: GET")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        raise httpResponse(httpmsgtypes['Success'],'Successful operation',json.dumps(dnet))

    def POST(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Topo MGMT ::: POST")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        if len(dnet['nodes'].keys())==0:
            try:
                t=json.loads(web.data())
                create_topology_from_data(t)
                dnet['nodes']=t['nodes']
                dnet['edges']=t['edges']
                if "attachPoints" in t.keys():
                    dnet['attachPoints']=t['attachPoints']
                if "vxlantunnel" in t.keys():
                    dnet['vxlantunnel']=t['vxlantunnel']
                save_state(dnet)
            except:
                raise httpResponse(httpmsgtypes['BadRequest'],"Malformed JSON")
        else:
            raise httpResponse(httpmsgtypes['Conflict'],"Currently there is a topology running")
        raise httpResponse(httpmsgtypes['Success'],'Successful operation',"OK")

    def DELETE(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        web.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        logger.info("Topo MGMT ::: DELETE")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        for n in dnet['nodes'].keys():
            del_node(dnet,dnet['nodes'][n])
        dnet['nodes']={}
        dnet['edges']=[]
        if "controller" in dnet.keys():
            del dnet['controller']
        if "attachPoints" in dnet.keys():
            del dnet['attachPoints']
        if "vxlantunnel" in dnet.keys():
            del dnet['vxlantunnel']
        save_state(dnet)
        raise httpResponse(httpmsgtypes['Success'],'Successful operation',json.dumps(dnet))

    def OPTIONS(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        raise httpResponse(httpmsgtypes['Success'],'Successful operation','{"description":"Options called CORS"}')

#-------- Node MGMT --------

class nodemgmt:

    def GET(self,node):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Node MGMT ::: GET")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        if node == None or node == "" or node=="all":
            raise httpResponse(httpmsgtypes['Success'],'Successful operation',json.dumps(dnet['nodes']))
        elif node in dnet['nodes'].keys():
            raise httpResponse(httpmsgtypes['Success'],'Successful operation',json.dumps(dnet['nodes'][node]))
        else:
            raise httpResponse(httpmsgtypes['NotFound'],"Node '"+node+"' not found")

    def POST(self,node):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Node MGMT ::: POST")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        imgs=[]
        try:
            data=json.loads(web.data())
        except:
            raise httpResponse(httpmsgtypes['BadRequest'],"Malformed JSON")
        type=data['type']
        id=node
        if id in dnet['nodes'].keys():
            raise httpResponse(httpmsgtypes['Conflict'],"ID already exists")
        if type=="LC":
            info=docky.images()
            for i in info:
                imgs.append(i['RepoTags'][0])
            if data['image'] not in imgs:
                raise httpResponse(httpmsgtypes['NotFound'],"Image not found")
            nodeaux={"id":id,"type":type,"image":data['image'],"intf":{}}
        else:
            nodeaux={"id":id,"type":type,"intf":{}} #TODO: Check if interfaces are necessary here
        try:
            add_node(dnet,nodeaux)
            dnet['nodes'][id]=nodeaux
            save_state(dnet)
        except:
            httpResponse(httpmsgtypes['InternalServer'],"Exception adding node")
        raise httpResponse(httpmsgtypes['Success'],'Successful operation',json.dumps(dnet['nodes'][node]))

    def DELETE(self,node):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        web.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        logger.info("Node MGMT ::: DELETE")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        if node not in dnet['nodes'].keys():
            raise httpResponse(httpmsgtypes['NotFound'],"Node not found")
        nodeaux=dnet['nodes'][node]
        del_node(dnet,nodeaux)
        del dnet['nodes'][node]
        save_state(dnet)
        raise httpResponse(httpmsgtypes['Success'],'Successful operation',node)

    def OPTIONS(self,node):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        web.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        raise httpResponse(httpmsgtypes['Success'],'Successful operation','{"description":"Options called CORS"}')

#-------- Edge MGMT --------

class edgemgmt:

    def GET(self,edge):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Edge MGMT ::: GET")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        if edge == None or edge == "" or edge=="-1":
            raise httpResponse(httpmsgtypes['Success'],'Successful operation',json.dumps(dnet['edges']))
        elif RepresentsInt(edge) and int(edge) < len(dnet['edges']) and int(edge)>0:
            raise httpResponse(httpmsgtypes['Success'],'Successful operation',json.dumps(dnet['edges'][int(edge)]))
        else:
            raise httpResponse(httpmsgtypes['NotFound'],"Edge '"+edge+"' not found. Please provide position")

    #edge var is IGNORED here
    def POST(self,edge):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Edge MGMT ::: POST")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        opt={}
        try:
            webdat=web.data()
            data=json.loads(webdat)['link']
        except:
            raise httpResponse(httpmsgtypes['BadRequest'],"Malformed JSON")
        issvl=False
        isdvl=False
        srcid=data['src']['id']
        dstid=data['dst']['id']
        if srcid not in dnet['nodes'].keys() or dstid not in dnet['nodes'].keys():
            raise httpResponse(httpmsgtypes['NotFound'],"Node(s) not found")
        if dnet['nodes'][srcid]['type']=="LC" and dnet['nodes'][dstid]['type']=="LC":
            raise httpResponse(httpmsgtypes['Conflict'],"LC to LC not supported")
        if dnet['nodes'][srcid]['type']=="OVS" and dnet['nodes'][dstid]['type']=="OVS" and data in dnet['edges']:
            raise httpResponse(httpmsgtypes['Conflict'],"Link already exists. Multiple links not supported by now.")
        if dnet['nodes'][srcid]['type']=="LC":
            try:
                iname=data['src']['intf']
                iip=data['src']['ip']
                if iname in dnet['nodes'][srcid]['intf'].keys():
                    raise httpResponse(httpmsgtypes['BadRequest'],"Interface name '"+iname+"' exists")
            except:
                raise httpResponse(httpmsgtypes['BadRequest'],"Interface info not available")
            vlan=None
            if "vlan" in data['src'].keys():
                vlan=data['src']['vlan']
                issvl=True
            aux=iip.split(".")[:-1]
            aux.append("0")
            gw=".".join(aux)
            if "vlan" in data['src'].keys():
                intf = {"ip": iip, "mask": "24", "gw": gw,"vlan":vlan}
            else:
                intf={"ip":iip,"mask":"24","gw":gw}
            dnet['nodes'][srcid]['intf'][iname]=intf
        if dnet['nodes'][dstid]['type']=="LC":
            try:
                iname=data['dst']['intf']
                iip=data['dst']['ip']
                if iname in dnet['nodes'][dstid]['intf'].keys():
                    raise httpResponse(httpmsgtypes['BadRequest'],"Interface name '"+iname+"' exists")
            except:
                raise httpResponse(httpmsgtypes['BadRequest'],"Interface info not available")
            vlan = None
            if "vlan" in data['dst'].keys():
                vlan = data['dst']['vlan']
                isdvl=True
            aux=iip.split(".")[:-1]
            aux.append("0")
            gw=".".join(aux)
            if "vlan" in data['dst'].keys():
                intf = {"ip": iip, "mask": "24", "gw": gw,"vlan":vlan}
            else:
                intf={"ip":iip,"mask":"24","gw":gw}
            dnet['nodes'][dstid]['intf'][iname]=intf
        aux=data
        #if issvl:
        #    del aux['src']['vlan']
        #if isdvl:
        #    del aux['dst']['vlan']
        dnet['edges'].append(aux)
        add_edge(dnet,data)
        save_state(dnet)
        raise httpResponse(httpmsgtypes['Success'],'Successful operation',json.dumps(data))

    #TODO: needs to be tested
    #edge var is IGNORED here
    def DELETE(self,edge):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        web.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        logger.info("Edge MGMT ::: DELETE")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        try:
            data=json.loads(web.data())['link']
        except:
            raise httpResponse(httpmsgtypes['BadRequest'],"Malformed JSON")
        if data not in dnet['edges']:
            raise httpResponse(httpmsgtypes['NotFound'],"Edge not found")
        else:
            del_edge(dnet,data)
            if dnet['nodes'][data['src']['id']]['type']=="LC":
                del dnet['nodes'][data['src']['id']]['intf'][data['src']['intf']]
            if dnet['nodes'][data['dst']['id']]['type']=="LC":
                del dnet['nodes'][data['dst']['id']]['intf'][data['dst']['intf']]
            logger.info(json.dumps(dnet['edges']))
            dnet['edges'].remove(data)
            logger.info(json.dumps(dnet['edges']))
        save_state(dnet)
        raise httpResponse(httpmsgtypes['Success'],'Successful operation','Edge '+json.dumps(data)+" succesfully removed")


    def OPTIONS(self,edge):
        #web.header('Access-Control-Allow-Origin','*')
        web.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        raise httpResponse(httpmsgtypes['Success'],'Successful operation','{"description":"Options called CORS"}')


#-------- AttchPoint --------
class attPoint:

    def GET(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Edge ATTP ::: GET")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        if 'attachPoints' in dnet.keys():
            raise httpResponse(httpmsgtypes['Success'],'Success',json.dumps(dnet['attachPoints']))
        else:
            raise httpResponse(httpmsgtypes['NotFound'],"No attachment points found")

    def POST(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Edge ATTP ::: POST")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        try:
            data=json.loads(web.data())
            switch=data['switch']
            intf=data['interface']
        except:
            raise httpResponse(httpmsgtypes['BadRequest'],"Malformed JSON")
        if switch not in dnet['nodes'].keys() or dnet['nodes'][switch]['type'] != "OVS":
            raise httpResponse(httpmsgtypes['NotFound'],"Node "+switch+" is not valid")
        if "attachPoints" in dnet.keys():
            for ap in dnet['attachPoints']:
                if intf == ap['interface']:
                    raise httpResponse(httpmsgtypes['Conflict'],"The interface is being used.")
        #try:
        check_output(["sudo","ovs-vsctl","add-port",switch,intf])
        if "attachPoints" not in dnet.keys():
            dnet['attachPoints']=[]
        dnet['attachPoints'].append({"switch":switch,"interface":intf})
        save_state(dnet)
        raise httpResponse(httpmsgtypes['Success'],'Success',"OK")
        #except:
         #   raise httpResponse(httpmsgtypes['InternalServer'],'Error attaching network')

    def DELETE(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        web.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        logger.info("Edge ATTP ::: DELETE")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        try:
            data=json.loads(web.data())
            switch=data['switch']
            intf=data['interface']
        except:
            raise httpResponse(httpmsgtypes['BadRequest'],"Malformed JSON")
        if "attachPoints" not in dnet.keys() or data not in dnet['attachPoints']:
            raise httpResponse(httpmsgtypes['NotFound'],"Attachment point not found")
        else:
            check_output(["sudo","ovs-vsctl","del-port",switch,intf])
            dnet['attachPoints'].remove(data)
            save_state(dnet)
            raise httpResponse(httpmsgtypes['Success'],'Success',json.dumps(dnet['attachPoints']))

    def OPTIONS(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        web.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        raise httpResponse(httpmsgtypes['Success'],'Successful operation','{"description":"Options called CORS"}')

#-------- tunnel --------
class vxlantunnel:

    def GET(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Edge ATTP ::: GET")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        if 'vxlantunnel' in dnet.keys():
            raise httpResponse(httpmsgtypes['Success'],'Success',json.dumps(dnet['vxlantunnel']))
        else:
            raise httpResponse(httpmsgtypes['NotFound'],"No vxlantunnels points found")

    def POST(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Edge ATTP ::: POST")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        try:
            data=json.loads(web.data())
            switch=data['switch']
            port=data['port']
            remoteip=data['remote']
        except:
            raise httpResponse(httpmsgtypes['BadRequest'],"Malformed JSON")
        if switch not in dnet['nodes'].keys() or dnet['nodes'][switch]['type'] != "OVS":
            raise httpResponse(httpmsgtypes['NotFound'],"Node "+switch+" is not valid")
        if "vxlantunnel" in dnet.keys():
            for ap in dnet['vxlantunnel']:
                if (port == ap['port']) and (switch == ap['switch']):
                    raise httpResponse(httpmsgtypes['Conflict'],"The port already exists at the switch.")
        #try:
        check_output(["sudo","ovs-vsctl","add-port",switch,port,"--","set","interface",port,"type=vxlan","options:remote_ip="+remoteip,"options:key=flow"])
        if "vxlantunnel" not in dnet.keys():
            dnet['vxlantunnel']=[]
        dnet['vxlantunnel'].append(data)
        save_state(dnet)
        raise httpResponse(httpmsgtypes['Success'],'Success',"OK")
        #except:
         #   raise httpResponse(httpmsgtypes['InternalServer'],'Error attaching network')

    def DELETE(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        web.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        logger.info("Edge ATTP ::: DELETE")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        try:
            data=json.loads(web.data())
            switch=data['switch']
            port=data['port']
        except:
            raise httpResponse(httpmsgtypes['BadRequest'],"Malformed JSON")
        if "vxlantunnel" not in dnet.keys() or data not in dnet['vxlantunnel']:
            raise httpResponse(httpmsgtypes['NotFound'],"tunnel not found")
        else:
            check_output(["sudo","ovs-vsctl","del-port",switch,port])
            dnet['vxlantunnel'].remove(data)
            save_state(dnet)
            raise httpResponse(httpmsgtypes['Success'],'Success',json.dumps(dnet['vxlantunnel']))

    def OPTIONS(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        web.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        raise httpResponse(httpmsgtypes['Success'],'Successful operation','{"description":"Options called CORS"}')

class controller:

    def GET(self):
        web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Edge CTRL ::: GET")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        resp={}
        for k in dnet['nodes'].keys():
            if "controller" in dnet['nodes'][k].keys():
                resp[k]=dnet['nodes'][k]['controller']
        raise httpResponse(httpmsgtypes['Success'],'Success',json.dumps(resp))

    def POST(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Edge CTRL ::: POST")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        try:
            data=json.loads(web.data())
        except:
            raise httpResponse(httpmsgtypes['BadRequest'],"Malformed JSON")
        if data['switch'] not in dnet['nodes'].keys() or dnet['nodes'][data['switch']]['type'] != "OVS":
            raise httpResponse(httpmsgtypes['NotFound'],"Node '"+data['switch']+"' not found")
        add_controller(dnet,data['ip'],data['switch'])
        save_state(dnet)
        raise httpResponse(httpmsgtypes['Success'],'Success',json.dumps(dnet['nodes'][data['switch']]))

    def DELETE(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        #web.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        logger.info("Edge CTRL ::: DELETE")
        dnet = load_state()
        if dnet == {}:
            dnet = {"nodes": {}, "edges": []}
        try:
            data=json.loads(web.data())
            switch=data['switch']
        except:
            raise httpResponse(httpmsgtypes['BadRequest'],"Malformed JSON")
        if switch not in dnet['nodes'].keys():
            raise httpResponse(httpmsgtypes['NotFound'],"Switch "+switch+" not found")
        if "controller" not in dnet['nodes'][switch].keys():
            raise httpResponse(httpmsgtypes['NotFound'],"No controller in switch "+switch)
        else:
            try:
                check_output(["sudo","ovs-vsctl","del-controller",switch])
            except:
                logger.info("ERROR")
            del dnet['nodes'][switch]['controller']
            save_state(dnet)
            raise httpResponse(httpmsgtypes['Success'],'Success',json.dumps(dnet))


    def OPTIONS(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        web.header("Access-Control-Allow-Methods", "GET,POST,OPTIONS,PUT,DELETE")
        raise httpResponse(httpmsgtypes['Success'],'Successful operation','{"description":"Options called CORS"}')


class images:

    def GET(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Edge IMGS ::: GET")
        info=docky.images()
        imgs=[]
        for i in info:
            imgs.append(i['RepoTags'][0])
        raise httpResponse(httpmsgtypes['Success'],'Success',json.dumps(imgs))

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        raise httpResponse(httpmsgtypes['Success'],'Successful operation','{"description":"Options called CORS"}')


class interfaces:

    def GET(self):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Edge INTFS ::: GET")
        pint = ni.interfaces()
        interfaces = []
        for i in pint:
            if ("em" in i or "eth" in i or "enx" in i or "rename" in i) and ("veth" not in i and "ovs" not in i):
                interfaces.append(i)
        raise httpResponse(httpmsgtypes['Success'],'Success',json.dumps(interfaces))

    def OPTIONS(self):
        web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        raise httpResponse(httpmsgtypes['Success'],'Successful operation','{"description":"Options called CORS"}')

class stats:

    def GET(self,node):
        #web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        logger.info("Edge INTFS ::: GET")
        try:
            print stts
            st=stts['stats']
            if node==None or node=="" or node=="-1" or node=="all":
                resp=json.dumps(st)
            else:
                if node in st.keys():
                    resp=json.dumps(st[node])
                else:
                    resp='{"Error":"Node not found"}'
        except:
            resp='{"Error":"bad response"}'
        raise httpResponse(httpmsgtypes['Success'],'Success',resp)

    def OPTIONS(self,node):
        web.header('Access-Control-Allow-Origin','*')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        raise httpResponse(httpmsgtypes['Success'],'Successful operation','{"description":"Options called CORS"}')

if __name__ == "__main__":
    app = MyApplication(urls, globals())
    app.run(8085)
