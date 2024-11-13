import socket
import os
import sys

# Define socket path
SOCKET_PATH = "/tmp/pixel_multiverse.sock"

# Clean up the socket file if it already exists
if os.path.exists(SOCKET_PATH):
    os.remove(SOCKET_PATH)

# Set up the Unix socket
server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

try:
    # Bind the socket to the path and listen for incoming connections
    server_socket.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o666)
    server_socket.listen(1)
    print(f"Listening on {SOCKET_PATH}...")

    while True:
        # Accept a client connection
        client_socket, client_address = server_socket.accept()
        print("Connection established.")

        with client_socket:
            while True:
                data = client_socket.recv(1024)  # Receive data from client
                if not data:
                    # No more data; client has closed the connection
                    break
                # Log received data (in real use, replace this with actual handling logic)
                print("Received:", data.decode().strip())

except Exception as e:
    print(f"Error: {e}")
finally:
    # Clean up on exit
    server_socket.close()
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)
    print("Server shut down.")

