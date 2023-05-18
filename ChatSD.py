import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.properties import DictProperty, ListProperty, StringProperty
# to use buttons:
from kivy.uix.button import Button
#Conexion
from time import sleep
import time
import socket
import threading
import queue
import select

#CONSTANTES
#TCP_IP = '192.168.86.44'
TCP_IP = "127.0.0.1"

TCP_PORT = 8888
BUFFER_SIZE = 1024
DEFAULT_ROOM="Sala Principal"
SCREENS =["Login","Register","Chat","Informacion","InformacionBoton"]

class ScrollableLabel(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_scroll_x = False
        self.needToScroll = False
        self.scroll_y = 1
        self.layout = GridLayout(cols=1, spacing=10,size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.add_widget(self.layout)
        self.chatHistory = Label(size_hint_y=None,markup=True)
        self.scrollToPoint = Label()
        self.layout.add_widget(self.chatHistory)
        self.layout.add_widget(self.scrollToPoint)

    def Update_Chat_History(self, message):
        self.chatHistory.text += "\n" + message
        self.layout.height = self.chatHistory.texture_size[1]+15
        self.chatHistory.height = self.chatHistory.texture_size[1]
        self.chatHistory.text_size = (self.chatHistory.width*0.98,None)
        if(self.needToScroll):self.scroll_to(self.scrollToPoint)
        

class ChatPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.username = "JBarco"
        self.room = DEFAULT_ROOM
        t = time.localtime()
        self.localTime = time.strftime("%H:%M:%S", t)
        self.cols = 1
        self.rows = 3
        #Nombre de sala y hora compartida
        self.roomNameLbl = Label(text=self.room)
        self.serverTime = Label(text=self.localTime,size_hint_x=0.2)
        topLine = GridLayout(cols=2,size_hint_y=.1)
        topLine.add_widget(self.roomNameLbl)
        topLine.add_widget(self.serverTime)
        self.add_widget(topLine)
        #Label para el chat
        self.historyLbl = ScrollableLabel()
        self.add_widget(self.historyLbl)
        #Entrada de texto y boton enviar
        self.newMessageTxt = TextInput(multiline = False)
        self.sendBtn = Button(text="Enviar",size_hint_x=0.2)
        self.sendBtn.bind(on_press=self.Send_Message)
        bottomLine = GridLayout(cols=2,size_hint_y=.1)
        bottomLine.add_widget(self.newMessageTxt)
        bottomLine.add_widget(self.sendBtn)
        self.add_widget(bottomLine)
        Window.bind(on_key_down=self.on_key_down)

    def on_key_down(self, instance, keyboard, keycode, text, modifiers):
        if keycode == 40:
            self.Send_Message(None)
    
    def Send_Message(self, _):
        #print("enviar mensaje")
        message = self.newMessageTxt.text
        self.newMessageTxt.text = ""
        if message:
            self.historyLbl.Update_Chat_History(f"[color=dd2020]{self.username}[/color] > {message}")
            if(self.historyLbl.height-5 <= self.historyLbl.layout.height): self.historyLbl.needToScroll = True
            else: self.historyLbl.needToScroll = False
            #socket enviar mensaje
            chatApp.ServerSocket.sendall(message.encode("UTF-8"))
        Clock.schedule_once(self.Focus_Text_Input,0.1)

    def Focus_Text_Input(self, _):
        self.newMessageTxt.focus = True

    def Incoming_Message(self, username, message, whisper = False):
        if not whisper:
            self.historyLbl.Update_Chat_History(f"[color=20dd20]{username}[/color] > {message}")
        else:            
            self.historyLbl.Update_Chat_History(f"[color=9b20dd]Mensaje privado de {username}[/color] > {message}")

    def Change_Room(self,message,room="Default"):
        #PENDIENTE ARREGLAR
        if(room == "Default"):                
            self.room = DEFAULT_ROOM
        elif(self.room == room):
            #Ya esta en esta sala
            return
        else: self.room = room
        self.roomNameLbl.text = room
        self.historyLbl.text = ""
        #mostrar mensaje del servidor
        #enviar mensaje de entrada a todos
        self.historyLbl.Update_Chat_History(f"[color=20dd20]{self.username}[/color] ha entrado a la sala")
    
    def Delete_Room(self, message, room):
        if(room == self.room):#Si se elimina la sala en la que esta, se sale
            self.Change_Room(message)
        else:
            #Mostrar mensaje sala eliminada
            return


class LoginPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 2
        self.add_widget(Label(text="IP: " + TCP_IP))
        self.add_widget(Label(text="Puerto: " + str(TCP_PORT)))
        self.add_widget(Label(text="Usuario: "))
        self.userTxt = TextInput(multiline=False)
        self.add_widget(self.userTxt)
        self.add_widget(Label(text="Contraseña: "))
        self.passwordTxt = TextInput(multiline=False)
        self.add_widget(self.passwordTxt)
        self.loginBtn = Button(text="Conectarse")
        self.loginBtn.bind(on_press=self.Login)
        self.add_widget(self.loginBtn)
        self.signup = Button(text="Crear Cuenta")
        self.add_widget(self.signup)
        self.username = chatApp.username
    
    def Register(self, instance):
        return
    def Login(self, instance):
        self.username = self.userTxt.text
        info = f"Intentando iniciar como {self.username}"
        password = self.passwordTxt.text
        chatApp.ServerSocket.sendall(f"#login {self.username} {password}".encode("UTF-8"))
        print(info)
        chatApp.infoPage.Update_Info(info)
        chatApp.screenManager.current = SCREENS[3]
        Clock.schedule_once(self.Connect,1)
    
    def Connect(self,_): 
        if(chatApp.logged):
            chatApp.nextScreen = SCREENS[2]
            print("Sesion iniciada")
        else:
            chatApp.nextScreen = SCREENS[0]
            chatApp.infoBtnPage.Update_Info("Error al iniciar")
            chatApp.screenManager.current = SCREENS[4]
            


class InfoPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.messageLbl = Label(halign='center',valign='middle', font_size=30)
        self.messageLbl.bind(width=self.Update_Text_Width)
        self.add_widget(self.messageLbl)

    def Update_Info(self,message):
        self.messageLbl.text = message

    def Update_Text_Width(self, *_):
        self.messageLbl.text_size = (self.messageLbl.width*0.9,None)
    

class InfoButtonPage(InfoPage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.exit=False
        self.rows = 2
        self.continueBtn = Button(text="OK",size_hint_y=.1,size_hint_x=0.2)
        self.continueBtn.bind(on_press=self.trigger)
        self.add_widget(self.continueBtn)
    
    def trigger(self, instance):
        if self.exit: chatApp.End_Client()
        else: self.Next_Screen()
    def Next_Screen(self):
        chatApp.screenManager.current = chatApp.nextScreen

class ChatSD(App):
    def build(self):
        Window.bind(on_request_close=self.exit_check)
        self.closing = False
        #Variables de usuario
        self.username = "Invitado"
        self.logged = False
        self.screenManager = ScreenManager()
        self.nextScreen = SCREENS[2]
        self.loginPage = LoginPage()
        screen = Screen(name=SCREENS[0])
        screen.add_widget(self.loginPage)
        self.screenManager.add_widget(screen)
        self.infoPage = InfoPage()
        screen = Screen(name=SCREENS[3])
        screen.add_widget(self.infoPage)
        self.screenManager.add_widget(screen)
        self.chatPage = ChatPage()
        screen = Screen(name=SCREENS[2])
        screen.add_widget(self.chatPage)
        self.screenManager.add_widget(screen)
        self.infoBtnPage = InfoButtonPage()
        screen = Screen(name=SCREENS[4])
        screen.add_widget(self.infoBtnPage)
        self.screenManager.add_widget(screen)
        if not (self.Connect_Server()):
            self.End_Client("----------------------Error en conexion--------------------------")
            return
        #Hilo para escuchar servidor
        self.serverThread = threading.Thread(target=self.Listen_Server)
        self.serverThread.start()
        return self.screenManager

    def exit_check(self, *args):
        self.End_Client("Desconectando...")
        return False
    
    def End_Client(self,message="Error"):
        if(self.closing):return
        print(message)
        self.closing=True
        self.ServerSocket.close()
        App.get_running_app().stop()

    def Connect_Server(self):
        #Conexion
        self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.ServerSocket.connect((TCP_IP, TCP_PORT))
            self.ServerSocket.setblocking(0)
            return True
        except:
            return False
        
    def Listen_Server(self):
        while True:
            ready = select.select([self.ServerSocket], [], [], 1)
            if ready[0]:
                try:
                    data = self.ServerSocket.recv(BUFFER_SIZE).decode("UTF-8")
                    self.chatPage.Incoming_Message("Alguien",data)
                    self.chatPage.Change_Room("","Prueba")
                    print(data)
                except:
                    input("Servidor desconectado")
                    self.infoBtnPage.Update_Info("Error: Servidor desconectado"+ 
                                "\n"+"Saliendo de la aplicacion")
                    self.infoBtnPage.exit = True
                    self.screenManager.current = SCREENS[4]
                    break
        return
        #finalizar

    def Check_Message(self,data):
        listedData = data.split("»")
        command = listedData[0]
        results = ["Login","Mensaje","Entrar Sala","Salir Sala","Eliminar Sala","Desconectar",
                   "Privado","noLogin"]
        #register Nombres,Apellidos,Login,Password,Edad,Genero
        #register Jose,Barco Arias,jbarco,1230,24,Hombre
        #login usuario contrasena
        #noLogin»Credenciales incorrectos
        #Login»Iniciado sesion correctamente
        #Mensaje»Klisman»HOla como esta
        #Entrar Sala»Prueba»ha entrado a la sala prueba
        #Salir Sala»Prueba»Ha salido de la sala
        #Eliminar Sala»Prueba»Se ha eliminado sala Prueba
        #Desconectar»Se ha desconectado
        #Privado»Klisman»Hola como estax
        if(command == results[0]):#Iniciar sesion exitosamente
            self.logged = True
            self.username = self.loginPage.username
        elif(command == results[1]):#Mostrar mensaje
            sender = listedData[1]
            message = listedData[2]
            self.chatPage.Incoming_Message(sender,message)
        elif(command == results[2]):#Entrar a sala
            room = listedData[1]
            message = listedData[2]
            self.chatPage.Change_Room(message,room)
        elif(command == results[3]):#Salir de sala a la sala principal
            message = listedData[1]
            self.chatPage.Change_Room(message)#Si no se envia room, se asume la principal
        elif(command == results[4]):#Eliminar una sala
            room = listedData[1]
            message = listedData[2]
            self.chatPage.Delete_Room(message,room)
        elif(command == results[5]):#Desconectar
            self.End_Client("Saliendo de la aplicacion")
        elif(command == results[6]):#Mensaje privado
            sender = listedData[1]
            message = listedData[2]
            self.chatPage.Incoming_Message(sender,message,True)
        elif(command == results[7]):#Login no aceptado
            return
            





if __name__ == '__main__':
    chatApp = ChatSD()
    chatApp.run()
    