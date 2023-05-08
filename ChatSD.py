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



class ChatSD(App):
    def build(self):
        return ChatPage()
if __name__ == '__main__':
    ChatSD().run()
    