import json, requests, time, datetime

height_range = 5

def measureHealth(obj, his, max):
	score = his * 0.2
	if obj['status'] == 'online':
		if obj['height'] < (max - height_range):
			score += 200
		else:
			score += 400
		score += (3000 - obj['elapsed']) / 30 * 4
	return score

xmr_headers = {
	'content-type': 'application/json',
}

while True:
	# Open IP File 
	try:
		ipf = open('IP.in', 'r')
	except (OSError, IOError) as e:
		print('IP FILE open error\n' + e + '\n')
	xmr_nodes = json.loads(ipf.read())
	ipf.close()
	
	#Get Height From Node
	node_ary = []
	max_height = -1
	for node_ip in xmr_nodes:
		node_infos = {'IP': node_ip}
		try:
			start = datetime.datetime.now()
			resp = requests.post(url='http://'+node_ip+'/getheight', headers=xmr_headers, timeout = 2)
			node_infos['elapsed'] = (datetime.datetime.now() - start).microseconds/1000
			node_json = json.loads(resp.text)
			if node_json['status'] == 'OK':
				node_infos['height'] = node_json['height']
				node_infos['status'] = 'online'
				if node_json['height'] > max_height:
					max_height = node_json['height']
			else:
				node_infos['height'] = -1
				node_infos['status'] = 'offline'
		except requests.exceptions.RequestException as err:
			node_infos['elapsed'] = 3000
			node_infos['height'] = -1
			node_infos['status'] = 'offline'

		node_ary.append(node_infos);
		print(str(node_infos))

	#Open Score File
	try:
		scf = open('score.json', 'r')
		history = json.loads(scf.read())
		scf.close()
	except (OSError, IOError) as e:
		print('Histroy FILE open error\n')
		history = []

	for node_obj in node_ary:
		history_score = 500
		for his in history:
			if node_obj['IP'] == his['IP']:
				history_score = his['score']
				break
		node_obj['score'] = measureHealth(node_obj, history_score, max_height)

	#Sort
	node_ary.sort(reverse = True, key = lambda obj:obj['score'])
	#print(str(node_ary))
	scf = open('score.json', 'w')
	scf.write(json.dumps(node_ary))
	scf.close()


	print('Enter Sleep->')
	time.sleep(300)
	print('<-Leave Sleep')



