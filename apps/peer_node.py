import json
import asyncio
import time
from urllib.request import Request as URLLibRequest
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from daemon.asynaprous import AsynapRous
from daemon.response import Response

app = AsynapRous()

# ---------------------------------------------------------
# Local Node State
# ---------------------------------------------------------
class NodeState:
    def __init__(self):
        self.username = None
        self.tracker_ip = None
        self.tracker_port = None
        self.token = None
        self.messages = []  # List of dicts: {"from": "user", "text": "msg", "timestamp": "...", "channel": "broadcast|direct"}

state = NodeState()

# =========================================================
# HELPER: Make Async HTTP Requests to Tracker/Peers
# =========================================================
async def async_http_post(url, payload, headers=None):
    """Simple wrapper to make non-blocking HTTP POST requests."""
    loop = asyncio.get_event_loop()
    
    def _do_post():
        req = URLLibRequest(url, data=json.dumps(payload).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        try:
            with urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode('utf-8')), response.status
        except HTTPError as e:
            return json.loads(e.read().decode('utf-8')), e.code
        except URLError as e:
            return {"error": str(e.reason)}, 500
            
    return await loop.run_in_executor(None, _do_post)

async def async_http_get(url, headers=None):
    """Simple wrapper to make non-blocking HTTP GET requests."""
    loop = asyncio.get_event_loop()
    
    def _do_get():
        req = URLLibRequest(url)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        try:
            with urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode('utf-8')), response.status
        except HTTPError as e:
            return json.loads(e.read().decode('utf-8')), e.code
        except URLError as e:
            return {"error": str(e.reason)}, 500
            
    return await loop.run_in_executor(None, _do_get)

# =========================================================
# LOCAL WEB UI APIs (Called by the browser frontend)
# =========================================================

@app.route('/api/register', methods=['POST'])
async def register_api_handler(headers, body):
    """
    Called by the UI to register a new user on the tracker.
    """
    try:
        data = json.loads(body) if body else {}
        username = data.get("username")
        password = data.get("password")
        tracker_ip = data.get("tracker_ip", "127.0.0.1")
        tracker_port = data.get("tracker_port", 7000)
        
        # Call the tracker's registration endpoint
        url = f"http://{tracker_ip}:{tracker_port}/register"
        resp_data, status = await async_http_post(url, {"username": username, "password": password})
        
        if status == 200:
            return Response.build_json_ok(resp_data)
        else:
            return Response.build_json_error(status, resp_data.get("error", "Registration failed"))
            
    except json.JSONDecodeError:
        return Response.build_json_error(400, "Invalid JSON body")


@app.route('/api/setup', methods=['POST'])
async def setup_handler(headers, body):
    """
    Called by the UI to login to the tracker and submit our local info.
    """
    try:
        data = json.loads(body) if body else {}
        username = data.get("username")
        password = data.get("password")
        tracker_ip = data.get("tracker_ip", "127.0.0.1")
        tracker_port = data.get("tracker_port", 7000)
        
        # 1. Login to tracker
        login_url = f"http://{tracker_ip}:{tracker_port}/login"
        resp_data, status = await async_http_post(login_url, {"username": username, "password": password})
        
        if status != 200 or "access_token" not in resp_data:
            return Response.build_json_error(400, resp_data.get("error", "Login failed"))
            
        token = resp_data["access_token"]
        
        # 2. Submit our local IP and Port
        # We need to tell the tracker what port WE are listening on
        # For simplicity, we assume we are running on localhost and the app knows its port.
        # We can extract the port from the Host header of the UI's request!
        host_header = headers.get("host", "127.0.0.1:8000")
        local_ip, local_port = host_header.split(":")
        
        submit_url = f"http://{tracker_ip}:{tracker_port}/submit-info"
        auth_headers = {"Authorization": f"Bearer {token}"}
        resp_data, status = await async_http_post(submit_url, {"ip": local_ip, "port": int(local_port)}, auth_headers)
        
        if status != 200:
            return Response.build_json_error(400, "Failed to submit info to tracker")
            
        # 3. Save state
        state.username = username
        state.tracker_ip = tracker_ip
        state.tracker_port = tracker_port
        state.token = token
        
        return Response.build_json_ok({"message": "Setup complete"})
        
    except json.JSONDecodeError:
        return Response.build_json_error(400, "Invalid JSON body")


@app.route('/api/peers', methods=['GET'])
async def get_peers_handler(headers, body):
    """
    Called by the UI to fetch the list of online peers from the tracker.
    """
    if not state.token:
        return Response.build_json_error(401, "Not logged in")
        
    url = f"http://{state.tracker_ip}:{state.tracker_port}/get-list"
    auth_headers = {"Authorization": f"Bearer {state.token}"}
    resp_data, status = await async_http_get(url, auth_headers)
    
    if status == 200:
        return Response.build_json_ok(resp_data)
    else:
        return Response.build_json_error(status, "Failed to fetch peers")


@app.route('/api/messages', methods=['GET'])
async def get_messages_handler(headers, body):
    """
    Called by the UI to poll for new messages.
    """
    return Response.build_json_ok({"messages": state.messages})


@app.route('/api/send_message', methods=['POST'])
async def send_message_handler(headers, body):
    """
    Called by the UI to send a message to a peer or broadcast to all.
    Expects: {"target": "username" or "broadcast", "message": "hello!"}
    """
    if not state.token:
        return Response.build_json_error(401, "Not logged in")
        
    try:
        data = json.loads(body) if body else {}
        target = data.get("target")
        text = data.get("message")
        
        if not target or not text:
            return Response.build_json_error(400, "Missing target or message")
            
        # Fetch peer list to find targets
        url = f"http://{state.tracker_ip}:{state.tracker_port}/get-list"
        auth_headers = {"Authorization": f"Bearer {state.token}"}
        resp_data, status = await async_http_get(url, auth_headers)
        
        if status != 200:
            return Response.build_json_error(500, "Could not fetch peers to send message")
            
        peers = resp_data.get("peers", [])
        
        # Add to our own local history first
        timestamp = time.strftime("%H:%M:%S")
        channel = "broadcast" if target == "broadcast" else "direct"
        
        state.messages.append({
            "from": state.username,
            "to": target,
            "text": text,
            "timestamp": timestamp,
            "channel": channel
        })

        payload = {
            "from": state.username,
            "text": text,
            "channel": channel
        }
        
        # Broadcast
        if target == "broadcast":
            for p in peers:
                if p["username"] != state.username:
                    # Send to this peer's /p2p/receive endpoint
                    peer_url = f"http://{p['ip']}:{p['port']}/p2p/receive"
                    # We don't await blocking here, we just fire and forget or gather
                    asyncio.create_task(async_http_post(peer_url, payload))
            return Response.build_json_ok({"message": "Broadcast sent"})
            
        # Direct Message
        else:
            for p in peers:
                if p["username"] == target:
                    peer_url = f"http://{p['ip']}:{p['port']}/p2p/receive"
                    resp, st = await async_http_post(peer_url, payload)
                    if st == 200:
                        return Response.build_json_ok({"message": "Message sent"})
                    else:
                        return Response.build_json_error(st, "Failed to deliver message to peer")
                        
            return Response.build_json_error(404, "Target peer not found or offline")
            
    except json.JSONDecodeError:
        return Response.build_json_error(400, "Invalid JSON body")


# =========================================================
# P2P NETWORK APIs (Called by OTHER PEERS)
# =========================================================

@app.route('/p2p/receive', methods=['POST'])
async def p2p_receive_handler(headers, body):
    """
    Called by another peer to deliver a message to us.
    """
    try:
        data = json.loads(body) if body else {}
        sender = data.get("from")
        text = data.get("text")
        channel = data.get("channel", "direct")
        
        if not sender or not text:
            return Response.build_json_error(400, "Missing sender or text")
            
        timestamp = time.strftime("%H:%M:%S")
        
        # Store in local history so the UI can fetch it
        state.messages.append({
            "from": sender,
            "to": state.username if channel == "direct" else "broadcast",
            "text": text,
            "timestamp": timestamp,
            "channel": channel
        })
        
        # Print to console as well
        print(f"[P2P Message] From {sender} ({channel}): {text}")
        
        return Response.build_json_ok({"message": "Message received"})
        
    except json.JSONDecodeError:
        return Response.build_json_error(400, "Invalid JSON body")
