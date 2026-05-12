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
daemon.backend
~~~~~~~~~~~~~~~~~
Main engine for the server. It manages network connections and 
routes them to the right app logic.
"""

import socket
import threading
import argparse

import asyncio
import inspect

from .response import *
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict

import selectors
sel = selectors.DefaultSelector()

mode_async = "coroutine"
#mode_async = "callback"
#mode_async = "threading"

def handle_client(ip, port, conn, addr, routes):
    # Helper to handle individual clients

    print("[Backend] Invoke handle_client accepted connection from {}".format(addr))
    daemon = HttpAdapter(ip, port, conn, addr, routes)

    # Handle client
    daemon.handle_client(conn, addr, routes)


# Callback for handling new client (itself run in sync mode)
def handle_client_callback(server, ip, port,conn, addr, routes):
    # Helper for the callback-based mode (Legacy)

    print("[Backend] Invoke handle_client_callback accepted connection from {}".format(addr))

    daemon = HttpAdapter(ip, port, conn, addr, routes)

    # Handle client
    daemon.handle_client(conn, addr, routes)


async def async_server(ip="0.0.0.0", port=7000, routes={}):
    # Starts the asynchronous server using asyncio

    print("[Backend] async_server **ASYNC** listening on port {}".format(port))
    if routes != {}:
        print("[Backend] route settings")
        for key, value in routes.items():
            isCoFunc = ""
            if inspect.iscoroutinefunction(value):
               isCoFunc += "**ASYNC** "
            print("   + ('{}', '{}'): {}{}".format(key[0], key[1], isCoFunc, str(value)))

    async def client_handler(reader, writer):
        # Handler for each new connection

        addr = writer.get_extra_info("peername")
        print("[Backend] Invoke handle_client_coroutine accepted connection from {}".format(addr))
        
        # We pass None for conn since we use reader/writer in coroutine mode
        daemon = HttpAdapter(ip, port, None, addr, routes)
        await daemon.handle_client_coroutine(reader, writer)

    server = await asyncio.start_server(client_handler, ip, port)
    async with server:
        await server.serve_forever()
    return


def run_backend(ip, port, routes):
    # Binds to the port and starts listening for connections

    # This global variable to configure the asynchrnous mode or not
    global mode_async

    print("[Backend] run_backend with routes={}".format(routes))
    # Process async stream for registering the service and terminate
    if mode_async == "coroutine":

       asyncio.run(async_server(ip, port, routes))
       return

    # Process socket object
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((ip, port))
        server.listen(50)

        print("[Backend] Listening on port {}".format(port))
        if routes != {}:
            print("[Backend] route settings")
            for key, value in routes.items():
               isCoFunc = ""
               if inspect.iscoroutinefunction(value):
                  isCoFunc += "**ASYNC** "
               print("   + ('{}', '{}'): {}{}".format(key[0], key[1], isCoFunc, str(value)))

        if mode_async == "callback":
            sel.register(server, selectors.EVENT_READ, (handle_client_callback, ip, port, routes))

        while True:
            # Accept connection
            conn, addr = server.accept()

            # Choose between callback or threading modes
            if mode_async == "callback":
               # Callback implementation - Event driven architecture
               server.setblocking(False)

               events = sel.select(timeout=None)
               for key, mask in events:
                   callback, ip, port, routes = key.data
                   callback(key.fileobj, ip, port, conn, addr, routes)

            else:
               # Baseline multi-thread implementation
               #client_thread = threading.Thread...
               pass


    except socket.error as e:
      print("Socket error: {}".format(e))

def create_backend(ip, port, routes={}):
    # Entry point to start the whole backend


    run_backend(ip, port, routes)