import argparse
from apps.tracker import app
import sys

def main():
    parser = argparse.ArgumentParser(description="Start the Tracker Server")
    parser.add_argument("--ip", default="127.0.0.1", help="IP address to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7000, help="Port to listen on (default: 7000)")
    args = parser.parse_args()

    print(f"========================================")
    print(f" Starting Tracker Server...")
    print(f" IP:   {args.ip}")
    print(f" Port: {args.port}")
    print(f"========================================")

    # Configure the framework with the chosen IP and port
    app.prepare_address(args.ip, args.port)

    try:
        # Launch the asyncio backend
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down Tracker Server...")
        sys.exit(0)

if __name__ == "__main__":
    main()
