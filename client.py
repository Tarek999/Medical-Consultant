import socket
import tkinter
import tkinter.scrolledtext
from tkinter import simpledialog, OptionMenu
import model
import errno  # to math specific errors handling
import sys
import threading

HOST = '127.0.0.1'
PORT = 9090

HEADER_LENGTH = 10

doctors = model.GetAllDoctors()
doctors_names = []

for i in range(len(doctors)):
    doctors_names.append(doctors[i][0])

class Client:
    def __init__(self, host, port):

        msg = tkinter.Tk()
        msg.withdraw()

        # Type your username
        self.name = simpledialog.askstring(
            "Name", "Please choose a Username", parent=msg)

        # Create a socket (of socket.AF_INET - address family), (socket.SOCK_STREAM - TCP, conection-based,)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to a given HOST and port
        self.client_socket.connect((HOST, PORT))

        # Set connection to non-blocking state, so .recv() call won't get blocked
        self.client_socket.setblocking(False)

        # Prepare username and header and send them
        # We need to encode username to bytes, then count number of bytes and prepare header of fixed size, that we encode to bytes as well
        self.username = self.name.encode('utf-8')

        self.username_header = f"{len(self.username):<{HEADER_LENGTH}}".encode(
            'utf-8')
        # ():<{} ==> '<' option is put for alignment, to force the field to be left-aligned within the available space

        # Sender name and his header are sent to the server only once
        self.client_socket.send(self.username_header + self.username)

        self.gui_done = False
        self.running = True

        self.active_patients = []
        self.doctor_scenario_flag = 0

        # Threading is used to keep receive function running all the time -> [Referesh GUI instantly]
        gui_thread = threading.Thread(target=self.GUI_Window)
        receive_thread = threading.Thread(target=self.receiveFromServer)

        gui_thread.start()
        receive_thread.start()

    # GUI Function using TKinter

    def GUI_Window(self):
        global patients_names
        self.window = tkinter.Tk()
        self.window.configure(bg="lightblue")

        self.window.title(self.name)
        self.window.iconbitmap(r'favicon.ico')

        self.chatLabel = tkinter.Label(
            self.window, text="Chat", bg="lightblue")
        self.chatLabel.config(font=('Areal', 12))
        self.chatLabel.pack(padx=20, pady=5)

        self.textArea = tkinter.scrolledtext.ScrolledText(
            self.window, bg='#DDD')
        self.textArea.config(state="disabled", bg='lightgrey')
        self.textArea.pack(padx=20, pady=5)

        self.msgLabel = tkinter.Label(
            self.window, text="Message", bg="lightblue")
        self.msgLabel.config(font=('Areal', 12))
        self.msgLabel.pack(padx=20, pady=5)

        self.inputArea = tkinter.Text(self.window, height=3, bg='#DDD')
        self.inputArea.pack(padx=20, pady=5)

        self.btn = tkinter.Button(
            self.window, text="Send", command=self.sendToServer, bg='lightblue')
        self.btn.config(font=('Areal', 12))
        self.btn.pack(padx=20, pady=5)
        
        # Get all current patients' rows
        patients_names = model.GetAllPatients()
        
        for i in range(len(patients_names)):
            # Separate only names 
            self.active_patients.append(patients_names[i][0])

        if (self.name in doctors_names):
            # If the user logged in is a doctor; hide radiobuttons and show the dropdownItems
            self.dropdownItem = tkinter.StringVar(self.window)
            self.dropdownItem.set(self.active_patients[0])
            self.dropdownList = OptionMenu(self.window, self.dropdownItem, *self.active_patients)
            self.dropdownList.config(bg='light blue')
            self.dropdownList.pack()
            
        else:
            global r
            r = tkinter.IntVar(self.window)
            radioButton1 = tkinter.Radiobutton(
                self.window, text="Send to Psychiatrists", variable=r, value=1, bg='lightblue').pack()
            radioButton2 = tkinter.Radiobutton(
                self.window, text="Send to Cardiologists", variable=r, value=2, bg='lightblue').pack()

        self.gui_done = True
        # KILL THE WINDOW
        self.window.protocol("WM_DELETE_WINDOW", self.stop)

        self.window.mainloop()

    def stop(self):
        # STOP THE PROCESS
        self.running = False
        self.window.destroy()
        self.client_socket.close()
        # Delete the patient row from the database
        model.dropPatientByName(self.name)
        print('patient drop from stop function ')
        exit(0)

    def sendToServer(self):
        """ Write the message and send it to the server """
        
        # Get the msg from the text field in the GUI
        message = f"{self.name}: {self.inputArea.get('1.0', 'end')}"

        if (self.name in doctors_names):
            # If the sender is a doctor:
            self.doctor_scenario_flag = 1
            # Put the patient's name (reciever) in the message header
            patient_name = f'{self.dropdownItem.get()}'.encode('utf-8')
            patient_name_header = f"{len(patient_name):<{HEADER_LENGTH}}".encode(
                'utf-8')
        else:
            # If the sender is a patient:
            self.doctor_scenario_flag = 0
            # Put the doctors's type (reciever) in the message header
            if (r.get() == 1):
                # If radiobutton1 (Psychiatrists) is selected
                doctor_type = 'A'.encode('utf-8')
                doctor_type_header = f"{len(doctor_type):<{HEADER_LENGTH}}".encode(
                    'utf-8')
            else:
                # If radiobutton2 (Cardiologists) is selected
                doctor_type = 'B'.encode('utf-8')
                doctor_type_header = f"{len(doctor_type):<{HEADER_LENGTH}}".encode(
                    'utf-8')
        
        
        # If message is not empty - send it
        if message:
            # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
            message = message.encode('utf-8')
            message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
            # Send the msg to the server
            if(self.doctor_scenario_flag):
                self.client_socket.send(message_header + message)
                self.client_socket.send(patient_name_header + patient_name)
            else:
                self.client_socket.send(message_header + message)
                self.client_socket.send(doctor_type_header + doctor_type)

            self.inputArea.delete('1.0', 'end')

    def receiveFromServer(self):
        """ Receive messages from other clients in the server and handle all errors. """
        while self.running:
            try:
                # Each msgs consists of four chunks ==> user['header'] + user['data'] + message['header'] + message['data']
                # We receive each one of them separately and combine them into a single message.
                self.username_header = self.client_socket.recv(
                    HEADER_LENGTH)

                # If we received no data, server will automatically close the connection
                if not len(self.username_header):
                    print('Connection closed by the server')
                    self.stop()

                # Convert header to int value
                self.username_length = int(
                    self.username_header.decode('utf-8').strip())

                # Receive and decode username
                self.username = self.client_socket.recv(
                    self.username_length).decode('utf-8')

                # We do the same for message
                message_header = self.client_socket.recv(HEADER_LENGTH)
                message_length = int(
                    message_header.decode('utf-8').strip())
                message = self.client_socket.recv(
                    message_length).decode('utf-8')

                # Update textarea
                self.textArea.config(state='normal')
                self.textArea.insert('end', message)
                self.textArea.yview('end')
                self.textArea.config(state='disabled')

            except IOError as e:
                # This is normal on non blocking connections - when there are no incoming data error is going to be raised
                # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
                # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
                # If we got different error code - something happened
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error: {}'.format(str(e)))
                    sys.exit()

                # We just did not receive anything
                continue

            except Exception as e:
                # Any other exception - something happened, exit
                print('Reading error: {}'.format(str(e)))
                sys.exit()


client = Client(HOST, PORT)
