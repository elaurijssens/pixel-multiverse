import socket
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# Define socket path and log file path
SOCKET_PATH = "/tmp/pixel_multiverse.sock"
LOG_FILE_PATH = "/var/log/pixel_multiverse.log"

# Set up logging with rotation: 5 MB per file, up to 3 backup files
logger = logging.getLogger("PixelMultiverseService")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=5 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Also log to stdout for systemd to capture
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)

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
    logger.info(f"Listening on {SOCKET_PATH}...")

    while True:
        # Accept a client connection
        client_socket, client_address = server_socket.accept()
        logger.info("Connection established.")

        with client_socket:
            while True:
                data = client_socket.recv(1024)  # Receive data from client
                if not data:
                    # No more data; client has closed the connection
                    break
                # Log received data
                logger.info("Received: %s", data.decode().strip())

except Exception as e:
    logger.error("Error: %s", e)
finally:
    # Clean up on exit
    server_socket.close()
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)
    logger.info("Server shut down.")
