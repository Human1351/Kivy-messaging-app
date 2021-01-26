import select
import socket

HEADER_LENGTH = 10
IP = "127.0.0.1"
PORT = 1234

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       # Initial socket setup
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)     # Allows to reconnect to same server:port

# Bind, Listen, update sockets_list
server_socket.bind((IP, PORT))
server_socket.listen()
sockets_list = [server_socket]

print(f'Listening for connections on {IP}:{PORT}')
clients = {}


def receive_message(client_sock):
    """
    Handles message receiving - similar way as client is sending/recieving
    """
    try:
        message_header = client_sock.recv(HEADER_LENGTH)                # Read the header
        if not len(message_header):                                     # Break loop if no header
            return False
        message_length = int(message_header.decode("utf-8").strip())    # Convert header to length
        return {"header": message_header, "data": client_sock.recv(message_length)}
    except:
        return False


# Receive messages for all client sockets, then send all messages to all client sockets.
while True:
    # select.select(read_list, write_list, error_list)
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        if notified_socket == server_socket:                        # If True -> new connection
            client_socket, clientaddress = server_socket.accept()   # Unique client socket and their address
            user = receive_message(client_socket)
            if user is False:
                continue
            sockets_list.append(client_socket)          # Append NEW socket to list of sockets
            clients[client_socket] = user               # Save this client as socket obj.
            print(f"Accepted new connection from {clientaddress[0]}:{clientaddress[1]}")
            print(f" username :{user['data'].decode('utf-8')}")
        else:
            # If not server socket, a message is incoming.
            message = receive_message(notified_socket)
            if message is False:
                # If the client disconnects...
                print(f"Closed connection from {clients[notified_socket]['data'].decode('utf-8')}")
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue
            user = clients[notified_socket]  # Connection is open && message -> print message
            print(f"Recieved message from {user['data'].decode('utf-8')}: {message['data'].decode('utf-8')}")

            for client_socket in clients:
                # Send message (message header sent by sender - username header sent by user on connect)
                if client_socket != notified_socket:
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

    # Handle for the exception/error sockets & remove client from list of users
    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]
