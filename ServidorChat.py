from time import sleep
import socket
from threading import Thread
import queue
import select
import sqlite3 
from datetime import datetime

#CONSTANTES

TCP_IP = '192.168.100.117'
#TCP_IP = '127.0.0.1'
TCP_PORT = 8888
BUFFER_SIZE = 1024
DATABASE = "database/chat.db"
DEBUG = False #ignorar

class Client(Thread):
    def __init__(self,conn,addr,serverSocket):
        super().__init__()
        self.connection = conn
        self.address = addr
        self.msgReceived = False #Variable para revisar si se ha recibido un mensaje
        self.message = ""
        self.serverSocket = serverSocket
        self.room = "Default"  # Al inicio, el cliente no está en ninguna sala
        self.nickname = None  # Se establecerá después de recibir el primer mensaje
        self.room_list = []
        self.username = None #Nombre de Usuario
        self.room = "Default"
            
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
                    print('>>Error de conexion')
                    break
        self.End_Client()#Terminar cliente
    
    def End_Client(self):
        self.connection.shutdown(2)    # 0 = done receiving, 1 = done sending, 2 = both
        self.connection.close()
        print(f"Se fue {self.address[0]}:{self.address[1]}")
    def Client_Clear_Msg(self):
        self.msgReceived = False
        self.message = ""
    def Client_Send_Msg(self,message):
        try:
            self.connection.sendall(message.encode("UTF-8"))
        except:
            print(">>Error enviando mensaje")
             
class Server():
    def __init__(self, **kwargs):
        # Crear un socket del servidor
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind((TCP_IP, TCP_PORT))
        self.serverSocket.listen()
        self.Create_Data_Base()#Crear tabla si no existe
        print(">>Servidor escuchando puerto "+str(TCP_PORT)+"...")
        self.q = queue.Queue() #Cola compartida
        self.clients = []
        self.rooms = [["Default","default",0]]
        broadcastThread = Thread(target=self.Broadcast)
        broadcastThread.start()   
        self.Server_Listen()
    
    def Server_Listen(self):
        while True:
            # Aceptar conexiones entrantes
            clientConn, clientAddress = self.serverSocket.accept()
            print(f">>Conexion de {clientAddress[0]}:{clientAddress[1]}")
            #Se inicia un hilo con la conexion del cliente nuevo
            client = Client(conn=clientConn,addr=clientAddress,serverSocket=self.serverSocket)
            client.start()
            serverTime = self.Get_Time()
            client.Client_Send_Msg("Reloj»"+serverTime)
            self.rooms[0][2] +=1
            self.clients.append(client) #Se agrega el cliente a una lista
            if(DEBUG):print(self.clients)
            
    def Check_Command(self, client):
        listedData = client.message.split("»")
        command = listedData[0]
        #Login
        if command.startswith("#login"):
            if(len(listedData)!=3):
                client.Client_Send_Msg(f"Mensaje»Servidor»Error en comando")
                return True
            self.Login(client)
            return True
        if command.startswith("#register"):
            self.Register(client)
            return True
        #Crear Sala
        if command.startswith("#cR"):
            if(len(listedData)!=2):
                client.Client_Send_Msg(f"Mensaje»Servidor»Error en comando")
                return True
            room_name = listedData[1] # Obtiene el nombre de la sala
            room_exists = False
            i=0
            for room in self.rooms: # Revisa si la sala ya existe
                if room[0] == room_name:
                    room_exists = True
                    self.rooms[i][2]+=1
                    client.Client_Send_Msg(f"Entrar Sala»{room_name}»Ya existe la sala {room_name}, se ha unido automaticamente")
                    break
                i+=1
            if not room_exists:  #Se crea una nueva instancia de la clase Room y se agrega a la lista de salas del servidor
                self.rooms.append([room_name,client.username,1])
                print(f"Sala {room_name} creada por {client.username}")
                client.Client_Send_Msg(f"Entrar Sala»{room_name}»Se ha creado la sala {room_name}")
            i=0
            for room in self.rooms:
                if client.room == room[0]:
                    self.rooms[i][2]-=1
                i+=1
            client.room = room_name    
            return True                 
        # Entrar a sala
        elif command.startswith("#gR"):
            if(len(listedData)!=2):
                client.Client_Send_Msg(f"Mensaje»Servidor»Error en comando")
                return True
            room_name=listedData[1]
            room_exists = False
            i=0
            for room in self.rooms:
                if room[0] == room_name:
                    room_exists = True
                    self.rooms[i][2] +=1
                    j=0
                    for r in self.rooms:
                        if r[0]==client.room:
                            self.rooms[j][2]-=1
                        j+=1
                    client.room = room_name
                    client.Client_Send_Msg(f"Entrar Sala»{room_name}»Se ha unido a la sala {room_name}")       
                    return True
                i+=1
            client.Client_Send_Msg(f"Mensaje»Servidor»No existe la sala {room_name}")
            return True
        #Salir de Sala
        elif(command.startswith("#eR")):
            i=0
            for room in self.rooms:
                if client.room == room[0]:
                    self.rooms[i][2]-=1
                    break
                i+=1
            self.rooms[0][2]+=1
            client.room = "Default"
            client.Client_Send_Msg(f"Salir Sala»Ha salido a la sala principal")
            return True
        #Salir del Servidor                    
        elif command.startswith("#exit"):
            client.End_Client() # Cerrar el socket del cliente
            return True
        #Lista de Nombres de Salas
        elif command.startswith("#lR"):
            client.Client_Send_Msg("Mensaje»Servidor»"+self.List_Rooms())
            return True
        #Eliminar Sala
        elif command.startswith('#dR'):
            if(len(listedData)!=2):
                client.Client_Send_Msg(f"Mensaje»Servidor»Error en comando")
                return True
            room_name=listedData[1]
            i=0
            for room in self.rooms:
                if room[0] == room_name:
                    if room[1]==client.username:
                        if room[2]>0:
                            client.Client_Send_Msg("Mensaje»Servidor»No se puede eliminar sala, no esta vacia")
                        else:
                            client.Client_Send_Msg(f"Mensaje»Servidor»Se ha eliminado la sala {room_name}")
                            self.rooms.remove(room)
                        return True
                    client.Client_Send_Msg("Mensaje»Servidor»No se puede eliminar sala, no fue creada por su usuario")
                    return True
                i+=1
            client.Client_Send_Msg("Mensaje»Servidor»No se puede eliminar sala, no existe")
            return True
        #Mostrar Usuarios
        elif command.startswith('#show users'):
            msg = self.Show_Users()
            client.Client_Send_Msg("Mensaje»Servidor»"+msg)
            return True
        #Mensaje Privado
        elif command.startswith('\private'):
            if(len(listedData)!=3):
                client.Client_Send_Msg(f"Mensaje»Servidor»Error en comando")
                return True
            username = listedData[1]# Extraer el nombre de usuario del mensaje
            recipient = None
            for cl in self.clients: #Encontrar el objeto cliente correspondiente al usuario
                if cl.username == username:
                    recipient = cl
                    break
            # Verificar si se encontró al usuario
            if recipient:
                # Enviar mensaje privado al usuario
                recipient.Client_Send_Msg(f"Privado»{client.username}»{listedData[2]}")
                client.Client_Send_Msg(f"Mensaje»Servidor»Se ha enviado el mensaje")
            else:
                client.Client_Send_Msg(f"Mensaje»Servidor»El usuario no existe")
            return True

    #Funcion para revisar periodicamente si se ha recibido mensaje de algun cliente
    def Check_Client_Messages(self):
        for client in self.clients:
            if not (client.is_alive()):
                #Revisar si el cliente aun esta conectado, sino se elimina
                i=0
                for room in self.rooms:
                    if client.room == room[0]:
                        self.rooms[i][2]-=1
                        break
                    i+=1
                self.clients.remove(client)
                continue
            if (client.msgReceived):
                if(self.Check_Command(client)):
                    client.Client_Clear_Msg()
                    continue#Revisar si hay un comando
                #Si algun cliente ha recibido mensaje, se agrega a la cola
                data = f"{client.username}»" + client.message
                self.q.put([client.room,data,client.username])
                client.Client_Clear_Msg()

    #Funcion para enviar mensajes recibidos a todos los clientes conectados
    def Broadcast(self):
        self.conn = sqlite3.connect(DATABASE)
        self.cur = self.conn.cursor()
        while True:
            self.Check_Client_Messages()
            if(self.q.empty()):
                #Si la cola esta vacia, no se hace nada
                continue
            data = self.q.get() 
            # Enviar datos procesados a los clientes de la Sala
            try:
                for client in self.clients:
                    if(client.room != data[0]):continue
                    if(client.username == data[2]):continue
                    try:
                        client.Client_Send_Msg("Mensaje»"+data[1])#linea para enviar mensajes al cliente
                    except socket.error:
                        print(">>Error enviando mensaje a "+client.address)
                self.q.task_done()
                #Se elimina el mensaje ya enviado, de la cola
            except:break
        self.conn.close()
    #mostrar todos los usuarios conectados al servidor
    def Show_Users(self):
        users = []
        for client in self.clients:
            users.append(client.username)
        msg = ""
        print(">>Usuarios conectados: ")
        for user in users:
            msg = msg + user + ", \n"
            print("\n")
            print(user)
        return msg

    #Función para listar todas las salas y sus usuarios
    def List_Rooms(self):
        msg=""
        for room in self.rooms:
            msg = msg + f"Sala: {room[0]}, Usuarios: {room[2]}, \n"
        return msg
    
    def Login(self, client):
        if client.username is not None:
            client.Client_Send_Msg("Mensaje»Server»Ya has iniciado sesion.")
            return
        message = client.message.split("»")
        user = message[1]
        pwd = message[2]
        # Verificar si el nombre de usuario ya está en uso
        for c in self.clients:
            if c.username == user:
                client.Client_Send_Msg("Login»0»El nombre de usuario ya esta en uso.")
                return
        # Asignar el nombre de usuario al cliente y enviar un mensaje de confirmación
        res = self.cur.execute("SELECT login,password FROM users WHERE login=? AND password=?",(user,pwd,))
        if(res.fetchone() is None):
            client.Client_Send_Msg("Login»0»Credenciales incorrectos")
            return
        else:
            client.username = user
            client.Client_Send_Msg("Login»1»Sesion iniciada correctamente")
            return
    
    def Register(self,client):
        listedData = client.message.split("»")
        names = listedData[1]
        lastnames = listedData[2]
        user = listedData[3]
        password = listedData[4]
        age = listedData[5]
        gender = listedData[6]
        res = self.cur.execute("SELECT login FROM users WHERE login=?",(user,))
        if(res.fetchone() is not None):
            client.Client_Send_Msg("Registrar»0»Ya existe una cuenta con ese usuario")
            return
        # Insertar información del usuario en la base de datos
        self.cur.execute("INSERT INTO users (nombres, apellidos, login, password, edad, genero) VALUES (?, ?, ?, ?, ?, ?)",
            (names, lastnames, user, password, age, gender,))
        self.conn.commit()
        client.Client_Send_Msg("Registrar»1»Se ha registrado la cuenta exitosamente")

    def Get_Time(self):
        now = datetime.now()
        time = f"{now.hour}»{now.minute}»{now.second}"
        return time
    
    def Create_Data_Base(self):
        # Crear conexión a la base de datos
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        # Crear tabla 'users' si no existe
        cur.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombres VARCHAR(100),
                        apellidos VARCHAR(100),
                        login VARCHAR(100),
                        password VARCHAR(100),
                        edad INTEGER,
                        genero VARCHAR(100))''')
        conn.close()

if __name__ == '__main__':
    Server()