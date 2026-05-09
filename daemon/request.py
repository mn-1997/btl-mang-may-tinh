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

This module provides a Request object to manage and persist
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict
import json


class Request():
    """Parses a raw HTTP request string into structured parts.

    After calling `prepare(raw_string)`, you can access:
      - self.method  : "GET", "POST", etc.
      - self.path    : "/login", "/get-list", etc.
      - self.headers : CaseInsensitiveDict of all headers
      - self.body    : the raw body string (everything after the blank line)
      - self.hook    : the matched route handler function (or None)

    Usage::

      >>> req = Request()
      >>> req.prepare(raw_http_string, routes)
      >>> req.method
      'POST'
      >>> req.get_json()
      {'username': 'alice', 'password': '123'}
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
        #: HTTP method (GET, POST, PUT, DELETE, etc.)
        self.method = None
        #: HTTP URL path (e.g. "/login")
        self.url = None
        #: Parsed headers as a case-insensitive dictionary
        self.headers = CaseInsensitiveDict()
        #: URL path (same as url, kept for compatibility)
        self.path = None
        #: Parsed cookies from the Cookie header
        self.cookies = {}
        #: Request body as a raw string
        self.body = ""
        #: Raw header section before parsing
        self._raw_headers = ""
        #: Raw body section before parsing
        self._raw_body = ""
        #: HTTP version string (e.g. "HTTP/1.1")
        self.version = None
        #: Registered routes dict
        self.routes = {}
        #: The matched handler function for this request's path
        self.hook = None

    def extract_request_line(self, request):
        """Pull the method, path, and version from the first line.

        Example first line: "GET /index.html HTTP/1.1"

        :param request (str): The full raw HTTP request string.
        :rtype: tuple of (method, path, version) or (None, None, None)
        """
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
        """Parse the header lines into a case-insensitive dictionary.

        Each header line looks like: "Content-Type: application/json"
        We split on the first ": " to get key and value.

        :param request (str): The raw HTTP request string.
        :rtype: CaseInsensitiveDict with all parsed headers.
        """
        headers = CaseInsensitiveDict()
        lines = request.split('\r\n')
        # Skip the first line (request line) and process the rest
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key] = val
        return headers

    def fetch_headers_body(self, request):
        """Split the request into header section and body section.

        HTTP requests have a blank line (\\r\\n\\r\\n) separating
        headers from the body.

        :param request (str): The full raw HTTP request string.
        :rtype: tuple of (header_string, body_string)
        """
        parts = request.split("\r\n\r\n", 1)
        _headers = parts[0]
        _body = parts[1] if len(parts) > 1 else ""
        return _headers, _body

    def prepare(self, request, routes=None):
        """Parse the entire raw HTTP request into structured fields.

        This is the main entry point. It:
        1. Extracts the request line (method, path, version)
        2. Splits headers from body
        3. Parses headers into a dictionary
        4. Looks up the matching route handler (hook)

        :param request (str): The full raw HTTP request string.
        :param routes (dict): Route registry {(METHOD, path): handler_func}.
        """

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

        # Step 5: Parse cookies from the Cookie header if present
        cookie_str = self.headers.get('cookie', '')
        if cookie_str:
            self.cookies = self._parse_cookies(cookie_str)

        # Step 6: Look up the matching route handler
        if routes and routes != {}:
            self.routes = routes
            self.hook = routes.get((self.method, self.path))
            print("[Request] Route lookup ({}, {}) -> {}".format(
                self.method, self.path, self.hook))

    def get_json(self):
        """Parse the request body as JSON and return a Python dict.

        This is the agreed-upon way for the app layer to read
        JSON data sent from the frontend.

        :rtype: dict or None if body is empty / invalid JSON.
        """
        if not self.body:
            return None
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:
            return None

    def get_bearer_token(self):
        """Extract the Bearer token from the Authorization header.

        Looks for: "Authorization: Bearer <token_string>"
        Returns just the token string, or None if not present.

        :rtype: str or None
        """
        auth_header = self.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            # Everything after "Bearer " is the token
            return auth_header[7:]
        return None

    def prepare_body(self, data, files, json_data=None):
        """Prepare the request body and set Content-Length.

        :param data: Raw body data.
        :param files: File attachments (not yet implemented).
        :param json_data: JSON payload to serialize.
        """
        if json_data is not None:
            self.body = json.dumps(json_data)
            self.headers['Content-Type'] = 'application/json'
        elif data:
            self.body = data
        self.prepare_content_length(self.body)

    def prepare_content_length(self, body):
        """Set the Content-Length header based on body size.

        :param body: The request body string.
        """
        if body:
            self.headers["Content-Length"] = str(len(body))
        else:
            self.headers["Content-Length"] = "0"

    def prepare_auth(self, auth, url=""):
        """Attach authentication credentials to the request.

        :param auth: Tuple of (username, password) or a token string.
        :param url: The target URL (unused for now).
        """
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
        """Set the Cookie header from a cookie string.

        :param cookies (str): Formatted cookie string like "key1=val1; key2=val2".
        """
        self.headers["Cookie"] = cookies

    def _parse_cookies(self, cookie_str):
        """Parse a raw Cookie header string into a dictionary.

        Example: "session=abc123; theme=dark" -> {"session": "abc123", "theme": "dark"}

        :param cookie_str (str): The raw cookie string.
        :rtype: dict
        """
        cookies = {}
        for pair in cookie_str.split(';'):
            pair = pair.strip()
            if '=' in pair:
                key, value = pair.split('=', 1)
                cookies[key.strip()] = value.strip()
        return cookies

