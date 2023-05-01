from time import sleep
import socket
import threading
import queue

#CONSTANTES
TCP_IP = '127.0.0.1'
TCP_PORT = 8888
BUFFER_SIZE = 1024

def ListenServer(ServerSocket,q):
    while True:
        try:
            data = ServerSocket.recv(BUFFER_SIZE).decode("UTF-8")
            print("\n"+data)
            #q.put(data)
        except:
             break
    return
    #finalizar

def StartClient():
    ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ServerSocket.connect((TCP_IP, TCP_PORT))
    q = queue.Queue()
    #Hilo para escuchar servidor
    serverThread = threading.Thread(target=ListenServer, args=(ServerSocket,q,))
    serverThread.start()
    while True:
        msg = input("Ingrese su mensaje: ")
        if(msg ==""):
            break
        ServerSocket.sendall(msg.encode("UTF-8"))
    ServerSocket.close()


if __name__ == '__main__':
    StartClient()