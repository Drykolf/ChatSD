from time import sleep
import socket
import threading
import queue

#CONSTANTES
TCP_IP = '127.0.0.1'
TCP_PORT = 8888
BUFFER_SIZE = 1024

def Client(clientConn,clientAddress,q):
    # Código para manejar la conexión con el cliente
    while True:
        try:
          data = clientConn.recv(BUFFER_SIZE).decode("UTF-8")
        except:break
        msg = f"{clientAddress[0]}:{clientAddress[1]} dice: " + data
        print(msg)
        q.put(msg)
    clientConn.close()
    print(f"Se fue {clientAddress[0]}:{clientAddress[1]}")

def SubClient(clients,q):
    while True:
        if(q.empty()):
            continue
        data = q.get()
        # Enviar datos procesados a los clientes
        try:
            for clientCx in clients:
                clientCx.sendall(data.encode("UTF-8"))
            q.task_done()
        except:break

def StartServer():
    # Crear un socket del servidor
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((TCP_IP, TCP_PORT))
    serverSocket.listen()
    print("Servidor escuchando puerto "+str(TCP_PORT)+"...")
    q = queue.Queue() #Cola compartida
    clients = []
    while True:
        # Aceptar conexiones entrantes
        clientConn, clientAddress = serverSocket.accept()
        print(f"Conexion de {clientAddress[0]}:{clientAddress[1]}")
        clients.append(clientConn)
        # Crear un hilo para manejar la conexión con el cliente
        clientThread = threading.Thread(target=Client, args=(clientConn,clientAddress,q,))
        clientThread.start()
        subClientThread = threading.Thread(target=SubClient, args=(clients,q,))
        subClientThread.start()

if __name__ == '__main__':#comentario
    StartServer()