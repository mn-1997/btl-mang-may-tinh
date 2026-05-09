#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# AsynapRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.proxy
~~~~~~~~~~~~~~~~~

This module implements a simple proxy server using Python's socket and threading libraries.
It routes incoming HTTP requests to backend services based on hostname mappings and returns
the corresponding responses to clients.

Requirement:
-----------------
- socket: provides socket networking interface.
- threading: enables concurrent client handling via threads.
- response: customized :class: `Response <Response>` utilities.
- httpadapter: :class: `HttpAdapter <HttpAdapter >` adapter for HTTP request processing.
- dictionary: :class: `CaseInsensitiveDict <CaseInsensitiveDict>` for managing headers and cookies.

"""
import socket
import threading
import asyncio
from .response import *
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict

#: A dictionary mapping hostnames to backend IP and port tuples.
#: Used to determine routing targets for incoming requests.
PROXY_PASS = {
    "192.168.56.103:8080": ('192.168.56.103', 9000),
    "app1.local": ('192.168.56.103', 9001),
    "app2.local": ('192.168.56.103', 9002),
}


async def forward_request(host, port, request_bytes):
    """
    Forwards an HTTP request to a backend server asynchronously and retrieves the response.

    :params host (str): IP address of the backend server.
    :params port (int): port number of the backend server.
    :params request_bytes (bytes): incoming HTTP request.

    :rtype bytes: Raw HTTP response from the backend server. If the connection
                  fails, returns a 502 Bad Gateway response.
    """
    try:
        reader, writer = await asyncio.open_connection(host, port)
        writer.write(request_bytes)
        await writer.drain()

        response = b""
        while True:
            chunk = await reader.read(4096)
            if not chunk:
                break
            response += chunk
            
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return response
        
    except Exception as e:
        print("Proxy forward error: {}".format(e))
        return (
            "HTTP/1.1 502 Bad Gateway\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 15\r\n"
            "Connection: close\r\n"
            "\r\n"
            "502 Bad Gateway"
        ).encode('utf-8')


def resolve_routing_policy(hostname, routes):
    """
    Handles an routing policy to return the matching proxy_pass.
    It determines the target backend to forward the request to.

    :params host (str): IP address of the request target server.
    :params port (int): port number of the request target server.
    :params routes (dict): dictionary mapping hostnames and location.
    """

    print(hostname)
    proxy_map, policy = routes.get(hostname,('127.0.0.1:9000','round-robin'))
    print(proxy_map)
    print(policy)

    proxy_host = ''
    proxy_port = '9000'
    if isinstance(proxy_map, list):
        if len(proxy_map) == 0:
            print("[Proxy] Emtpy resolved routing of hostname {}".format(hostname))
            print("Empty proxy_map result")
            # TODO: implement the error handling for non mapped host
            #       the policy is design by team, but it can be 
            #       basic default host in your self-defined system
            # Use a dummy host to raise an invalid connection
            proxy_host = '127.0.0.1'
            proxy_port = '9000'
        elif len(proxy_map) == 1:
            proxy_host, proxy_port = proxy_map[0].split(":", 2)
        #elif: # apply the policy handling 
        #   proxy_map
        #   policy
        else:
            # Out-of-handle mapped host
            proxy_host = '127.0.0.1'
            proxy_port = '9000'
    else:
        print("[Proxy] resolve route of hostname {} is a singulair to".format(hostname))
        proxy_host, proxy_port = proxy_map.split(":", 2)

    return proxy_host, proxy_port

async def handle_client_coroutine(reader, writer, routes):
    """
    Handles an individual client connection asynchronously by parsing the request,
    determining the target backend, and forwarding the request.

    :params reader (StreamReader): async reader.
    :params writer (StreamWriter): async writer.
    :params routes (dict): dictionary mapping hostnames and location.
    """
    addr = writer.get_extra_info("peername")

    request_bytes = await reader.read(4096)
    if not request_bytes:
        writer.close()
        return

    request_str = request_bytes.decode('utf-8', errors='ignore')

    hostname = ""
    # Extract hostname
    for line in request_str.splitlines():
        if line.lower().startswith('host:'):
            hostname = line.split(':', 1)[1].strip()
            break

    print("[Proxy] {} at Host: {}".format(addr, hostname))

    # Resolve the matching destination in routes and need conver port
    # to integer value
    resolved_host, resolved_port = resolve_routing_policy(hostname, routes)
    try:
        resolved_port = int(resolved_port)
    except ValueError:
        print("Not a valid integer")
        resolved_host = None

    if resolved_host:
        print("[Proxy] Host name {} is forwarded to {}:{}".format(hostname, resolved_host, resolved_port))
        response = await forward_request(resolved_host, resolved_port, request_bytes)        
    else:
        response = (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode('utf-8')
        
    writer.write(response)
    await writer.drain()
    writer.close()


async def async_proxy_server(ip, port, routes):
    print("[Proxy] **ASYNC** Listening on IP {} port {}".format(ip,port))
    
    async def client_handler(reader, writer):
        await handle_client_coroutine(reader, writer, routes)
        
    server = await asyncio.start_server(client_handler, ip, port)
    async with server:
        await server.serve_forever()


def run_proxy(ip, port, routes):
    """
    Starts the proxy server and listens for incoming connections. 
    Uses asyncio event loop.
    """
    asyncio.run(async_proxy_server(ip, port, routes))


def create_proxy(ip, port, routes):
    """
    Entry point for launching the proxy server.

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.
    """
    run_proxy(ip, port, routes)
