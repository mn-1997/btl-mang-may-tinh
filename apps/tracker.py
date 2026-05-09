import json
from daemon.asynaprous import AsynapRous
from daemon.response import Response
from daemon.auth import authenticate, logout, register_user

# ---------------------------------------------------------
# The AsynapRous Application Instance
# ---------------------------------------------------------
app = AsynapRous()

# ---------------------------------------------------------
# Simple In-Memory Peer Database
# Format: { "alice": {"ip": "192.168.1.5", "port": 5000} }
# ---------------------------------------------------------
PEERS = {}

# =========================================================
# API Endpoints
# =========================================================

@app.route('/register', methods=['POST'])
async def register_handler(headers, body):
    """
    Register a brand new user.
    Expects JSON: {"username": "...", "password": "..."}
    """
    try:
        data = json.loads(body) if body else {}
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return Response.build_json_error(400, "Missing username or password")
            
        if register_user(username, password):
            return Response.build_json_ok({"message": f"User {username} registered successfully!"})
        else:
            return Response.build_json_error(400, "Username already exists")
            
    except json.JSONDecodeError:
        return Response.build_json_error(400, "Invalid JSON body")


@app.route('/login', methods=['POST'])
async def login_handler(headers, body):
    """
    Authenticate a user and return a Bearer token.
    Expects JSON: {"username": "...", "password": "..."}
    """
    try:
        # Parse the JSON body
        data = json.loads(body) if body else {}
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return Response.build_json_error(400, "Missing username or password")
            
        # Verify credentials and generate token
        token = authenticate(username, password)
        if token:
            return Response.build_json_ok({"access_token": token})
        else:
            return Response.build_unauthorized("Invalid credentials")
            
    except json.JSONDecodeError:
        return Response.build_json_error(400, "Invalid JSON body")


@app.route('/submit-info', methods=['POST'], auth_required=True)
async def submit_info_handler(headers, body):
    """
    Submit the peer's current IP and port.
    Requires Bearer token.
    Expects JSON: {"ip": "127.0.0.1", "port": 5000}
    """
    try:
        # We know who this is because auth_required=True intercepted the token
        username = headers.get("_authenticated_user")
        
        data = json.loads(body) if body else {}
        ip = data.get("ip")
        port = data.get("port")
        
        if not ip or not port:
            return Response.build_json_error(400, "Missing IP or port")
            
        # Save their info in our in-memory dictionary
        PEERS[username] = {"ip": ip, "port": port}
        
        return Response.build_json_ok({"message": f"Info submitted successfully for {username}"})
        
    except json.JSONDecodeError:
        return Response.build_json_error(400, "Invalid JSON body")


@app.route('/get-list', methods=['GET'], auth_required=True)
async def get_list_handler(headers, body):
    """
    Retrieve the list of all online peers.
    Requires Bearer token.
    STRICT MODE: User must have submitted their own info first.
    """
    username = headers.get("_authenticated_user")
    
    # Check if the user has shared their own info yet
    if username not in PEERS:
        return Response.build_json_error(
            403, "Forbidden: You must call /submit-info before you can see other peers."
        )

    # Convert our PEERS dictionary into a list of objects
    peer_list = []
    for peer_name, info in PEERS.items():
        peer_list.append({
            "username": peer_name,
            "ip": info["ip"],
            "port": info["port"]
        })
        
    return Response.build_json_ok({"peers": peer_list})


@app.route('/logout', methods=['POST'], auth_required=True)
async def logout_handler(headers, body):
    """
    Log the user out by invalidating their token.
    Requires Bearer token.
    """
    # Extract the token from the Authorization header
    auth_header = headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        logout(token)  # Invalidates it in the auth module
        
        username = headers.get("_authenticated_user")
        
        # Optionally, remove them from the active peer list too
        if username in PEERS:
            del PEERS[username]
            
        return Response.build_json_ok({"message": "Successfully logged out"})
        
    return Response.build_json_error(400, "Could not process logout")
