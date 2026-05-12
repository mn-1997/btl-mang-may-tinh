import secrets
import time

# User data (In-memory)
USERS = {
    "alice": "123",
    "bob": "456",
    "charlie": "789",
}

# Current session tokens
ACTIVE_TOKENS = {}

# Tokens expire after 1 hour (3600 seconds)
TOKEN_EXPIRY_SECONDS = 3600


def register_user(username, password):
    # Create a new user account

    if username in USERS:
        return False
    
    USERS[username] = password
    return True


def authenticate(username, password):
    # Check login details and return a token if correct

    # Check if the user exists and the password is correct
    if username in USERS and USERS[username] == password:
        return _generate_token(username)
    return None


def _generate_token(username):
    # Generate a unique hex token with an expiry time

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
    # Check if a token is still valid and not expired

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
    # Delete a token to log out the user

    if token in ACTIVE_TOKENS:
        del ACTIVE_TOKENS[token]
        return True
    return False
