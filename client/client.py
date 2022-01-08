import socket
import pathlib, sys

current_directory = str(pathlib.Path(__file__).parent.parent.absolute())
new_path = current_directory + '/protocol'
sys.path.append(new_path)
from MessageProtocol import MessageProtocol

HEADER = 1024
PORT = 6066
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "127.0.1.1"
ADDR = (SERVER, PORT)


class Client():

    ######################Client Dynamic Messages############################
    def username_msg(self, username):
        return MessageProtocol('Username', username).encode()

    def chair_msg(self, number):
        return MessageProtocol('Chair', str(number)).encode()
    #########################################################################


    def __init__(self):
        ######################Client Constant Messages############################
        self.game_start_msg = MessageProtocol('Start', "Start").encode()

        self.ready_msg = MessageProtocol('Ready', "Ready").encode()
        #########################################################################

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Stage 5 - spectate
    def spectate(self):
        while (True):
            received_msg = self.get()
            print(received_msg.message)
            if received_msg.type == 'GameResult':
                return

    # Stage 4 - game
    def game(self):
        self.send(self.ready_msg)

        while(True):

            chairs = self.get()
            print(chairs.message)
            print(" ")
            print("Get ready to get your chair:")
            while(True):
                recieved_msg = self.get()
                if recieved_msg.type == 'Wait':
                    if recieved_msg.message == '•Play':
                        print('•')
                        break
                    print(recieved_msg.message)
                else:
                    #print(recieved_msg.message, end="")
                    break

            while (True):
                input_info = input("Choose your chair: ")
                try:
                    chair_number = int(input_info)
                except ValueError:
                    print("You should write the number of the chair")
                    continue

                self.send(self.chair_msg(chair_number))
                answer = self.get()
                if answer.message == "\033[93m"+"This chair is already occupied"+"\033[0m"+"Lost":
                    print("This chair is already occupied.\n\nAll chairs are occupied, so you lost :(")
                    return 'Spectate'
                elif answer.message == "\033[93m"+"This chair doesn't exist"+"\033[0m"+"Lost":
                    print("This chair doesn't exist.\n\nAll chairs are occupied, so you lost :(")
                    return 'Spectate'


                else:
                    print(answer.message)

                if answer.type == 'Accepted':
                    break
                else:
                    received = self.get()
                    print(" ")
                    print(received.message)

                    if received.type == 'Lost':
                        return 'Spectate'

            print("")
            new_round = self.get()
            print(new_round.message)
            if new_round.type == 'GameResult':
                return 'End'

        return



    # Stage 3.1(only for admins) - start game
    def game_start(self):
        while(True):
            print(" ")
            input_info = input("Enter 'Start' when you are ready to play... ")
            if input_info == 'Start':
                self.send(self.game_start_msg)
                received = self.get()
                print(" ")
                print(received.message)
                if received.type == 'Accepted':
                    break
        return

    #Stage 3 - greeting
    def greeting(self):
        received = self.get()

        print(received.message)
        if received.type == 'Admin':
            self.game_start()
        else:
            received = self.get()
            print(" ")
            print(received.message)
        return

    #Stage 2 - authorization
    def authorization(self):
        while (True):
            print(" ")
            input_info = input("Enter your username: ")
            self.send(self.username_msg(input_info))
            received = self.get()
            print(received.message)
            print(" ")
            if received.type == 'Accepted':
                break
        return




    def main(self):
        #Stage 1 - connection
        self.sock.connect(ADDR)
        #Stage 2 - authorization
        self.authorization()
        #Stage 3 - greeting
        self.greeting()
        # Stage 4 - game
        game_result = self.game()
        # Stage 5 - spectate
        #if game_result == 'Spectate':
        #    self.spectate()


        return

    def send(self, message):
        self.sock.send(message)

    # def send(self, type, message):
    #     self.sock.send(MessageProtocol(type, message).encode())

    def get(self):
        return MessageProtocol().decode(self.sock.recv(2048))




    # def send(message1):
    #     msg = MessageProtocol('message', message1)
    #     message = msg.encode())
    #     client.send(message)



##########
client = Client()
client.main()

