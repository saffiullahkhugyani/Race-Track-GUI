import time
from datetime import datetime
import serial.tools.list_ports
import serial
import json
import threading
import tkinter
from tkinter import messagebox, font, simpledialog
import customtkinter as ctk

from remote_data import RemoteData
from player_model import PlayerModel
from local_data import LocalData


class SerialCommunication:
    def __init__(self, port, baud_rate, update_callback, messagebox_callback,
                 status_update_label_callback, comport_connected_label_callback):
        self.port = port
        self.baud_rate = baud_rate
        self.update_callback = update_callback
        self.status_update_label_callback = status_update_label_callback
        self.comport_connected_label_callback = comport_connected_label_callback
        self.messagebox_callback = messagebox_callback
        self.serial = None

        self.ports = serial.tools.list_ports.comports()
        self.port_list = [str(port) for port in self.ports]
        for comport in self.port_list:
            print(comport)

        # if ports are available then connecting to the given (COM) port
        if self.port is not None:
            try:
                # Serial port initialization
                self.serial = serial.Serial(self.port, self.baud_rate)
                print(f"Connected to {self.port}")

                # callbacks
                self.comport_connected_label_callback()
                self.messagebox_callback(f'Connected to {self.serial.port}', True)

                # starting thread to fetch data from arduino
                self.read_thread = threading.Thread(target=self.read_serial_data)
                self.read_thread.daemon = True
                self.read_thread.start()

            except serial.SerialException as e:
                print(f"Exception: {e}")
                messagebox_callback(e, False)

    def read_serial_data(self):
        while True:
            if self.serial.in_waiting:
                data = self.serial.readline().decode().strip()
                try:
                    received_data = json.loads(data)  # Assuming data is in JSON format
                    if isinstance(received_data, dict):

                        # To display players data
                        if "player_info" in received_data:
                            self.update_callback(received_data)

                        # updating the label based on the game
                        if "status" in received_data:
                            self.status_update_label_callback(received_data)

                    else:
                        pass

                except json.JSONDecodeError as e:
                    print("JSON decode error:", e)
                    print(data)
                except Exception as e:
                    print("Error:", e)


class App(ctk.CTk):
    race_type = None
    ready_headline = None

    def __init__(self, title, size):
        # main window setup
        super().__init__()
        self.title(title)

        self.read_config_file()

        self.geometry(f"{size[0]}x{size[1]}+{100}+{50}")
        self.minsize(650, 500)

        # Schedule the window to be maximized after it has been fully initialized
        self.after(0, self.maximize_window)

        # Set full screen state
        self.full_screen_state = True
        self.bind("<F11>", self.toggle_full_screen)
        self.bind("<Escape>", self.end_full_screen)

        # side_bar instance with None for maine_frame
        self.side_bar = SideBar(self, main_frame=None)

        # passing side_bar instance into main_frame
        self.main_frame = MainFrame(self, self.side_bar)

        # updating reference of maine frame into side_bar
        # and configuring the reset button command after main frame is initialized
        self.side_bar.main_frame = self.main_frame
        self.side_bar.reset_button.configure(command=self.main_frame.destroy_widget)

        # # serial communication class initializing
        # self.serial_communication = None
        # self.serial_communication = SerialCommunication('COM6', 9600, self.main_frame.display)

        # run
        self.mainloop()

    def maximize_window(self):
        self.state("zoomed")

    def toggle_full_screen(self, event=None):
        self.full_screen_state = not self.full_screen_state
        self.attributes("-fullscreen", self.full_screen_state)

    def end_full_screen(self, event=None):
        self.full_screen_state = False
        self.attributes("-fullscreen", False)

    def read_config_file(self, event=None):
        with open('config.json') as config_file:
            data = json.load(config_file)

            self.race_type = data['race_type']
            self.ready_headline = data['ready_headline']


class SideBar(ctk.CTkFrame):
    def __init__(self, parent, main_frame):
        super().__init__(parent)

        # Dictionary to store player IDs
        self.player_id_map = {}

        # instance of Main frame to access the class methods
        self.is_success = None
        self.message = None
        self.main_frame = main_frame

        # serial communication class initializing
        self.serial_communication = None

        self.configure(fg_color='gray70')
        self.place(x=0, y=0, relwidth=0.12, relheight=1)

        # reset button
        self.reset_button = ctk.CTkButton(self, state="disabled", text='Reset', command=None)
        self.reset_button.pack(side='bottom', padx=5, pady=5)

        # taking input of (COM) port number
        self.com_port_entry = ctk.CTkEntry(self, placeholder_text="Enter (COM) Number")
        self.com_port_entry.pack(padx=5, pady=5)
        self.connect_button = ctk.CTkButton(self, text='Connect', command=self.connect_serial)
        self.connect_button.pack(side='top', padx=5, pady=5)

        # Add Player ID button
        self.add_player_button = ctk.CTkButton(self, text='Add Players', command=self.add_players)
        self.add_player_button.pack(side='top', padx=5, pady=5)

        self.circle = Circle(self, radius=25, color="red")

    def connect_serial(self):
        com_port = "COM" + self.com_port_entry.get()

        self.com_port_entry.delete(0, 'end')
        print(com_port)

        # initializing serial communication
        self.serial_communication = SerialCommunication(com_port, 9600,
                                                        self.main_frame.display,
                                                        self.update_message_box,
                                                        self.main_frame.status_update_label,
                                                        self.main_frame.com_port_connected_label)

    def update_message_box(self, message, is_success):
        self.message = message
        self.is_success = is_success

        if self.is_success:

            # displaying message if connection is success
            messagebox.showinfo("Success", message)

            # updating the circle color if connection success
            self.circle.update_connection_status()
            self.connect_button.configure(state='disabled')
            self.reset_button.configure(state='normal')
        else:
            messagebox.showerror("Failed", message)

    def add_players(self):
        # Ask for the number of players
        num_players = simpledialog.askinteger("Number of Players", "Enter the number of players:")
        if num_players is None:
            return  # User canceled

        # for i in range(1, num_players + 1):
        #     player_id = simpledialog.askstring("Player ID", f"Enter ID for Player {i}:")
        #     if player_id:
        #         self.player_id_map[i] = player_id

        player_id_dialog = PlayerIDDialog(self, num_players)
        player_id_map = player_id_dialog.get_player_ids()

        if player_id_map:
            # Store or process the collected player IDs
            self.player_id_map = player_id_map
            messagebox.showinfo("Player IDs", f"Collected IDs: {self.player_id_map}")

        # Process the player IDs (e.g., save to the database or display in UI)
        # messagebox.showinfo("Player IDs", f"Collected IDs: {self.player_id_map}")
        # Optionally, store the player_ids in a variable or pass them to another part of the app


class MainFrame(ctk.CTkFrame):
    playerWidget = []
    playersDataList = []
    dynamic_label = None

    def __init__(self, parent, sidebar):
        super().__init__(parent)

        # store reference to sidebar
        self.sidebar = sidebar

        self.place(relx=0.12, y=0, relwidth=0.88, relheight=1)

        self.label = ctk.CTkLabel(self, text='Loading...',
                                  font=ctk.CTkFont(size=120, weight=font.BOLD, family='Helvetica'))
        self.label.pack(expand=True, fill='both')

        # initializing dynamic label
        self.dynamic_label = parent.ready_headline
        self.dynamic_race_type = parent.race_type

        # Initializing  Local data instance
        self.local_data = LocalData()

        # Initializing remote data instance
        self.remote_data = RemoteData()

    def com_port_connected_label(self):
        self.label.configure(text=self.dynamic_label)

    def status_update_label(self, data):

        """ print function for testing in development """
        # print(f"status update function: {data}")

        status = data.get("status", "")

        if isinstance(data, dict) and all(key in data for key in ("status",)):
            if status == "Start":
                for i in range(3, 0, -1):
                    self.label.configure(text=i, font=ctk.CTkFont(size=500, weight=font.BOLD, family='Helvetica'))
                    time.sleep(1)
                self.label.configure(text="Go")
            elif status == "Reset":
                print(f"status: {status}")
                self.destroy_widget()
            elif status == "Race finished":

                # date of race
                # Date of race as a string
                date_stamp = datetime.now()
                cd = date_stamp.date().strftime('%Y-%m-%d')  # Format date as string "YYYY-MM-DD"
                print(f"Date: {cd}")
                # race type
                race_type = self.dynamic_race_type
                for child in self.playersDataList:
                    # converting dict into player model and passing it to database
                    player_dict = child
                    player_model = PlayerModel(**player_dict, race_type=race_type, race_date=cd)
                    # print(f"Data: {player_model.to_dict()}")

                    self.remote_data.update_player_data(player_model)

                # fetch_all_record = self.local_data.fetch_all_data()
                # for un_synced_child in fetch_all_record:
                #     print(f"saved and un synced data: {un_synced_child}")

            else:
                if 'wins!!' in status:
                    print(f'oho status {status}')
                    self.label.pack(expand=False, fill='both')
                    self.label.configure(text=f"{self.dynamic_race_type} {status}",
                                         font=ctk.CTkFont(size=100, weight=font.BOLD, family='Helvetica'))
                else:
                    self.label.pack(expand=False, fill='both')
                    self.label.configure(text=status,
                                         font=ctk.CTkFont(size=100, weight=font.BOLD, family='Helvetica'))

    def len(self):
        # print function for development purpose
        return len(self.playersDataList)

    def destroy_widget(self):
        if self.playerWidget is not None:
            for child in self.playerWidget:
                child.delete()
            if len(self.playerWidget) != 0:
                print(f"list is not empty: {len(self.playerWidget)}")
                self.playerWidget = []
                self.playersDataList = []
            else:
                print(f"Player widget list is empty: {len(self.playerWidget)}")
            self.label.pack(expand=True, fill='both')
            self.label.configure(text=self.dynamic_label)

    def display(self, data):

        """ print function for testing in development """
        # print(f" display function: {data}")

        if isinstance(data, dict) and all(key in data for key in ("player_info",)):

            # extracting player information
            playerData = data.get("player_info")

            # getting player number
            player_number = playerData.get("player_number")

            # fetching player id from side_bar and adding it to player data
            player_id = self.sidebar.player_id_map.get(player_number, "Unknown ID")
            playerData["player_id"] = player_id  # adding player_id to player data

            self.playersDataList.append(playerData)
            self.playerWidget.append(PlayerInfo(self, 'red', playerData, self.len()))
            time.sleep(0.1)
        else:
            pass

        # if self.len() > self.playersLength:
        #     self.playersLength = self.len()
        # else:
        #     self.checkAllData = True

        # print(self.playersLength)

        # if self.checkAllData:
        #     for index, child in enumerate(self.playersDataList):
        #         self.playerWidget.append(PlayerInfo(self, 'red', child, self.len()))
        #         time.sleep(0.1)
        #
        # print(f"Player wid length: {len(self.playerWidget)}")


class PlayerInfo(ctk.CTkFrame):
    def __init__(self, parent, color, data, player_wid_length):
        super().__init__(parent)

        # player widget length
        length = player_wid_length

        # player data
        player_number = data.get("player_number", "")
        player_position = data.get("position", "")
        reaction_time = data.get("reaction_time", "")
        lap_time = data.get("lap_time", "")
        eliminated = data.get("eliminated", "")
        race_time = data.get("race_time", "")
        status = data.get("status", "")

        player_status = (
            "DNF" if player_position == 0 and not eliminated else
            "Position {}".format(player_position) if not eliminated else
            "OUT"
        )

        color = ['red', 'green', 'blue', 'yellow'][player_number - 1] if 1 <= player_number <= 4 else 'gray'

        # configure row and columns
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # color frame
        self.colorFrame = tkinter.Frame(self, background=color, height=50, highlightthickness=1,
                                        highlightbackground='black')
        self.colorFrame.grid(row=0, column=0, rowspan=1, sticky='new')

        # player data frame
        self.dataFrame = tkinter.Frame(self, background="white", highlightthickness=1, highlightbackground='black')
        self.dataFrame.grid(row=1, column=0, sticky='new', rowspan=4)

        if length <= 2:
            # dynamic font sizes for 2 players
            self.default_font_size = 65
            self.default_font_size_small = 40
            self.default_font_size_label = 18
        elif length == 3:
            # dynamic font sizes for 3 players
            self.default_font_size = 85
            self.default_font_size_small = 65
            self.default_font_size_label = 43
        elif length == 4:
            # dynamic font sizes for 4 players
            self.default_font_size = 95
            self.default_font_size_small = 75
            self.default_font_size_label = 53

        # player number
        self.playerNumber = tkinter.Label(self.dataFrame, text=f"Player {player_number}", background='gray70',
                                          borderwidth=1, relief='solid')
        self.playerNumber.pack(padx=5, pady=(5, 0), fill='both')

        # player status
        self.playerStatus = tkinter.Label(self.dataFrame, text=player_status, background='gray70', borderwidth=1,
                                          relief='solid')
        self.playerStatus.pack(padx=5, pady=(5, 0), fill='both')

        # player response time
        self.playerResponseTimeFrame = tkinter.Frame(self.dataFrame, background="gray70",
                                                     borderwidth=1, relief='solid')
        self.playerResponseTimeLabel = tkinter.Label(self.playerResponseTimeFrame, text="Response time:",
                                                     background='gray70')
        self.playerResponseTime = tkinter.Label(self.playerResponseTimeFrame, text=reaction_time,
                                                background='gray70')

        self.playerResponseTimeFrame.pack(padx=5, pady=(5, 0), fill='both')
        self.playerResponseTimeLabel.pack(padx=2, pady=(2, 0), fill='x')
        self.playerResponseTime.pack(padx=2, pady=(0, 2), fill='x')

        # player lap time
        self.playerLapTimeFrame = tkinter.Frame(self.dataFrame, background="gray70",
                                                borderwidth=1, relief='solid')
        self.playerLapTimeLabel = tkinter.Label(self.playerLapTimeFrame, text="Lap time: ", background='gray70')
        self.playerLapTime = tkinter.Label(self.playerLapTimeFrame, text=lap_time, background='gray70')

        self.playerLapTimeFrame.pack(padx=5, pady=(5, 5), fill='both')
        self.playerLapTimeLabel.pack(padx=2, pady=(2, 0), fill='x')
        self.playerLapTime.pack(padx=2, pady=(0, 2), fill='x')

        self.pack(side='left', expand=True, fill='x', padx=(10, 10), pady=20)

        self.update_fonts()
        self.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        self.update_fonts()

    def update_fonts(self):
        width = self.winfo_width()
        height = self.winfo_height()

        # Calculate font sizes based on widget size
        font_size = max(10, int(self.default_font_size * min(width / 400, height / 300)))
        font_size_small = max(8, int(self.default_font_size_small * min(width / 400, height / 300)))
        font_size_label = max(6, int(self.default_font_size_label * min(width / 400, height / 300)))

        # Update font sizes
        self.playerNumber.config(font=ctk.CTkFont(size=font_size, weight=font.BOLD, family='Helvetica'))
        self.playerStatus.config(font=ctk.CTkFont(size=font_size_small, weight=font.BOLD, family='Helvetica'))
        self.playerResponseTimeLabel.config(font=ctk.CTkFont(size=font_size_label, weight=font.NORMAL,
                                                             family='Helvetica'))
        self.playerResponseTime.config(font=ctk.CTkFont(size=font_size_small, weight=font.BOLD, family='Helvetica'))
        self.playerLapTimeLabel.config(font=ctk.CTkFont(size=font_size_label, weight=font.NORMAL, family='Helvetica'))
        self.playerLapTime.config(font=ctk.CTkFont(size=font_size_small, weight=font.BOLD, family='Helvetica'))

    def delete(self):
        self.destroy()


class Circle(tkinter.Frame):
    def __init__(self, parent, radius=50, color="black", **kwargs):
        super().__init__(parent)
        # creating canvas for circle
        self.canvas = tkinter.Canvas(self, width=radius * 2, height=radius * 2, **kwargs)
        self.circle = self.canvas.create_oval(2, 2, radius * 2, radius * 2, outline='black', fill=color)
        self.canvas.configure(bg='gray70', highlightthickness=0)
        self.canvas.pack(ipadx=1, ipady=1)

        # label to display connection status
        self.label = tkinter.Label(self, text='Disconnected', background='gray70')
        self.label.pack(side='bottom', fill='x')

        # frame configuration
        self.configure(background='gray70')
        self.pack(side='bottom', )

    def update_connection_status(self):
        self.canvas.itemconfig(self.circle, fill='blue')
        self.label.configure(text="Connected")


class PlayerIDDialog(ctk.CTkToplevel):
    def __init__(self, parent, num_players):
        super().__init__(parent)
        self.title("Enter Player IDs")
        self.num_players = num_players
        self.player_id_map = {}

        # Create input fields for each player
        self.entries = {}
        for i in range(1, num_players + 1):
            label = ctk.CTkLabel(self, text=f"Player {i} ID:")
            label.grid(row=i - 1, column=0, padx=10, pady=5)
            entry = ctk.CTkEntry(self)
            entry.grid(row=i - 1, column=1, padx=10, pady=5)
            self.entries[i] = entry

        # Confirm button
        self.confirm_button = ctk.CTkButton(self, text="Confirm", command=self.on_confirm)
        self.confirm_button.grid(row=num_players, column=0, columnspan=2, pady=10)

    def on_confirm(self):
        # Collect data from entries
        for i, entry in self.entries.items():
            player_id = entry.get()
            if player_id:
                self.player_id_map[i] = player_id
        self.destroy()  # Close dialog window

    def get_player_ids(self):
        self.wait_window()  # Wait until the dialog is closed
        return self.player_id_map


if __name__ == "__main__":
    App("Race Track", (1200, 600))
