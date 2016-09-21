import sys
import socket
import utils
from thread import *

SERV_PORT = 7734
SERV_HOST = ''

LOGGING = 1

#host:port
active_peers = {}
#RFC_id: [(title,host,port),...]
RFC_inventory = {}

#lock for Active Peer dictionary
AP_lock = allocate_lock()
#lock for RFC inventory dictionary
RFCI_lock = allocate_lock()

#get port peer is listening on and add its entry to active peer dic
def register_peer(soc,addr):
	peer_hname = socket.gethostbyaddr(addr[0])
	if peer_hname=="":
		print "Failed to resolve host address "+str(addr[0])
		sys.exit()
	AP_lock.acquire()
	active_peers[peer_hname[0]] = 0
	AP_lock.release()

def add_RFC(rqst):
	msg_lines = rqst.split('\n')
	for line in msg_lines:
		if len(line.split())<=0:
			continue
		line_token = line.split()

		if line_token[0]=='ADD':
			RFC_id = line_token[2].strip()
		if line_token[0]=='Host:':
			host = line_token[1].strip()
		if line_token[0]=='Port:':
			port = line_token[1].strip()
		if line_token[0]=='Title:':
			RFC_title = ' '.join(line_token[1:])

	#update port no in peer list
	AP_lock.acquire()
	active_peers[host]=port
	AP_lock.release()

	RFCI_lock.acquire()
	if RFC_id in RFC_inventory:
		RFC_inventory[RFC_id].append((RFC_title,host,port))
	else:
		RFC_inventory[RFC_id]=[(RFC_title,host,port)]
	RFCI_lock.release()
	resp = utils.create_resp_message(200,[(RFC_id,RFC_title,host,port)])
	return resp

def lookup_RFC(rqst):
	msg_lines = rqst.split('\n')
	RFC_id = ''
	for line in msg_lines:
		if len(line.split())<=0:
			continue
		line_token = line.split()
		if line_token[0]=='LOOKUP':
			RFC_id = line_token[2].strip()

		if len(RFC_id) == 0:
			resp = utils.create_resp_message(400,[])
		else:
			RFCI_lock.acquire()
			if RFC_id in RFC_inventory:
				resp = utils.create_resp_message(200,[(RFC_id,)+ tup for tup in RFC_inventory[RFC_id]])
			RFCI_lock.release()
	return resp

def list_RFC(rqst):
	rfc_list = []
	RFCI_lock.acquire()
	for rfc_id in  RFC_inventory:
		rfc_list += [(rfc_id,)+ tup for tup in RFC_inventory[rfc_id]]
	RFCI_lock.release()
	resp = utils.create_resp_message(200,rfc_list)
	return resp

def close_conn(rqst):
	host = rqst.split()[1]
	port = rqst.split()[2]
	AP_lock.acquire()
	del active_peers[host]
	AP_lock.release()
	
	RFCI_lock.acquire()
	for rfc in RFC_inventory:
		for tup in RFC_inventory[rfc]:
			if tup[1]==host and tup[2]==port:
				RFC_inventory[rfc].remove(tup)
	RFCI_lock.release()
	return ''

def process_message(rqst):
	msg_tokens = rqst.split()
	if msg_tokens[0]=='ADD':
		resp = add_RFC(rqst)
	elif msg_tokens[0]=='LOOKUP':
		resp = lookup_RFC(rqst)
	elif msg_tokens[0]=='LIST':
		resp = list_RFC(rqst)
	elif msg_tokens[0]=='CLOSE':
		resp = close_conn(rqst)
	else:
		resp = utils.create_resp_message(400,[])
	return resp

def spawn_peer_thread(soc, addr):
	#b = soc.send("welcome"+str(addr))
	#print str(b)+"bytes send
	register_peer(soc,addr)
	while(1):
		rqst = utils.recieve_data(soc)
		print rqst
		if(len(rqst)!=0):
			resp = process_message(rqst)
			if resp=='':
				break
			utils.send_data(soc,resp)

def accept_connections(lis_soc):
	while 1:
		peer_soc, peer_addr = lis_soc.accept()
		#print "Yo! someone connected"
		start_new_thread(spawn_peer_thread,(peer_soc,peer_addr))
def main():
	lis_soc = utils.init_listening_socket(SERV_HOST,SERV_PORT)
	accept_connections(lis_soc)

if __name__ == "__main__":
    main()