import json, requests, time, datetime

height_range = 5
threshold = 850

xmr_headers = {
	'content-type': 'application/json',
}

url_cf = 'https://api.cloudflare.com/client/v4/zones/e1787b6bb10e8d5fa8fb7705e181a0ce/dns_records/'
name_cf = 'node.xmr-tw.org'
headers_cf = {
	'X-Auth-Email': 'chunhsi.tso@gmail.com',
	'Content-Type': 'application/json',
	'X-Auth-Key': '---'
}

#calculate health
def measureHealth(obj, his, max):
	score = his * 0.75
	if obj['status'] == 'online':
		if obj['height'] < (max - height_range):
			score += 50
		else:
			score += 150
		score += (3000 - obj['elapsed']) / 30
	return score
def cutPort(str):
	i = str.find(':')
	return str[:i]

while True:
	# Open IP File 
	try:
		ipf = open('IP.in', 'r')
		xmr_nodes = json.loads(ipf.read())
		ipf.close()
	except (OSError, IOError) as e:
		print('IP FILE open error\n' + e + '\n')
	
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

	#Get DNS List From Cloudflare
	try:
		res_cf = requests.get(url = url_cf, json = {'name': name_cf, 'per_page': 100}, headers = headers_cf)
		json_cf = json.loads(res_cf.text)
		if json_cf['success'] == True:
			print('Success When Get DNS List')
			#Create DNS Record
			for node_obj in node_ary:
				if node_obj['score'] >= threshold and node_obj['status'] == 'online':
					flag_exist = False
					for list_obj in json_cf['result']:
						if list_obj['name'] == name_cf and list_obj['content'] == cutPort(node_obj['IP']):
							flag_exist = True
							break
					if flag_exist:
						print(node_obj['IP'] + ' already exist')
					else:
						try:
							res_create = requests.post(url = url_cf, json = {'name': name_cf, 'type': 'A', 'content': cutPort(node_obj['IP'])}, headers = headers_cf)
							json_create = json.loads(res_create.text)
							if json_create['success'] == True:
								print(node_obj['IP'] + ' create record success')
							else:
								print(node_obj['IP'] + ' create record fail')
								print(res_create.text)
						except requests.exceptions.RequestException as err:
							print(str(err))
			#Delete DNS Record
			for list_obj in json_cf['result']:
				if list_obj['name'] == name_cf:
					flag_exist = False
					for node_obj in node_ary:
						if cutPort(node_obj['IP']) == list_obj['content'] and node_obj['score'] >= threshold and node_obj['status'] == 'online':
							flag_exist = True
							break
					if not flag_exist:
						try:
							res_del = requests.delete(url = url_cf+list_obj['id'], headers = headers_cf)
							json_del = json.loads(res_del.text)
							if json_del['success'] == True:
								print(list_obj['content'] + ' delete record success')
							else:
								print(list_obj['content'] + ' delete record fail')
								print(res_del.text)
						except requests.exceptions.RequestException as err:
							print(str(err))
		else:			
			print('Error When Get DNS List')
	except requests.exceptions.RequestException as err:
		print(str(err))

	print('Enter Sleep->')
	time.sleep(300)
	print('<-Leave Sleep')



