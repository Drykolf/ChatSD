import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.properties import DictProperty, ListProperty, StringProperty
# to use buttons:
from kivy.uix.button import Button
#Conexion
from time import sleep
import socket
import threading
import queue

#CONSTANTES
TCP_IP = '127.0.0.1'
TCP_PORT = 8888
BUFFER_SIZE = 1024


class ScrollableLabel(ScrollView):
    def __init__(self, **kwargs):
        self.needToScroll = False
        super().__init__(**kwargs)
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
        self.cols = 1
        self.rows = 2

        self.historyLbl = ScrollableLabel(height = Window.size[1]*0.9, size_hint_y = None)
        self.add_widget(self.historyLbl)

        self.newMessageTxt = TextInput(width=Window.size[0]*0.8, size_hint_x = None, multiline = False)
        self.sendBtn = Button(text="Enviar")
        self.sendBtn.bind(on_press=self.Send_Message)

        bottomLine = GridLayout(cols=2)
        bottomLine.add_widget(self.newMessageTxt)
        bottomLine.add_widget(self.sendBtn)
        self.add_widget(bottomLine)

        Window.bind(on_key_down=self.on_key_down)
        #Iniciar Servidor
        threading.Thread(target=self.StartServer).start()

    def on_key_down(self, instance, keyboard, keycode, text, modifiers):
        if keycode == 40:
            self.Send_Message(None)
    
    def Send_Message(self, _):
        #print("enviar mensaje")
        message = self.newMessageTxt.text
        self.newMessageTxt.text = ""
        if message:
            self.historyLbl.Update_Chat_History(f"[color=dd2020]JBarco[/color] > {message}")
            if(self.historyLbl.height-5 <= self.historyLbl.layout.height): self.historyLbl.needToScroll = True
            else: self.historyLbl.needToScroll = False
            #socket enviar mensaje
        Clock.schedule_once(self.Focus_Text_Input,0.1)

    def Focus_Text_Input(self, _):
        self.newMessageTxt.focus = True

    def Incoming_Message(self, username, message):
        self.historyLbl.Update_Chat_History(f"[color=20dd20]{username}[/color] > {message}")

    def Client(self, clientConn,clientAddress,q):
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

    def SubClient(self, clients,q):
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

    def StartServer(self):
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
            clientThread = threading.Thread(target=self.Client, args=(clientConn,clientAddress,q,))
            clientThread.start()
            subClientThread = threading.Thread(target=self.SubClient, args=(clients,q,))
            subClientThread.start()


class ChatSD(App):
    def build(self):
        return ChatPage()
if __name__ == '__main__':
    ChatSD().run()
    