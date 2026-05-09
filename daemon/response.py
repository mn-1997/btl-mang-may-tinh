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

This module builds HTTP responses to send back to clients.

It can:
  - Serve static files (HTML, CSS, images) from disk
  - Build JSON API responses (200 OK, 400 Bad Request, 401 Unauthorized, etc.)
  - Attach CORS headers so browsers allow cross-origin requests
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
    """Builds and sends HTTP responses.

    Two main usage patterns:
    1. **File responses** — serve HTML/CSS/images from disk via build_response()
    2. **JSON responses** — return API data via the static helper methods

    Attributes:
        status_code (int): HTTP status code (e.g., 200, 404).
        headers (dict): Response headers.
        _content (bytes): The response body as raw bytes.
        _header (bytes): The formatted response header as raw bytes.
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

        #: HTTP status code (e.g. 200, 404)
        self.status_code = None

        #: Response headers dictionary
        self.headers = {}

        #: URL of the response
        self.url = None

        #: Text encoding (e.g. "utf-8")
        self.encoding = None

        #: Redirect history
        self.history = []

        #: Human-readable status reason (e.g. "OK", "Not Found")
        self.reason = None

        #: Response cookies
        self.cookies = CaseInsensitiveDict()

        #: Time elapsed for the request
        self.elapsed = datetime.timedelta(0)

        #: The original request that produced this response
        self.request = request

    # ==============================================================
    #  STATIC HELPERS — build complete HTTP response bytes
    #  These are the main methods your route handlers will use.
    # ==============================================================

    @staticmethod
    def build_json_ok(data):
        """Build a 200 OK response with a JSON body.

        Use this for successful API responses like:
          {"message": "Logged in successfully", "token": "abc123"}

        :param data (dict): Python dict to serialize as JSON.
        :rtype: bytes — the complete HTTP response ready to send.
        """
        body = json.dumps(data)
        return Response._build_json_response(200, "OK", body)

    @staticmethod
    def build_json_error(status_code, message):
        """Build an error response with a JSON body.

        Use this for 400 Bad Request, 404 Not Found, etc:
          {"error": "Missing username field"}

        :param status_code (int): The HTTP error code.
        :param message (str): Human-readable error description.
        :rtype: bytes
        """
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
        """Shortcut for 401 Unauthorized responses.

        Automatically includes the WWW-Authenticate header
        telling the client to use Bearer tokens.

        :param message (str): Error detail.
        :rtype: bytes
        """
        body = json.dumps({"error": message})
        extra_headers = {
            "WWW-Authenticate": 'Bearer realm="asynaprous"',
        }
        return Response._build_json_response(
            401, "Unauthorized", body, extra_headers)

    @staticmethod
    def build_cors_preflight():
        """Handle CORS preflight (OPTIONS) requests.

        Browsers send an OPTIONS request before the actual request
        when using custom headers like Authorization. This response
        tells the browser "yes, you're allowed to proceed."

        :rtype: bytes
        """
        return Response._build_json_response(204, "No Content", "")

    @staticmethod
    def _build_json_response(status_code, reason, body, extra_headers=None):
        """Internal helper that assembles a complete HTTP response string.

        Combines the status line, standard headers, CORS headers,
        any extra headers, and the body into a single byte string.

        :param status_code (int): HTTP status code.
        :param reason (str): Status reason phrase.
        :param body (str): Response body string.
        :param extra_headers (dict): Additional headers to include.
        :rtype: bytes
        """
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
        """Guess the MIME type of a file from its extension.

        Examples: "index.html" -> "text/html", "style.css" -> "text/css"

        :param path (str): File path or name.
        :rtype: str — MIME type string.
        """
        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'

    def prepare_content_type(self, mime_type='text/html'):
        """Set the Content-Type header and determine the file directory.

        Different MIME types are served from different directories:
          - text/html  -> www/
          - text/css   -> static/
          - image/*    -> static/
          - application/* -> apps/

        :param mime_type (str): MIME type of the requested resource.
        :rtype: str — base directory path.
        """
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
            base_dir = BASE_DIR + "apps/"
            self.headers['Content-Type'] = 'application/{}'.format(sub_type)
        else:
            # Unknown MIME type — fall back to static/
            base_dir = BASE_DIR + "static/"
            self.headers['Content-Type'] = mime_type

        return base_dir

    def build_content(self, path, base_dir):
        """Read a file from disk and return its contents.

        :param path (str): Relative path to the file.
        :param base_dir (str): Directory where the file is located.
        :rtype: tuple (content_length, content_bytes)
        """
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
        """Build the HTTP response header lines as bytes.

        Creates a standard header block with Content-Type, Date,
        Content-Length, CORS headers, etc.

        :param request: The incoming Request object.
        :rtype: bytes — encoded HTTP response header.
        """
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
        """Build a 404 Not Found response for missing files.

        :rtype: bytes
        """
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
        """Build a full HTTP response for a file-serving request.

        This is the main method for serving static files. It:
        1. Determines the MIME type from the file extension
        2. Finds the file on disk
        3. Reads the content
        4. Constructs headers + body

        :param request: The incoming Request object.
        :param envelop_content: Optional pre-built content.
        :rtype: bytes — the complete HTTP response.
        """
        print("[Response] Building response for {}".format(request.path))

        path = request.path
        mime_type = self.get_mime_type(path)
        print("[Response] {} {} mime={}".format(
            request.method, request.path, mime_type))

        base_dir = ""

        # Choose the right directory based on file type
        if path.endswith('.html') or mime_type == 'text/html':
            base_dir = self.prepare_content_type(mime_type='text/html')
        elif mime_type == 'text/css':
            base_dir = self.prepare_content_type(mime_type='text/css')
        elif mime_type in ('application/json', 'application/octet-stream'):
            base_dir = self.prepare_content_type(mime_type='application/json')
            envelop_content = ""
        else:
            return self.build_notfound()

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

