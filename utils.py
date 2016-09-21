import socket

LOGGING = 0
CONN_BACKLOG=50
HEADER_LEN = 10
VERSION = 'P2P-CI/1.0'
STATUS = {404:'NOT FOUND',200:'OK',400:'BAD REQUEST'}
def init_listening_socket(host,port):
	#create TCP socket
	try:
		lis_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error, error_msg:
		print "Socket creation failed. "+str(error_msg[0])+": "+error_msg[1]
		sys.exit()

	if LOGGING:
		print "Listening socket created"
	#Bind socket to all itnerface on known port 
	try:
		lis_soc.bind((host,port))
	except socket.error, error_msg:
		print "Binding failed. "+str(error_msg[0])+": "+error_msg[1]
		sys.exit()
	if LOGGING:
		print "Socket binding successful"
	#listen for peers
	lis_soc.listen(CONN_BACKLOG)
	if LOGGING:
		print "Socket is now listening..."

	return lis_soc
def create_rqst_message(method,rfc_id,headers):
	if method=='LIST':
		msg = method+' '+'ALL'+' '+VERSION+'\n'
	else:
		msg = method+' RFC '+str(rfc_id)+' '+VERSION+'\n'
	for header in headers:
		msg = msg+header+':'+' '+headers[header]+'\n'
	return msg
def create_resp_message(status,headers):
	msg = VERSION+' '+str(status)+' '+STATUS[status]+'\n\n'
	for tup in headers:
		msg += 'RFC'+' '+tup[0]+' '+tup[1]+' '+tup[2]+' '+tup[3]+'\n'
	return msg

def send_data(soc,data):
	if LOGGING:
		print "sending msg..."
		print data
	data_str = str(data)
	header = str(len(data_str)).ljust(HEADER_LEN)
	msg_len = HEADER_LEN + len(data_str)
	while msg_len>0:
		send_len = soc.send(header+data_str)
		msg_len = msg_len - send_len
	#if LOGGING:
	#	print ">>>>>>>> ",len(data)," size data send"
def recieve_data(soc):
	header = soc.recv(HEADER_LEN)
	data = ''
	if len(header)!=0:
		data_len = int(header)
		data = soc.recv(data_len)
	#if LOGGING:
	#	print "<<<<<<<<< ",len(data)," size data recieved"
	return data