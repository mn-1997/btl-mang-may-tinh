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
deamon.asynaprous
~~~~~~~~~~~~~~~~~

This module provides a AsynapRous object to deploy RESTful url web app with routing
"""

from .backend import create_backend
from .auth import validate_token
from .response import Response
import asyncio
import inspect

class AsynapRous:
    """
    The main App object. Use @app.route to add endpoints and app.run() to start.
    """

    def __init__(self):
        # Setup the app with no routes yet

        self.routes = {}
        self.ip = None
        self.port = None
        return

    def prepare_address(self, ip, port):
        # Set the network IP and port

        self.ip = ip
        self.port = port

    def route(self, path, methods=['GET'], auth_required=False):
        # Decorator to link a URL path to a Python function

        def decorator(func):
            # We don't store wrapper here directly, we wrap it
            # so the wrapper executes when the route is invoked
            
            def sync_wrapper(headers, body):
               print("[AsynapRous] running sync function...  [{}] {}".format(methods, path))
               if auth_required:
                   auth_header = headers.get('authorization', '')
                   if auth_header.startswith('Bearer '):
                       token = auth_header[7:]
                       username = validate_token(token)
                       if username:
                           # Pass authenticated user to handler via custom header
                           headers['_authenticated_user'] = username
                       else:
                           return Response.build_unauthorized("Invalid or expired token")
                   else:
                       return Response.build_unauthorized("Missing Bearer token")
               
               result = func(headers, body)
               return result

            async def async_wrapper(headers, body):
               print("[AsynapRous] running Async function... [{}] {}".format(methods, path))
               if auth_required:
                   auth_header = headers.get('authorization', '')
                   if auth_header.startswith('Bearer '):
                       token = auth_header[7:]
                       username = validate_token(token)
                       if username:
                           headers['_authenticated_user'] = username
                       else:
                           return Response.build_unauthorized("Invalid or expired token")
                   else:
                       return Response.build_unauthorized("Missing Bearer token")

               result = await func(headers, body)
               return result

            # Wrap depending on if coroutine
            if inspect.iscoroutinefunction(func):
                wrapper = async_wrapper
            else:
                wrapper = sync_wrapper

            # Store the wrapped function in routes
            for method in methods:
                self.routes[(method.upper(), path)] = wrapper

            # Optional attach route metadata to the function
            func._route_path = path
            func._route_methods = methods

            return wrapper
        return decorator

    def run(self):
        # Launch the backend server

        if not self.ip or not self.port:
            print("Rous app need to preapre address"
                  "by calling app.prepare_address(ip,port)")

        create_backend(self.ip, self.port, self.routes)
        
