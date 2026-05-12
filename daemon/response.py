#
# Copyright (C) 2026 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# AsynApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.response
~~~~~~~~~~~~~~~~~
Builds HTTP responses to send back to clients.
"""
import datetime
import json
import os
import mimetypes
from .dictionary import CaseInsensitiveDict

# Root directory for resolving static file paths
BASE_DIR = ""

# ------------------------------------------------------------------
#  CORS (Cross-Origin Resource Sharing) default headers
#  These allow the frontend (possibly on a different port) to
#  call our API without the browser blocking the request.
# ------------------------------------------------------------------
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}


class Response():
    """
    Builds and sends HTTP responses (both files and JSON).
    """

    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookies",
        "elapsed",
        "request",
        "body",
    ]

    def __init__(self, request=None):
        """Create a new empty Response.

        :param request: The originating Request object (optional).
        """
        self._content = b""
        self._content_consumed = False
        self._header = b""
        self._next = None

        self.status_code = None
        self.headers = {}
        self.url = None
        self.encoding = None
        self.history = []
        self.reason = None
        # self.cookies = CaseInsensitiveDict()
        self.elapsed = datetime.timedelta(0)
        self.request = request


    @staticmethod
    def build_json_ok(data):
        # Success response (200 OK)

        body = json.dumps(data)
        return Response._build_json_response(200, "OK", body)

    @staticmethod
    def build_json_error(status_code, message):
        # Error response (400, 404, etc.)

        body = json.dumps({"error": message})
        # Map common codes to their standard reason phrases
        reasons = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error",
        }
        reason = reasons.get(status_code, "Error")
        return Response._build_json_response(status_code, reason, body)

    @staticmethod
    def build_unauthorized(message="Authentication required"):
        # 401 Unauthorized response

        body = json.dumps({"error": message})
        extra_headers = {
            "WWW-Authenticate": 'Bearer realm="asynaprous"',
        }
        return Response._build_json_response(
            401, "Unauthorized", body, extra_headers)

    @staticmethod
    def build_cors_preflight():
        # CORS OPTIONS response

        return Response._build_json_response(204, "No Content", "")

    @staticmethod
    def _build_json_response(status_code, reason, body, extra_headers=None):
        # Internal helper to assemble the HTTP response string

        # Start with the status line
        status_line = "HTTP/1.1 {} {}".format(status_code, reason)

        # Build the headers dict
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(body.encode("utf-8"))),
            "Date": datetime.datetime.utcnow().strftime(
                "%a, %d %b %Y %H:%M:%S GMT"),
            "Connection": "close",
        }

        # Add CORS headers so browsers allow cross-origin calls
        headers.update(CORS_HEADERS)

        # Add any extra headers (like WWW-Authenticate)
        if extra_headers:
            headers.update(extra_headers)

        # Format each header as "Key: Value\r\n"
        header_lines = [status_line]
        for key, value in headers.items():
            header_lines.append("{}: {}".format(key, value))

        # Join with \r\n, add blank line before body
        response_str = "\r\n".join(header_lines) + "\r\n\r\n" + body
        return response_str.encode("utf-8")

    # ==============================================================
    #  FILE-SERVING METHODS — serve static content from disk
    # ==============================================================

    def get_mime_type(self, path):
        # Guess file type from extension

        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'

    def prepare_content_type(self, mime_type='text/html'):
        # Set Content-Type and find the right folder

        base_dir = ""

        # Make sure headers dict exists
        if not hasattr(self, "headers") or self.headers is None:
            self.headers = {}

        # Split "text/html" into main_type="text", sub_type="html"
        main_type, sub_type = mime_type.split('/', 1)
        print("[Response] Processing main_type={} sub_type={}".format(
            main_type, sub_type))

        if main_type == 'text':
            self.headers['Content-Type'] = 'text/{}'.format(sub_type)
            if sub_type == 'plain' or sub_type == 'css':
                base_dir = BASE_DIR + "static/"
            elif sub_type == 'html':
                base_dir = BASE_DIR + "www/"
            else:
                base_dir = BASE_DIR + "static/"
        elif main_type == 'image':
            base_dir = BASE_DIR + "static/"
            self.headers['Content-Type'] = 'image/{}'.format(sub_type)
        elif main_type == 'application':
            if sub_type == 'javascript':
                base_dir = BASE_DIR + "static/"
            else:
                base_dir = BASE_DIR + "apps/"
            self.headers['Content-Type'] = 'application/{}'.format(sub_type)
        else:
            # Unknown MIME type — fall back to static/
            base_dir = BASE_DIR + "static/"
            self.headers['Content-Type'] = mime_type

        return base_dir

    def build_content(self, path, base_dir):
        # Read file from disk

        filepath = os.path.join(base_dir, path.lstrip('/'))

        print("[Response] Serving file at {}".format(filepath))
        try:
            with open(filepath, "rb") as f:
                content = f.read()
        except Exception as e:
            print("[Response] build_content error: {}".format(e))
            return -1, b""
        return len(content), content

    def build_response_header(self, request):
        # Build the HTTP header block

        # Collect all header key-value pairs
        headers = {
            "Content-Type": self.headers.get(
                'Content-Type', 'application/octet-stream'),
            "Content-Length": str(len(self._content)),
            "Date": datetime.datetime.utcnow().strftime(
                "%a, %d %b %Y %H:%M:%S GMT"),
            "Cache-Control": "no-cache",
            "Connection": "close",
        }

        # Add CORS headers
        headers.update(CORS_HEADERS)

        # Build the status line
        status_line = "HTTP/1.1 {} {}".format(
            self.status_code or 200,
            self.reason or "OK"
        )

        # Format: "Key: Value\r\n" for each header
        header_lines = [status_line]
        for key, value in headers.items():
            header_lines.append("{}: {}".format(key, value))

        # End headers with a blank line
        fmt_header = "\r\n".join(header_lines) + "\r\n\r\n"
        return fmt_header.encode('utf-8')

    def build_notfound(self):
        # 404 response

        return (
            "HTTP/1.1 404 Not Found\r\n"
            "Accept-Ranges: bytes\r\n"
            "Content-Type: text/html\r\n"
            "Content-Length: 13\r\n"
            "Cache-Control: max-age=86000\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode('utf-8')

    def build_response(self, request, envelop_content=None):
        # Build response for a static file

        print("[Response] Building response for {}".format(request.path))

        path = request.path
        mime_type = self.get_mime_type(path)
        print("[Response] {} {} mime={}".format(
            request.method, request.path, mime_type))

        base_dir = ""

        # Choose the right directory based on file type
        base_dir = self.prepare_content_type(mime_type=mime_type)
        
        if mime_type in ('application/json', 'application/octet-stream'):
            envelop_content = ""

        # Read the file from disk
        content_length, content = self.build_content(path, base_dir)
        if content_length < 0:
            return self.build_notfound()

        # Store content for header building
        self._content = content
        self.status_code = 200
        self.reason = "OK"

        # Build the header
        self._header = self.build_response_header(request)

        return self._header + self._content

