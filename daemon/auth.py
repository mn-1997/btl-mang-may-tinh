import secrets
import time

# ---------------------------------------------------------
# Simple In-Memory User Database
# Real apps would use a database file or server.
# ---------------------------------------------------------
USERS = {
    "alice": "123",
    "bob": "456",
    "charlie": "789",
}

# ---------------------------------------------------------
# Active Tokens Dictionary
# Maps a token string to user information and expiry time.
# Format: { "token_abc...": {"username": "alice", "expires": 167...} }
# ---------------------------------------------------------
ACTIVE_TOKENS = {}

# Tokens expire after 1 hour (3600 seconds)
TOKEN_EXPIRY_SECONDS = 3600


def register_user(username, password):
    """
    Add a new user to the system.
    Returns True if successful, False if the user already exists.

    :param username: The new login name.
    :param password: The new password.
    """
    if username in USERS:
        return False
    
    USERS[username] = password
    return True


def authenticate(username, password):
    """
    Check if the username and password match our records.
    If valid, generate and return a new Bearer token.
    If invalid, return None.

    :param username: The user's login name.
    :param password: The user's password.
    :rtype: str (the token) or None
    """
    # Check if the user exists and the password is correct
    if username in USERS and USERS[username] == password:
        return _generate_token(username)
    return None


def _generate_token(username):
    """
    Generate a secure random Bearer token for the user.
    Stores it in ACTIVE_TOKENS with an expiration time.

    :param username: The user's name.
    :rtype: str (the generated token)
    """
    # Generate a random 32-byte hex string
    token = secrets.token_hex(32)
    
    # Calculate when the token should expire
    expires_at = time.time() + TOKEN_EXPIRY_SECONDS
    
    # Store the token details in memory
    ACTIVE_TOKENS[token] = {
        "username": username,
        "expires": expires_at,
    }

    # Log the token to a text file
    try:
        with open("tokens.txt", "a") as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] User: {username} | Token: {token}\n")
    except Exception as e:
        print(f"[Auth] Could not write to tokens.txt: {e}")
    
    return token


def validate_token(token):
    """
    Check if a token is valid (exists and has not expired).
    Returns the username if valid, otherwise None.

    :param token: The token string provided by the user.
    :rtype: str (the username) or None
    """
    # Check if we have this token in our active list
    if token not in ACTIVE_TOKENS:
        return None
        
    token_info = ACTIVE_TOKENS[token]
    
    # Check if the token has expired
    if time.time() > token_info["expires"]:
        # Token expired, remove it and return None
        del ACTIVE_TOKENS[token]
        return None
        
    # Token is valid, return the associated username
    return token_info["username"]


def logout(token):
    """
    Log the user out by deleting their active token.
    
    :param token: The token string to invalidate.
    :rtype: bool (True if successfully logged out, False if token wasn't valid)
    """
    if token in ACTIVE_TOKENS:
        del ACTIVE_TOKENS[token]
        return True
    return False
