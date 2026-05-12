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
daemon.httpadapter
~~~~~~~~~~~~~~~~~
Handles translating raw TCP bytes into Request and Response objects.
"""

from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict

import asyncio
import inspect

class HttpAdapter:
    """
    Manages client connections and maps them to the right functions.
    """

    __attrs__ = [
        "ip",
        "port",
        "conn",
        "connaddr",
        "routes",
        "request",
        "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        # Save connection details and routes


        #: IP address.
        self.ip = ip
        #: Port.
        self.port = port
        #: Connection
        self.conn = conn
        #: Conndection address
        self.connaddr = connaddr
        #: Routes
        self.routes = routes
        #: Request
        self.request = Request()
        #: Response
        self.response = Response()

    def handle_client(self, conn, addr, routes):
        # Handle a standard blocking connection (legacy mode)


        # Connection handler.
        self.conn = conn        
        # Connection address.
        self.connaddr = addr
        # Request handler
        req = self.request
        # Response handler
        resp = self.response

        # Handle the request
        msg = conn.recv(4096).decode("utf-8")
        req.prepare(msg, routes)
        print("[HttpAdapter] Invoke handle_client connection {}".format(addr))

        # Handle request hook
        if req.hook:
            # Handle for App hook here
            try:
                # Sync wrapper will be called
                result = req.hook(req.headers, req.body)
                response = resp.build_response(req) # Fallback if not returning properly
                if isinstance(result, bytes):
                    # We assume it is a raw response if bytes
                    response = result
            except Exception as e:
                response = Response.build_json_error(500, str(e))
        else:
            # Default file serving behavior if no hook
            response = resp.build_response(req)

        #print("[HttpAdapter] Response content {}".format(response))
        conn.sendall(response)
        conn.close()

    async def handle_client_coroutine(self, reader, writer):
        # Main handler for asynchronous connections

        # Request handler
        req = self.request
        # Response handler
        resp = self.response

        addr = writer.get_extra_info("peername")
        print("[HttpAdapter] Invoke handle_client_coroutine connection {}".format(addr))

        # Handle the request asynchronously
        # Read until we have the headers (separated by \r\n\r\n)
        msg_bytes = await reader.read(4096)
        if not msg_bytes:
            writer.close()
            return
            
        msg = msg_bytes.decode("utf-8", errors="ignore")
        
        # Parse initial request
        req.prepare(msg, self.routes)
        
        # Check if we need to read more for the body
        content_length = int(req.headers.get("Content-Length", 0))
        current_body_len = len(req.body.encode("utf-8"))
        
        while current_body_len < content_length:
            chunk = await reader.read(4096)
            if not chunk:
                break
            chunk_str = chunk.decode("utf-8", errors="ignore")
            req.body += chunk_str
            current_body_len += len(chunk)

        # Handle request hook
        response = b""
        if req.hook:
            try:
                # Dispatch to handler function
                if inspect.iscoroutinefunction(req.hook):
                    result = await req.hook(req.headers, req.body)
                else:
                    result = req.hook(req.headers, req.body)
                    
                if isinstance(result, bytes):
                    # The route handler returned a complete HTTP response (e.g. from build_json_ok)
                    response = result
                else:
                    # Fallback wrapper if just returning dict
                    response = Response.build_json_ok(result)
            except Exception as e:
                print(f"[HttpAdapter] Error in hook: {e}")
                response = Response.build_json_error(500, str(e))
        else:
            if req.method == 'OPTIONS':
                 response = Response.build_cors_preflight()
            else:
                 # Default file serving behavior
                 response = resp.build_response(req)

        # Send all the response asynchronously
        writer.write(response)
        await writer.drain()
        writer.close()


    # @property
    # def extract_cookies(self, req, resp):
    #     # Parse cookies from headers
    #
    #     cookies = {}
    #     for header in req.headers:
    #         if header.startswith("Cookie:"):
    #             cookie_str = header.split(":", 1)[1].strip()
    #             for pair in cookie_str.split(";"):
    #                 key, value = pair.strip().split("=")
    #                 cookies[key] = value
    #     return cookies

    def build_response(self, req, resp):
        # Create a Response object from request info

        response = Response()

        # Set encoding.
        response.encoding = get_encoding_from_headers(response.headers)
        response.raw = resp
        response.reason = response.raw.reason

        if isinstance(req.url, bytes):
            response.url = req.url.decode("utf-8")
        else:
            response.url = req.url

        # Add new cookies from the server.
        # response.cookies = extract_cookies(req)

        # Give the Response some context.
        response.request = req
        response.connection = self

        return response

    def build_json_response(self, req, resp):
        # Create a JSON response

        response = Response(req)

        # Set encoding.
        response.raw = resp

        if isinstance(req.url, bytes):
            response.url = req.url.decode("utf-8")
        else:
            response.url = req.url

        # Give the Response some context.
        response.request = req
        response.connection = self

        return response


    # def get_connection(self, url, proxies=None):
        # """Returns a url connection for the given URL. 

        # :param url: The URL to connect to.
        # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
        # :rtype: int
        # """

        # proxy = select_proxy(url, proxies)

        # if proxy:
            # proxy = prepend_scheme_if_needed(proxy, "http")
            # proxy_url = parse_url(proxy)
            # if not proxy_url.host:
                # raise InvalidProxyURL(
                    # "Please check proxy URL. It is malformed "
                    # "and could be missing the host."
                # )
            # proxy_manager = self.proxy_manager_for(proxy)
            # conn = proxy_manager.connection_from_url(url)
        # else:
            # # Only scheme should be lower case
            # parsed = urlparse(url)
            # url = parsed.geturl()
            # conn = self.poolmanager.connection_from_url(url)

        # return conn


    def add_headers(self, request):
        # Hook for subclasses to add extra headers

        pass

    def build_proxy_headers(self, proxy):
        # Add auth headers for proxy requests

        headers = {}
        #
        # TODO: build your authentication here
        #       username, password =...
        # we provide dummy auth here
        #
        username, password = ("user1", "password")

        if username:
            headers["Proxy-Authorization"] = (username, password)

        return headers