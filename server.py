import socket
import select
import model
IP = "127.0.0.1"
PORT = 9090

HEADER_LENGTH = 10

# Create a socket
# socket.AF_INET - address family, IPv4
# socket.SOCK_STREAM - TCP, conection-based,
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# SO_ - socket option
# SOL_ - socket option level
# Sets REUSEADDR (as a socket option) to 1 on socket
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


# Bind, so server informs operating system that it's going to use given IP and port
server_socket.bind((IP, PORT))

# This makes server listen to new connections
server_socket.listen()

# List of sockets for select.select()
sockets_list = [server_socket]  # store all sockets(clients) in one list

# List of connected clients - socket as a key, user header and name as data
clients = {}
print(f'Listening for connections on {IP}:{PORT}...')

doctors = model.GetAllDoctors()


def receive_message(client_socket):
    ''' Handles message receiving '''
    try:
        # Recieve the header
        message_header = client_socket.recv(HEADER_LENGTH)

        if not len(message_header):
            # Client closed connection or smth else, but we didnt get the msg
            return False

        # Length of the actual msg, strip for type conversion.
        message_length = int(message_header.decode('utf-8').strip())

        # Return a dict
        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:
        # Something went wrong like empty message or client exited abruptly.
        return False


while True:
    # select() call with three parameters:
    #   - rlist - sockets to be monitored for incoming data
    #   - wlist - sockets for data to be send to (checks if for example buffers are not full and socket is ready to send some data)
    #   - xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
    # Returns lists:
    #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
    #   - writing - sockets ready for data to be send thru them
    #   - errors  - sockets with some exceptions
    read_sockets, _, exception_sockets = select.select(
        sockets_list, [], sockets_list)

    # doctor_flag used to check if the doctor found in the database
    doctor_flag = 0
    # send_once_flag used to make sure that the message is sent only once
    send_once_flag = 0

    # Iterate over notified sockets
    for notified_socket in read_sockets:
        # If notified socket is a server socket - new connection, accept it
        if notified_socket == server_socket:
            # Accept new connection
            client_socket, client_address = server_socket.accept()

            # Client should send his name right away, receive it
            user = receive_message(client_socket)
            # store the received name to check if that user is a registered doctor or not
            temp_username = user['data'].decode('utf8')

            for i in range(len(doctors)):
                # iterate in doctors table using temp_username
                if temp_username == doctors[i][0]:
                    # if that client is a doctor; break.
                    doctor_flag = 1
                    break

            if(doctor_flag == 0):
                # if doctor is not found; store the client as a temp-patient in the database.
                model.addPatient(temp_username, client_address[1])
                print(
                    f"Patient added to db with name: {temp_username} and address: {client_address[1]}")
                doctor_flag = 1

            # If False - client disconnected before he sent his name
            if user is False:
                continue

            # Add accepted socket to select.select() list
            sockets_list.append(client_socket)

            # Also save username and username header
            clients[client_socket] = user

            print('Accepted new connection from {}:{}, username: {}'.format(
                *client_address, user['data'].decode('utf-8')))
        else:
            # Receive a message
            message = receive_message(notified_socket)

            # Receive the type associated with the message
            type = receive_message(notified_socket)

            # If False, client disconnected, cleanup
            if message is False:
                print('Closed connection from: {}'.format(
                    clients[notified_socket]['data'].decode('utf-8')))
                # Remove from list for socket.socket()
                sockets_list.remove(notified_socket)
                # Remove from our list of users
                del clients[notified_socket]
                continue

            # Get user by notified socket, so we will know who sent the message
            user = clients[notified_socket]
            print('Received message from: {}: {}; type: {}'.format(
                user["data"].decode("utf-8"), message["data"].decode("utf-8"), type["data"].decode("utf-8")))

            # Now we need to broadcast this message out to all specific connected clients:
            # Iterate over connected clients and broadcast message
            for client_socket in clients:

                send_once_flag = 0
                # Get the patient's address and store it -> patient_raddr
                patient_raddr = 0

                # Retrieve the active patients' rows from the database
                active_patients = model.GetAllPatients()

                # store the name sent with the message -> patient_name
                patient_name = type["data"].decode('utf-8')

                # double check that the name associated with the message is the same in the database
                for patient in active_patients:
                    if(patient_name == patient[0]):
                        patient_raddr = patient[1]

                # if client_socket address matches the addres in db; send.
                temp_ = client_socket.getpeername()
                current_client_raddr = temp_[1]

                if(current_client_raddr == patient_raddr):
                    # Send user and message (both with their headers)
                    # We are reusing here message header sent by sender, and saved username header send by user when he connected
                    client_socket.send(
                        user['header'] + user['data'] + message['header'] + message['data'] + type['header'] + type['data'])

                if client_socket == notified_socket:
                    # resend the message to the sender to see it on his screen
                    send_once_flag = 1
                    client_socket.send(
                        user['header'] + user['data'] + message['header'] + message['data'] + type['header'] + type['data'])

                for i in range(len(doctors)):
                    # send the message to the chosen specialty
                    name = clients[client_socket]['data']
                    name = name.decode('utf-8')
                    if (name == doctors[i][0]) and (send_once_flag == 0):
                        # my client is a doctor
                        if (doctors[i][1] == type["data"].decode('utf-8')):
                            client_socket.send(
                                user['header'] + user['data'] + message['header'] + message['data'] + type['header'] + type['data'])

    # Handle some socket exceptions just in case (not really necessary).
    for notified_socket in exception_sockets:

        # Remove from list for socket.socket()
        sockets_list.remove(notified_socket)

        # Remove from our list of users
        del clients[notified_socket]
