import os
import sys

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

import socket_client

kivy.require("1.10.1")


class ScrollableLabel(ScrollView):
    """
    Kivy does not provide scrollable labels, so attempting to make one.
    - ScrollView does not allow us to add more than one widget.
    - Creating a layout and placing two widgets inside it should work.
    - Height will be set manually.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = GridLayout(cols=1, size_hint_y=None)
        self.add_widget(self.layout)

        # Two widgets, one to show history, other as a scroll point (markup allows for colors, etc.).
        self.chat_history = Label(size_hint_y=None, markup=True)
        self.scroll_to_point = Label()

        self.layout.add_widget(self.chat_history)
        self.layout.add_widget(self.scroll_to_point)

    def update_chat_history(self, message):
        """
        Methods called externally to add new message to the chat history
        """
        self.chat_history.text += '\n' + message  # PRODUCTION SECURITY ISSUE!

        self.layout.height = self.chat_history.texture_size[1] + 15             # Margin on bottom (15px)
        self.chat_history.height = self.chat_history.texture_size[1]            # Height of chat_history
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)    # Margin sides (98%)

        # Scroll on update.
        self.scroll_to(self.scroll_to_point)

    def update_chat_history_layout(self, _=None):
        """
        Updates the layout as new messages come in (namely the scroll_to_point).
        """
        self.layout.height = self.chat_history.texture_size[1] + 15             # Margin on bottom (15px)
        self.chat_history.height = self.chat_history.texture_size[1]            # Height of chat_history
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)    # Margin sides (98%)


class ConnectPage(GridLayout):
    """
    Page shown on initialization.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cols = 2

        # Pre-written details used for expediting logging in.
        if os.path.isfile("prev_details.txt"):
            with open("prev_details.txt", "r") as f:
                d = f.read().split(",")
                prev_ip = d[0]
                prev_port = d[1]
                prev_username = d[2]
        else:
            prev_ip = ""
            prev_port = ""
            prev_username = ""

        self.add_widget(Label(text="IP:"))  # widget 1
        self.ip = TextInput(text=prev_ip, multiline=False)
        self.add_widget(self.ip)

        self.add_widget(Label(text="Port:"))  # widget 2
        self.port = TextInput(text=prev_port, multiline=False)
        self.add_widget(self.port)

        self.add_widget(Label(text="Username:"))  # widget 3
        self.username = TextInput(text=prev_username, multiline=False)
        self.add_widget(self.username)

        # Empty span in bottom left of grid
        self.add_widget(Label())

        # Join button in bottom right.
        self.join = Button(text="Join")
        self.join.bind(on_press=self.join_button)
        self.add_widget(self.join)

    def join_button(self, instance):
        port = self.port.text
        ip = self.ip.text
        username = self.username.text

        with open("prev_details.txt", "w") as f:
            # stores info for server login in txt file for ease of use/testing expedition.
            f.write(f"{ip},{port},{username}")

        # Create info string, update InfoPage with a message and show it
        info = f"Attempting to join {ip}:{port} as {username}"
        chat_app.info_page.update_info(info)
        chat_app.screen_manager.current = "Info"

        Clock.schedule_once(self.connect, timeout=1)

    def connect(self, timeout=1):
        """
        Connects to the server. Assumes socket_server.py is already running.
        :param timeout: Null
        """
        # sockets_client info
        port = int(self.port.text)
        ip = self.ip.text
        username = self.username.text

        if not socket_client.connect(ip=ip, port=port, my_username=username, error_callback=show_error):
            return
        # Create chat page and activate it AFTER connection
        chat_app.create_chat_page()
        chat_app.screen_manager.current = "Chat"


class ChatPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.rows = 2

        # First row -> scrollable label (history of chat), 90% height
        self.history = ScrollableLabel(height=Window.size[1] * 0.9, size_hint_y=None)
        self.add_widget(self.history)

        # Second row content -> Input field (80%width) & send button
        self.new_message = TextInput(width=Window.size[0] * 0.8, size_hint_x=None, multiline=False)
        self.send = Button(text="Send")
        self.send.bind(on_press=self.send_message)  # Binds 'send' button to send_message()

        # Minor grid layout for Row 2
        bottom_line = GridLayout(cols=2)
        bottom_line.add_widget(self.new_message)
        bottom_line.add_widget(self.send)
        self.add_widget(bottom_line)

        Window.bind(on_key_down=self.on_key_down)  # Bind the ENTER key to send the message

        Clock.schedule_once(self.focus_text_input, 1)
        socket_client.start_listening(self.incoming_message, show_error)
        self.bind(size=self.adjust_fields)  # Adjust fields for resizing window in "chat_history" section

    # Updates page layout
    def adjust_fields(self, *_):
        """
        Updates page layout
        """
        # Chat history height -> 90% + 50px constant for Row 2
        if Window.size[1] * 0.1 < 50:
            new_height = Window.size[1] - 50
        else:
            new_height = Window.size[1] * 0.9
        self.history.height = new_height

        # New message input width -> 80% + 160px constant for send button
        if Window.size[0] * 0.2 < 160:
            new_width = Window.size[0] - 160
        else:
            new_width = Window.size[0] * 0.8
        self.new_message.width = new_width

        # Update chat history layout via scheduling (non-callable?).
        Clock.schedule_once(self.history.update_chat_history_layout, 0.01)

    def on_key_down(self, instance, keyboard, keycode, text, modifiers):
        """
        If Enter key is pressed, send message.
        """
        if keycode == 40:
            self.send_message(None)

    def send_message(self, _):
        """
        Gets message, resets input form, sends message
        """
        message = self.new_message.text
        self.new_message.text = ""
        if message:
            # Red color for OUR username
            self.history.update_chat_history(f"[color=dd2020]{chat_app.connect_page.username.text}[/color] > {message}")
            socket_client.send(message)

        # Schedule refocusing to input field
        Clock.schedule_once(self.focus_text_input, 0.1)

    def focus_text_input(self, _):
        # Sets focus to text input field
        self.new_message.focus = True

    def incoming_message(self, username, message):
        # Update chat history with username and message, gets called on new message, green for username
        self.history.update_chat_history(f"[color=20dd20]{username}[/color] > {message}")


# Simple information/error page
class InfoPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.cols = 1
        self.message = Label(halign="center", valign="middle", font_size=30)
        # Binding (listening) message to update its width (default [100,100]
        self.message.bind(width=self.update_text_width)
        self.add_widget(self.message)

    def update_info(self, message):
        # Called with a message, to update message text in widget
        self.message.text = message

    def update_text_width(self, *_):
        # Updates width of label -> 90% of label width
        self.message.text_size = (self.message.width * 0.9, None)


class MyApp(App):
    """
    Main window manager. Referenced as chat_app above.
    """

    def build(self):
        self.screen_manager = ScreenManager()  # Using screen_manager to add multiple screens and switch between them

        # Initial connection screen
        self.connect_page = ConnectPage()
        screen = Screen(name="Connect")
        screen.add_widget(self.connect_page)
        self.screen_manager.add_widget(screen)

        # Info page
        self.info_page = InfoPage()
        screen = Screen(name="Info")
        screen.add_widget(self.info_page)
        self.screen_manager.add_widget(screen)

        return self.screen_manager

    def create_chat_page(self):
        """
        Waiting to create the chat page until this method is called (due to it wanting to make a connection).
        When Called, connection details should be set, then Chat widget is added to screen_manager.
        """
        self.chat_page = ChatPage()
        screen = Screen(name="Chat")
        screen.add_widget(self.chat_page)
        self.screen_manager.add_widget(screen)


def show_error(message):
    """
    Error callback function -> used by sockets client.
    Updates info page with an error message, shows message and schedules exit in 10 seconds.
    """
    print(message)
    chat_app.info_page.update_info(message)
    chat_app.screen_manager.current = "Info"
    Clock.schedule_once(sys.exit, 10)


if __name__ == "__main__":
    chat_app = MyApp()
    chat_app.run()
