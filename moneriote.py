from functools import partial
from multiprocessing import Pool, freeze_support
from subprocess import Popen
from time import sleep

import json
import re
import requests
import subprocess
import random, pprint

monerodLocation = 'monerod.exe'  # This is the relative or full path to the monerod binary
moneroDaemonAddr = '10.1.1.61'  # The IP address that the rpc server is listening on
moneroDaemonPort = '18081'  # The port address that the rpc server is listening on
moneroDaemonAuth = 'not:used'  # The username:password that the rpc server requires (if set) - has to be something

maximumConcurrentScans = 16  # How many servers we should scan at once
acceptableBlockOffset = 3  # How much variance in the block height will be allowed
scanInterval = 5  # N Minutes
rpcPort = 18089  # This is the rpc server port that we'll check for

currentNodes = []

'''
    Gets the current top block on the chain
'''
def get_blockchain_height():
    process = Popen([
        monerodLocation,
        '--rpc-bind-ip', moneroDaemonAddr,
        '--rpc-bind-port', moneroDaemonPort,
        '--rpc-login', moneroDaemonAuth,
        'print_height'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True, bufsize=1)
    (output, err) = process.communicate()
    return int(re.sub('[^0-9]', '', output.splitlines()[0]))


'''
    Gets the last known peers from the server
'''
def load_nodes():
    nodes = []
    process = Popen([
        monerodLocation,
        '--rpc-bind-ip', moneroDaemonAddr,
        '--rpc-bind-port', moneroDaemonPort,
        '--rpc-login', moneroDaemonAuth,
        'print_pl'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True, bufsize=1)
    (output, err) = process.communicate()

    regex = r"(gray|white)\s+(\w+)\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})"
    matches = re.finditer(regex, output)


    for matchNum, match in enumerate(matches):
        if match.group(1) == 'white':
            address = match.group(3)

            if address not in currentNodes and address != '0.0.0.0':
                nodes.append(address)
    print('All peers from server: ' + str(len(nodes)) + ' nodes')
    return nodes


"""
    Scans the requested address to see if the RPC port is available and is within the accepted range
"""
def scan_node(accepted_height, address):

    try:
        req = requests.get('http://' + address + ':' + rpcPort.__str__() + '/getheight', timeout=1)
    except requests.exceptions.RequestException:
        return {'address': address, 'valid': False}

    try:
        node_height_json = json.loads(req.text)
    except:
        return {'address': address, 'valid': False}

    block_height_diff = int(node_height_json['height']) - accepted_height

    # Check if the node we're checking is up to date (with a little buffer)
    if acceptableBlockOffset >= block_height_diff >= (acceptableBlockOffset * -1):
        return {'address': address, 'valid': True}
    else:
        return {'address': address, 'valid': False}



"""
    Start threads checking known nodes to see if they're alive
"""
def start_scanning_threads(current_nodes, blockchain_height):

    print('Scanning accepted nodes...')

    pool = Pool(processes=maximumConcurrentScans)
    response = pool.map(partial(scan_node, blockchain_height), current_nodes)

    pool.close()
    pool.join()

    for node in response:
        if node['valid'] is True and node['address'] not in currentNodes:
            currentNodes.append(node['address'])

        if node['valid'] is False and node['address'] in currentNodes:
            currentNodes.remove(node['address'])
    
    print( 'After screening: ' + str(len(currentNodes)) + ' nodes')


    
"""
    Update our powerdns authorative records
"""
def check_all_nodes():

    # if currentNodes.__len__() > 0:
    #     print ('Checking existing nodes...')
    #     start_scanning_threads(currentNodes, get_blockchain_height())
    print ('Checking for new nodes...')
    start_scanning_threads(load_nodes(), get_blockchain_height())
    print ("We currently have {} 18089 nodes".format(currentNodes.__len__()))
    return currentNodes


if __name__ == '__main__':
    freeze_support()
    check_all_nodes()
