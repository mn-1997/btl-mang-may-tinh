# reverse_proxy.py
#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# AsynapRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#


"""
start_proxy
~~~~~~~~~~~~~~~~~
Entry point for starting the reverse proxy. It reads host mappings from a config file.
"""

import socket
import threading
import argparse
import re
from urllib.parse import urlparse
from collections import defaultdict

from daemon import create_proxy

PROXY_PORT = 8080


def parse_virtual_hosts(config_file):
    # Read the virtual host settings from a file


    with open(config_file, 'r') as f:
        config_text = f.read()

    # Match each host block
    host_blocks = re.findall(r'host\s+"([^"]+)"\s*\{(.*?)\}', config_text, re.DOTALL)

    dist_policy_map = ""

    routes = {}
    for host, block in host_blocks:
        proxy_map = {}

        # Find all proxy_pass entries
        proxy_passes = re.findall(r'proxy_pass\s+http://([^\s;]+);', block)
        map = proxy_map.get(host,[])
        map = map + proxy_passes
        proxy_map[host] = map

        # Find dist_policy if present
        policy_match = re.search(r'dist_policy\s+(\w+)', block)
        if policy_match:
            dist_policy_map = policy_match.group(1)
        else: #default policy is round_robin
            dist_policy_map = 'round-robin'
            
        # Build the mapping based on number of backends found
        if len(proxy_map.get(host,[])) == 1:
            routes[host] = (proxy_map.get(host,[])[0], dist_policy_map)
        else:
            routes[host] = (proxy_map.get(host,[]), dist_policy_map)

    for key, value in routes.items():
        print(key, value)
    return routes


if __name__ == "__main__":
    # Start the proxy server


    parser = argparse.ArgumentParser(prog='Proxy', description='', epilog='Proxy daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PROXY_PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    routes = parse_virtual_hosts("config/proxy.conf")

    create_proxy(ip, port, routes)
