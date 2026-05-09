import argparse
from apps.peer_node import app
import sys

def main():
    parser = argparse.ArgumentParser(description="Start the Local P2P Node (UI & Chat Server)")
    parser.add_argument("--ip", default="127.0.0.1", help="IP address to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    args = parser.parse_args()

    print(f"========================================")
    print(f" Starting Local P2P Node...")
    print(f" UI Access: http://{args.ip}:{args.port}/index.html")
    print(f" Listening for P2P on Port: {args.port}")
    print(f"========================================")

    # Configure the framework with the chosen IP and port
    app.prepare_address(args.ip, args.port)

    try:
        # Launch the asyncio backend
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down P2P Node...")
        sys.exit(0)

if __name__ == "__main__":
    main()
