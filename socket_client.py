import socket
from threading import Thread

HEADER_LENGTH = 10
client_socket = None


def connect(ip, port, my_username, error_callback):
    """
    Connects to the server
    """
    global client_socket

    # Create a socket (socket.AF_INET == IPv4 (options: AF_INET6, AF_BLUETOOTH, AF_UNIX))
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to given ip and port
        client_socket.connect((ip, port))
    except Exception as e:
        # Connection error
        error_callback(f'Connection error: {str(e)}')
        return False

    # NOTE: using threading means blocking ins't needed (from v1)

    # Encode username to bytes, then count bytes, prepare & encode header (fixed size), Send.
    username = my_username.encode("utf-8")
    username_header = f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
    client_socket.send(username_header + username)
    return True


def send(message):
    """
    Sends a message to the server
    If message is not empty, encode message to bytes, prepare header and convert to bytes (like username), then send
    """
    message = message.encode("utf-8")
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode("utf-8")
    client_socket.send(message_header + message)


def start_listening(incoming_message_callback, error_callback):
    """
    Start listening in a thread.
    :param incoming_message_callback: callback to be called when new message arrives
    :param error_callback: callback to be called on error
    """
    Thread(target=listen, args=(incoming_message_callback, error_callback), daemon=True).start()


def listen(incoming_message_callback, error_callback):
    """
    Listen for incoming data
    :param incoming_message_callback: callback to be called when new message arrives
    :param error_callback: callback to be called on error
    """
    while True:
        try:
            # Now we want to loop over received messages (there might be more than one) and print them
            while True:
                username_header = client_socket.recv(HEADER_LENGTH)
                if not len(username_header):
                    # If we received no data, connection is closed -> throw error (exit).
                    error_callback('Connection closed by the server')

                username_length = int(username_header.decode('utf-8').strip())      # Convert header to int value
                username = client_socket.recv(username_length).decode('utf-8')      # Receive and decode username

                # Same for message - but no need to check for length.
                message_header = client_socket.recv(HEADER_LENGTH)
                message_length = int(message_header.decode('utf-8').strip())
                message = client_socket.recv(message_length).decode('utf-8')
                incoming_message_callback(username, message)

        except Exception as e:      # Any other exception => display info screen
            error_callback('Reading error: {}'.format(str(e)))
