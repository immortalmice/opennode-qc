import json, requests, time, datetime

xmr_headers = {
	'content-type': 'application/json',
}

while 1:
	# Open File 
	try:
		ipf = open('IP.in', 'r')
	except (OSError, IOError) as e:
		print('FILE open error\n' + e + '\n')
	xmr_nodes = json.loads(ipf.read())
	
	#Get Height From Node
	node_ary = []
	for node_ip in xmr_nodes:
		node_infos = {'IP': node_ip}
		try:
			start = datetime.datetime.now()
			resp = requests.post(url='http://'+node_ip+'/getheight', headers=xmr_headers, timeout = 3)
			node_infos['elapsed'] = (datetime.datetime.now() - start).microseconds/1000
			node_json = json.loads(resp.text)
			if node_json['status'] == 'OK':
				node_infos['height'] = node_json['height']
				node_infos['status'] = 'online'
			else:
				node_infos['height'] = -1
				node_infos['status'] = 'offline'
		except requests.exceptions.RequestException as err:
			node_infos['elapsed'] = 3000
			node_infos['height'] = -1
			node_infos['status'] = 'offline'

		node_ary.append(node_infos);
		print(str(node_infos))

	print('Enter Sleep->')
	time.sleep(300)
	print('<-Leave Sleep')



