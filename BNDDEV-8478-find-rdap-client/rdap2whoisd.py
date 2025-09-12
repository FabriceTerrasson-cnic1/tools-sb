#!/usr/bin/env python3
import socket
import subprocess
import argparse

# -----------------------------
# Handle command-line arguments
# -----------------------------
parser = argparse.ArgumentParser(description="WHOIS proxy using OpenRDAP")
parser.add_argument("--port", type=int, default=43, help="Port to listen on (default: 43)")
args = parser.parse_args()

HOST = "0.0.0.0"   # Listen on all interfaces
PORT = args.port   # Use port from arguments

# -----------------------------
# Functions
# -----------------------------
def handle_query(query):
    domain = query.strip()
    if not domain:
        return "Invalid query\n"
    try:
        result = subprocess.check_output(
            ["/root/bin/rdap", "-w", domain],
            stderr=subprocess.STDOUT,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output}\n"

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"WHOIS proxy running on port {PORT}...")
        while True:
            conn, addr = s.accept()
            with conn:
                query = conn.recv(1024).decode("utf-8").strip()
                print(f"Query from {addr}: {query}")
                response = handle_query(query)
                conn.sendall(response.encode("utf-8"))

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    run_server()
