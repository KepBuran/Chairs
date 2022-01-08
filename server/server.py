import socket
import threading
import pathlib, sys, os
import time
import random
import signal
import psutil

current_directory = str(pathlib.Path(__file__).parent.parent.absolute())
new_path = current_directory + '/protocol'
sys.path.append(new_path)
from MessageProtocol import MessageProtocol
# from protocol.MessageProtocol import MessageProtocol

#####SETTINGS#########
HEADER = 1024
PORT = 6066
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
MAX_ROUND_WAIT = 5


class Server():
    ######################Server Dynamic Messages############################
    def all_chairs_message(self):
        string = "  "
        for i in range(len(self.chairs)):
            if self.chairs[i]:
                string = string + str(i+1) + " "
        return MessageProtocol('Chairs', "There are all free chairs:\n"+string).encode()

    def round_result_msg(self):
        string = "\033[4m"+self.kicked_players[-1][2]+" didn't find free chair."+"\033[0m"+"\n\n\t"+"\033[92m"+"Round "+str(self.round_counter)+"\033[0m"
        return MessageProtocol('RoundResult', string).encode()

    def game_result_msg(self):
        return MessageProtocol('GameResult', "\033[92m"+"\t"+self.active_players[0][2] + " won!!!"+"\033[0m"+"\nThank you for playing Chairs game. See you soon...").encode()
    #################################################################

    def __init__(self):
        ######################Server Constant Messages############################
        self.username_acception_msg = MessageProtocol('Accepted', "From now you will be known by this username.").encode()
        self.username_rejection_msg = MessageProtocol('Rejected', "This username is already used by another player.").encode()

        self.greeting_admin_msg = MessageProtocol('Admin', "Hello! Welcome to Chairs game!\nYou are first player to join, so are main user now!").encode()
        self.greeting_user_msg = MessageProtocol('User', "Hello! Welcome to Chairs game!\nPlease wait for the start of the game...").encode()

        self.game_start_rejection_amount_msg = MessageProtocol('Rejected', "There are should be 2 players or more!").encode()
        self.game_start_rejection_auth_msg = MessageProtocol('Rejected', "Wait for all users to authorize!").encode()
        self.game_start_acception_msg = MessageProtocol('Accepted', "Starting Game").encode()

        self.round_wait_msg = MessageProtocol('Wait', "•").encode()
        self.round_play_msg = MessageProtocol('Play', "Choose your chair: ").encode()

        self.chair_acception_msg = MessageProtocol('Accepted',"\033[92m"+"Chair successfuly occupied by you!"+"\033[0m").encode()
        self.chair_rejection_exist_msg = MessageProtocol('Rejected', "\033[93m"+"This chair doesn't exist"+"\033[0m").encode()
        self.chair_rejection_occupied_msg  = MessageProtocol('Rejected', "\033[93m"+"This chair is already occupied"+"\033[0m").encode()

        self.lost_msg = MessageProtocol('Lost', "\033[91m"+"All chairs are occupied, so you lost :("+"\033[0m").encode()
        #################################################################



        #######################Server attributes###########################
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(ADDR)

        self.round_counter = 1
        self.auth = []
        self.ready_status = []
        self.usernames = []
        self.admin = None
        self.game_started = False

        self.chairs = []
        self.active_players = []
        self.kicked_players = []

        self.round_in_procces = False
        self.game_end = False
        ##################################################################


    def game(self):
        while (True):
            time.sleep(0.1)
            if self.game_started:
                break

        while (True):
            time.sleep(0.1)
            if (not (False in self.ready_status)) and (len(self.ready_status) >= 1):
                break

        print(f"[GAME START] All users are ready.")


        while(True):
            time.sleep(2)
            self.chairs = [True] * (len(self.active_players) - 1)
            for player in self.active_players:
                player[0].send(self.all_chairs_message())
            time.sleep(1)
            wait_seconds = random.randint(2, MAX_ROUND_WAIT)

            if len(self.active_players) == 1:
                print(f"[GAME END] Game successfuly ended.")
                self.game_end = True
                break

            print(f"[NEW ROUND] Starting round {self.round_counter}.")


            while (wait_seconds>0):
                time.sleep(1)
                for player in self.active_players:
                    player[0].send(self.round_wait_msg)
                wait_seconds = wait_seconds - 1

            for player in self.active_players:
                player[0].send(self.round_play_msg)

            self.round_in_procces = True

            while(True):
                if not self.round_in_procces:
                    break

            if len(self.active_players) == 1:
                self.game_end = True
                game_result_msg = self.game_result_msg()
                for player in self.active_players:
                    player[0].send(game_result_msg)
                    #player[0].close()
                #for player in self.kicked_players:
                #    player[0].send(game_result_msg)
                #    player[0].close()
                current_system_pid = os.getpid()

                ThisSystem = psutil.Process(current_system_pid)
                ThisSystem.terminate()
                return

            else:
                round_result_msg = self.round_result_msg()
                for player in self.active_players:
                    player[0].send(round_result_msg)
                #for player in self.kicked_players:
                #    player[0].send(round_result_msg)



    def game_client(self, conn, addr, username):
        while(True):
            time.sleep(0.1)
            if self.game_started:
                break

        self.send(conn, 'Accepted', '\033[92m'+'     Game started!\n\tRound 1'+'\033[0m')
        self.active_players.append([conn, addr, username])
        index = len(self.ready_status)
        self.ready_status.append(False)
        received = self.get(conn)

        if received.type == 'Ready':
            self.ready_status[index] = True


        while(True):
            while(True):
                if self.round_in_procces:
                    break

            if self.game_end:
                return

            while(True):
                try:
                    received_chair = self.get(conn)
                except IndexError:
                    return
                chair_number = int(received_chair.message)
                chair_index = chair_number-1
                if (chair_index <= -1) or (chair_index >= len(self.chairs)):
                    conn.send(self.chair_rejection_exist_msg)
                    if True in self.chairs:
                        time.sleep(0.01)
                        conn.send(self.all_chairs_message())
                    else:
                        self.round_counter = self.round_counter + 1
                        conn.send(self.lost_msg)
                        lost_id = 0
                        for i in range(len(self.active_players)):
                            if self.active_players[i][1] == addr:
                                lost_id = i
                        self.kicked_players.append(self.active_players.pop(lost_id))
                        self.chairs.pop()
                        self.round_in_procces = False
                        return

                else:
                    if self.chairs[chair_index]:
                        self.chairs[chair_index] = False
                        conn.send(self.chair_acception_msg)
                        break
                    else:
                        conn.send(self.chair_rejection_occupied_msg)
                        if True in self.chairs:
                            time.sleep(0.01)
                            conn.send(self.all_chairs_message())
                        else:
                            conn.send(self.lost_msg)
                            self.round_counter = self.round_counter+1
                            lost_id = 0
                            for i in range(len(self.active_players)):
                                if self.active_players[i][1] == addr:
                                    lost_id = i
                            self.kicked_players.append(self.active_players.pop(lost_id))
                            self.chairs.pop()
                            self.round_in_procces = False
                            return



        return



    #Stage 3 - greeting
    def greeting(self, conn, addr):

        if self.admin == addr:
            conn.send(self.greeting_admin_msg)
            connected = True
            while connected:

                msg = MessageProtocol().decode(conn.recv(HEADER))
                if msg.message == DISCONNECT_MESSAGE:
                    connected = False

                if msg.type == 'Start':
                    if (threading.activeCount() - 2) <= 1:
                        print("[GAME START CANCELLED] admin tried to init game, but there are not enough players")
                        conn.send(self.game_start_rejection_amount_msg)
                    elif False in self.auth:
                        print("[GAME START CANCELLED] admin tried to init game, but some players are not authorized yet")
                        conn.send(self.game_start_rejection_auth_msg)
                    else:
                        print("[GAME START] admin started game.")
                        self.game_started = True
                        # conn.send(self.game_start_acception_msg)
                        # self.game_client(conn, addr)
                        break
        else:
            conn.send(self.greeting_user_msg)
            return
        return



    #Stage 2 - authorization
    def authorization(self, conn, addr):

        index = len(self.auth)
        self.auth.append(False)
        while (True):
            received = self.get(conn)
            if received.message in self.usernames:
                print(f"[AUTHORIZATION FAILED] {addr} is not authorized, because {received.message} is already used by another user.")
                conn.send(self.username_rejection_msg)
            else:
                if len(self.usernames) == 0:
                  self.admin = addr
                self.usernames.append(received.message)
                conn.send(self.username_acception_msg)
                print(f"[NEW AUTHORIZATION] {addr} will be known as {received.message}.")
                self.auth[index] = True
                return received.message


    def main_client(self, conn, addr):
        print(f"[NEW CONNECTION] {addr} connected.")
        username = self.authorization(conn, addr)

        #print(f"[STAGE 2] {addr}")
        self.greeting(conn, addr)

        self.game_client(conn, addr, username)

        #print(f"[CLOSING] {addr}")
        #conn.close()
        print(f"[LIFECYCLE ENDED] {username} {addr}.")


    def main_spectator(self, conn, addr):
        pass

    #Stage 1 - connection
    def start(self):
        self.sock.listen()
        print(f"[LISTENING] Server is listening on {SERVER}")
        thread = threading.Thread(target=self.game)
        thread.start()

        while True:
            if not self.game_started:
                conn, addr = self.sock.accept()
                if self.game_started:
                    conn.close()
                    break
                if (threading.activeCount() - 2) == 0:
                    self.admin = addr

                thread = threading.Thread(target=self.main_client, args=(conn, addr))
                thread.start()
                print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 2}")
            else:
                break

        print(f"[STOPPED LISTENING] Server stoped listening due to start of the game")

        while True:
            if self.game_end:
                print(f"[SERVER STOP] Server is shutting down")
                break
        return



    def send(self, conn, type, message):
        conn.send(MessageProtocol(type, message).encode())

    def get(self, conn):
        return MessageProtocol().decode(conn.recv(1024))


# if name == 'main':
print("[STARTING] server is starting...")
server = Server()
server.start()