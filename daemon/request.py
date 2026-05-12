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
daemon.request
~~~~~~~~~~~~~~~~~
Handles parsing raw HTTP request strings into usable Python objects.
"""
from .dictionary import CaseInsensitiveDict
import json


class Request():
    """
    Parses a raw HTTP request string into structured fields (method, path, headers, body).
    """

    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "_raw_headers",
        "_raw_body",
        "reason",
        "cookies",
        "routes",
        "hook",
    ]

    def __init__(self):
        self.method = None
        self.url = None
        self.headers = CaseInsensitiveDict()
        self.path = None
        self.cookies = {}
        self.body = ""
        self._raw_headers = ""
        self._raw_body = ""
        self.version = None
        self.routes = {}
        self.hook = None

    def extract_request_line(self, request):
        # Get the method, path, and version from the first line

        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()

            # Default "/" to serve the index page
            if path == '/':
                path = '/index.html'
        except Exception:
            return None, None, None

        return method, path, version

    def prepare_headers(self, request):
        # Parse the header lines into a dictionary

        headers = CaseInsensitiveDict()
        lines = request.split('\r\n')
        # Skip the first line (request line) and process the rest
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key] = val
        return headers

    def fetch_headers_body(self, request):
        # Separate headers from the body

        parts = request.split("\r\n\r\n", 1)
        _headers = parts[0]
        _body = parts[1] if len(parts) > 1 else ""
        return _headers, _body

    def prepare(self, request, routes=None):
        # Parse the entire raw HTTP request


        # Step 1: Parse the first line (e.g. "POST /login HTTP/1.1")
        self.method, self.path, self.version = self.extract_request_line(request)
        print("[Request] {} {} {}".format(self.method, self.path, self.version))

        # Step 2: Split the raw text into headers and body
        self._raw_headers, self._raw_body = self.fetch_headers_body(request)

        # Step 3: Parse headers into a dictionary
        #         MUST happen before any self.headers.get() call
        self.headers = self.prepare_headers(request)

        # Step 4: Store the body for later use by handlers
        self.body = self._raw_body

        # Step 5: (Optional) Parse cookies
        # cookie_str = self.headers.get('cookie', '')
        # if cookie_str:
        #     self.cookies = self._parse_cookies(cookie_str)

        # Step 6: Look up the matching route handler
        if routes and routes != {}:
            self.routes = routes
            self.hook = routes.get((self.method, self.path))
            print("[Request] Route lookup ({}, {}) -> {}".format(
                self.method, self.path, self.hook))

    def get_json(self):
        # Parse body as JSON

        if not self.body:
            return None
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:
            return None

    def get_bearer_token(self):
        # Extract Bearer token from headers

        auth_header = self.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            # Everything after "Bearer " is the token
            return auth_header[7:]
        return None

    def prepare_body(self, data, files, json_data=None):
        # Prepare request body and content length

        if json_data is not None:
            self.body = json.dumps(json_data)
            self.headers['Content-Type'] = 'application/json'
        elif data:
            self.body = data
        self.prepare_content_length(self.body)

    def prepare_content_length(self, body):
        # Calculate body size for header

        if body:
            self.headers["Content-Length"] = str(len(body))
        else:
            self.headers["Content-Length"] = "0"

    def prepare_auth(self, auth, url=""):
        # Add authentication info

        if isinstance(auth, tuple) and len(auth) == 2:
            # Basic auth — not used in this project but kept for compat
            username, password = auth
            import base64
            credentials = base64.b64encode(
                "{}:{}".format(username, password).encode()
            ).decode()
            self.headers["Authorization"] = "Basic {}".format(credentials)
        elif isinstance(auth, str):
            # Bearer token
            self.headers["Authorization"] = "Bearer {}".format(auth)

    def prepare_cookies(self, cookies):
        # Set cookie header

        self.headers["Cookie"] = cookies

    def _parse_cookies(self, cookie_str):
        # Parse cookie string into dict

        cookies = {}
        for pair in cookie_str.split(';'):
            pair = pair.strip()
            if '=' in pair:
                key, value = pair.split('=', 1)
                cookies[key.strip()] = value.strip()
        return cookies

