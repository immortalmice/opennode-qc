import json, requests, time

xmr_headers = {
	'content-type': 'application/json',
}

while 1:
	try:
		ipf = open('IP.in', 'r')
	except (OSError, IOError) as e:
		print('FILE open error\n' + e + '\n')
	xmr_nodes = json.loads(ipf.read())
	
	for node_ip in xmr_nodes:
		try:
		    resp = requests.post(url='http://'+node_ip+'/getheight', headers=xmr_headers, timeout = 3)
		    node_json = json.loads(resp.text)
		    if node_json['status'] == 'OK':
		        result = resp.text
		    else:
		        result = 'status error.'
		    
		except requests.exceptions.RequestException as err:
		    result = str(err)

		print(node_ip + '\n' + result + '\n')

	print('Enter Sleep->')
	time.sleep(300)
	print('<-Leave Sleep')



