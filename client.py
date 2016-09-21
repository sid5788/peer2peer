import sys
import socket
import os
import utils
import platform
from time import gmtime, strftime
import time
from thread import *

SERVER_PORT = 7734
LOGGING = 1

def spawn_serve_peers(lis_soc,):
	while 1:
		peer_soc, peer_addr = lis_soc.accept()
		#print "my peer conected to me ",peer_soc,peer_addr
		msg = utils.VERSION+' '+str(200)+' '+'OK'+'\n\n'
		rqst = utils.recieve_data(peer_soc)
		msg += 'Date: '+ strftime("%Y-%m-%d %H:%M:%S", gmtime()) + ' GMT\n'
		msg += 'OS: '+ platform.system()+'\n'
		if rqst.split()[0]!='GET':
			resp = utils.create_resp_message(400,header)
		else:
			msg_tokens = rqst.split('\n')
			rfc_id = msg_tokens[0].split()[2].strip()
			filePath = './rfc/rfc'+rfc_id+'.txt'
			file = open(filePath,'r')
			file_str = file.read()
			msg += 'Last-Modified: '+ time.ctime(os.path.getmtime(filePath))+'\n'
			msg += 'Content-Length: '+str(len(file_str))+'\n'
			msg += 'Content-Type: '+'text/text'+'\n'
		utils.send_data(peer_soc,msg+file_str)

def connect_to_server(server_hostname,server_port):
	#create socket
	try:
		serv_soc =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error, error_msg:
		print "Socket creation failed. "+str(error_msg[0])+": "+error_msg[1]
		sys.exit()
	if LOGGING:
		print "Server socket created"

	#get host ip
	try:
		remote_host_ip = socket.gethostbyname(server_hostname)
	except socket.gaierror:
		print "Host name"+server_hostname+" can not be resolved"
		sys.exit()
	#connect to server
	serv_soc.connect((remote_host_ip,server_port))
	return serv_soc
	#msg = serv_soc.recv(100)
	#print "recvd msg: ",msg

#SEND P2P add message
def register_with_server(soc,my_listening_port):
	rfc_list = os.listdir('./rfc')
	header_dic = {}
	header_dic['Host']=socket.gethostname()
	header_dic['Port']=str(my_listening_port)
	for rfc in rfc_list:
		full_path  =os.path.join('./rfc', rfc)
		file = open(full_path,'r')
		file_str = file.read()
		file_lines = file_str.split('\n')
		rfc_title = file_lines[4].strip()
		rfc_id = file_str[file_str.find('Request for Comments:')+len("Request for Comments:"):].split()[0].strip()
		header_dic['Title'] = rfc_title
		msg = utils.create_rqst_message('ADD',rfc_id,header_dic)
		utils.send_data(soc,msg)
		data = utils.recieve_data(soc)
		print data

	#utils.send_data(soc,str(my_listening_port))
	#print "i have send port =",my_listening_port
def print_response(resp):
	print resp
def get_user_action(serv_soc,my_listening_port):
	while 1:
		cmd = raw_input('Cmd options: \n1. LOOKUP <RFC Id> <Title>\n'+\
			'2. LIST\n3. GET <RFCC Id> <host> <port>\n'+'4. CLOSE\n')
		cmd_token = cmd.split()
		header_dic = {}
		header_dic['Host']=socket.gethostname()
		header_dic['Port']=str(my_listening_port)
		
		if cmd_token[0]=='CLOSE':
			rqst = 'CLOSE '+header_dic['Host']+' '+str(my_listening_port)
			utils.send_data(serv_soc,rqst)
			exit()

		elif cmd_token[0]=='LOOKUP':
			rfc_id = cmd_token[1]
			header_dic['Title'] = ' '.join(cmd_token[2:])
			rqst = utils.create_rqst_message('LOOKUP',rfc_id,header_dic)
			soc  = serv_soc

		elif cmd_token[0]=='LIST':
			rqst = utils.create_rqst_message('LIST','ALL',{})
			soc  = serv_soc

		elif cmd_token[0]=='GET':
			rfc_id = cmd_token[1]
			host = cmd_token[2]
			port = cmd_token[3]
			del header_dic['Port']
			header_dic['OS'] = platform.system()
			rqst = utils.create_rqst_message('GET',rfc_id,header_dic)
			peer_soc = connect_to_server(host,int(port))
			soc = peer_soc
		else:
			print 'Bad Command...\n'
			continue

		utils.send_data(soc,rqst)
		resp = utils.recieve_data(soc)
		print_response(resp)
		if cmd_token[0]=='GET':
			file_cont = ''.join(resp.split('\n')[6:])
			f = open('./recieved/'+str(rfc_id)+'.txt','w')
			f.write(file_cont)
			f.close()

def main():
	if len(sys.argv) != 2:
		print "Usage: client.py <Server_Name>"
		sys.exit()
	#open a  aport for listening to other peers
	lis_soc = utils.init_listening_socket('',0)
	#start a new thread to accept rqsts form peers
	start_new_thread(spawn_serve_peers,(lis_soc,))
	
	server_hostname = sys.argv[1]
	my_listening_port = lis_soc.getsockname()[1]
	serv_soc = connect_to_server(server_hostname,SERVER_PORT)
	register_with_server(serv_soc,my_listening_port)
	get_user_action(serv_soc,my_listening_port)

if __name__ == "__main__":
    main()