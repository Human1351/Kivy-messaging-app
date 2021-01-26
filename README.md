# Kivy-messaging-app
A messaging app between two or more clients, using mostly Kivy and Sockets.

This app allows two or more users to send and recieve messages via sockets with a script to run the server. This version of the app uses a basic Kivy GUI for possible future integration with a mobile client.

Please note, this app uses the default socket connection types (AF_INET and SOCK_STREAM) as the connection to the server program, and is potentially unsecure. This app has not been tested for security vulnerabilities and should not be connected to unsecure networks/devices without optimization.  A few alternatives have been left in the comments of socket_client.py if you would rather impliment and optimize those. See [documentation](https://docs.python.org/3.8/library/socket.html#socket.socket) for more details.
