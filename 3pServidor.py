from time import sleep
import socket
from threading import Thread
import queue
import select

#CONSTANTES
TCP_IP = '127.0.0.1'
TCP_PORT = 8888
BUFFER_SIZE = 1024
DEBUG = False #ignorar

class Client(Thread):
    def __init__(self,conn,addr,serverSocket):
        super().__init__()
        self.connection = conn
        self.address = addr
        self.msgReceived = False #Variable para revisar si se ha recibido un mensaje
        self.message = ""
        self.serverSocket = serverSocket
    
    def run(self):
        self.Client_Connection()
    
    def Client_Connection(self):
        while True:
            ready = select.select([self.connection], [], [], 1)
            if ready[0]:
                try:
                    data = self.connection.recv(BUFFER_SIZE).decode("UTF-8")
                    if not data:
                        break
                    #mostrar dato recibido
                    msg = f"{self.address[0]}:{self.address[1]} dice: " + data
                    print(f'received: {msg}')
                    self.message = data
                    self.msgReceived = True
                except:
                    #Error de conexion
                    print('Error de conexion')
                    break
        self.End_Client()#Terminar cliente
    
    def End_Client(self):
        self.connection.shutdown(2)    # 0 = done receiving, 1 = done sending, 2 = both
        self.connection.close()
        print(f"Se fue {self.address[0]}:{self.address[1]}")
    def Client_Msg_Queued(self):
        self.msgReceived = False
        self.message = ""
    def Client_Send_Msg(self,message):
        try:
            self.connection.sendall(message.encode("UTF-8"))
        except:
            print("Error enviando mensaje")

class Server():
    def __init__(self, **kwargs):
        # Crear un socket del servidor
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind((TCP_IP, TCP_PORT))
        self.serverSocket.listen()
        print("Servidor escuchando puerto "+str(TCP_PORT)+"...")
        self.q = queue.Queue() #Cola compartida
        self.clients = []
        broadcastThread = Thread(target=self.Broadcast)
        broadcastThread.start()    
        self.Server_Listen()

    def Server_Listen(self):
        while True:
            # Aceptar conexiones entrantes
            clientConn, clientAddress = self.serverSocket.accept()
            print(f"Conexion de {clientAddress[0]}:{clientAddress[1]}")
            #Se inicia un hilo con la conexion del cliente nuevo
            client = Client(conn=clientConn,addr=clientAddress,serverSocket=self.serverSocket)
            client.start()
            self.clients.append(client) #Se agrega el cliente a una lista
            print(self.clients)

    def Check_Command(self,data):
        #if data == $comando: hacer algo
        return

    #Funcion para revisar periodicamente si se ha recibido mensaje de algun cliente
    def Check_Client_Messages(self):
        for client in self.clients:
            if not (client.is_alive()):
                #Revisar si el cliente aun esta conectado, sino se elimina
                self.clients.remove(client)
                #print(self.clients)
                continue
            if (client.msgReceived):
                self.Check_Command(client.message)#Ejemplo para revisar los comandos?
                #Si algun cliente ha recibido mensaje, se agrega a la cola
                data = f"{client.address[0]}:{client.address[1]} dice: " + client.message
                self.q.put(data)
                client.Client_Msg_Queued()

    #Funcion para enviar mensajes recibidos a todos los clientes conectados
    def Broadcast(self):
        while True:
            self.Check_Client_Messages()
            if(self.q.empty()):
                #Si la cola esta vacia, no se hace nada
                continue
            data = self.q.get()
            # Enviar datos procesados a los clientes
            try:
                for client in self.clients:
                    try:
                        client.Client_Send_Msg(data)#linea para enviar mensajes al cliente
                    except socket.error:
                        print("Error enviando mensaje a "+client.address)
                self.q.task_done()
                #Se elimina el mensaje ya enviado, de la cola
            except:break

if __name__ == '__main__':
    Server()