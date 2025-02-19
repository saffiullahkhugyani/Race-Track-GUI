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

        # updating reference of main frame into side_bar
        # and configuring the reset button command after main frame is initialized
        self.side_bar.main_frame = self.main_frame
        self.side_bar.reset_button.configure(command=self.main_frame.destroy_widget)

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


class SideBar(ctk.CTkFrame):
    def __init__(self, parent, main_frame):
        super().__init__(parent)

        # instance of Main frame to access the class methods
        self.is_success = None
        self.message = None
        self.main_frame = main_frame

        # serial communication class initializing
        self.serial_communication = None

        # Initializing  Local data instance
        self.local_data = LocalData()

        # sensor data
        self.sensor_data = None

        self.configure(fg_color='gray70')
        self.place(x=0, y=0, relwidth=0.12, relheight=1)

        # Race type dropdown
        self.race_types = ["Jet", "Plane", "Co2 Car",
                           "Gravity car","Walk along glider", "Jet glider"]  # predefined race types
        self.race_type_dropdown = ctk.CTkOptionMenu(self, values=self.race_types)
        self.race_type_dropdown.pack(padx=5, pady=5)

        # headline Dropdown
        self.headline_list = ["Get Ready Pilots", "Get Ready Drivers"]
        self.headline_dropdown = ctk.CTkOptionMenu(self, values=self.headline_list)
        self.headline_dropdown.pack(padx=5, pady=5)

        self.track_distance_entry = ctk.CTkEntry(self, placeholder_text="Enter Track Distance")
        self.track_distance_entry.pack(padx=5, pady=5)

        self.country_entry = ctk.CTkEntry(self, placeholder_text="Enter Country")
        self.country_entry.pack(padx=5, pady=5)

        self.city_entry = ctk.CTkEntry(self, placeholder_text="Enter City")
        self.city_entry.pack(padx=5, pady=5)

        # taking input of (COM) port number
        self.com_port_entry = ctk.CTkEntry(self, placeholder_text="Enter (COM) Number")
        self.com_port_entry.pack(padx=5, pady=5)

        # connect button and reset button
        self.connect_button = ctk.CTkButton(self, text='Connect', command=self.connect_serial)
        self.connect_button.pack(side='top', padx=5, pady=5)

        self.reset_button = ctk.CTkButton(self, state="disabled", text='Reset', command=None)
        self.reset_button.pack(side='bottom', padx=5, pady=5)

        # serial connection indicator RED for disconnect, BLUE for connected
        self.circle = Circle(self, radius=25, color="red")

        # Divider
        self.divider_frame = ctk.CTkFrame(self, height=2, fg_color="gray80")
        self.divider_frame.pack(fill='x', pady=10, padx=4)

        # Container for the ir sensors indication
        self.status_container = ctk.CTkFrame(self)
        self.status_container.configure(fg_color='gray70')
        self.status_container.pack(padx=5)

        self.label = ctk.CTkLabel(self.status_container, text="Ir Sensor Status",
                                  font=ctk.CTkFont(size=15, weight=font.BOLD, family='Helvetica'))
        self.label.pack(side='top', pady=5)

        # Serial connection indicator: circle and label
        self.s1 = Circle(self.status_container, radius=8, color="green")
        self.s1.pack(side='top', pady=5)
        self.s1.label.configure(text="Player 1", bg='gray70',
                                font=ctk.CTkFont(size=12, weight=font.BOLD, family='Helvetica'))

        # Serial connection indicator: circle and label
        self.s2 = Circle(self.status_container, radius=8, color="green")
        self.s2.pack(side='top', pady=5)
        self.s2.label.configure(text="Player 2",
                                font=ctk.CTkFont(size=12, weight=font.BOLD, family='Helvetica'))

    def connect_serial(self):

        # validate that all the fields are filled
        if not all([
            self.race_type_dropdown.get().strip(),
            self.headline_dropdown.get().strip(),
            self.track_distance_entry.get().strip(),
            self.country_entry.get().strip(),
            self.city_entry.get().strip(),
            self.com_port_entry.get().strip()
        ]):
            messagebox.showwarning("Incomplete Information", "Please fill in all the fields"
                                                             " before connecting")
            return

        # if all fields are validated saving a copy of data into database
        self.local_data.save_race_session_info(race_type=self.race_type_dropdown.get(), headline=self.headline_dropdown.get(),
                                               track_distance=self.track_distance_entry.get().strip(),
                                               country=self.country_entry.get().strip(),
                                               city=self.city_entry.get().strip(),
                                               com_port=self.com_port_entry.get().strip())

        # passing data to main frame
        self.main_frame.race_type = self.race_type_dropdown.get().strip()
        self.main_frame.race_headline = self.headline_dropdown.get().strip()
        self.main_frame.track_distance = self.track_distance_entry.get().strip()

        # Geather and display COM port information
        com_port = "COM" + self.com_port_entry.get()
        self.com_port_entry.delete(0, 'end')
        print(f"Connecting to {com_port} with provided race details...")

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

    def ir_sensor_status(self, data):
        self.sensor_data = data

        # this method update the Ir sensor info on the sidebar
        if isinstance(data, dict) and "status" in data:
            details = data.get("details", {})

            if isinstance(details, dict):  # Ensure 'details' is a dictionary
                player_num = details.get("player", None)
                sensor_status = details.get("ir_sensor_status", False)

                if player_num == 1:
                    print(f"Player {player_num} sensor status is {sensor_status}")
                    self.s1.update_ir_sensor_status(status=sensor_status)

                if player_num == 2:
                    print(f"Player {player_num} sensor status is {sensor_status}")
                    self.s2.update_ir_sensor_status(status=sensor_status)

            else:
                print("No details available.")


class MainFrame(ctk.CTkFrame):
    playerWidget = []
    playersDataList = []
    dynamic_label = None

    def __init__(self, parent, sidebar):
        super().__init__(parent)

        # store reference to sidebar
        self.sidebar = sidebar

        self.place(relx=0.12, y=0, relwidth=0.88, relheight=1)

        self.label = ctk.CTkLabel(self, text='Enter Race Details',
                                  font=ctk.CTkFont(size=120, weight=font.BOLD, family='Helvetica'))
        self.label.pack(expand=True, fill='both')

        # list for store race details
        self.race_type = None
        self.race_headline = None
        self.track_distance = None

        # Initializing  Local data instance
        self.local_data = LocalData()

        # Initializing remote data instance
        self.remote_data = RemoteData()

        # Initializing model list for final data
        self.player_model_list = []

    def com_port_connected_label(self):
        self.label.configure(text=self.race_headline)

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

                for child in self.playersDataList:
                    # converting dict into player model and passing it to database
                    player_dict = child
                    player_id_dialog = PlayerIDDialog(self, child["player_number"])
                    player_id = player_id_dialog.get_player_id()

                    player_model = PlayerModel(**player_dict, race_type=self.race_type,
                                               race_date=cd, player_id=player_id,
                                               track_distance=self.track_distance)
                    self.player_model_list.append(player_model)
                    print(f"Data before sync: {player_model.to_dict()}")

                # to sync data to remote and local databases
                for data in self.player_model_list:
                    self.remote_data.update_player_data(data)
            elif status == "Ir Sensor":
                self.sidebar.ir_sensor_status(data=data)
            else:
                if 'wins!!' in status:
                    print(f'oho status {status}')
                    self.label.pack(expand=False, fill='both')
                    self.label.configure(text=f"{self.race_type} {status}",
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
                self.player_model_list = []
            else:
                print(f"Player widget list is empty: {len(self.playerWidget)}")
            self.label.pack(expand=True, fill='both')
            self.label.configure(text=self.race_headline)

    def display(self, data):

        """ print function for testing in development """
        # print(f" display function: {data}")

        if isinstance(data, dict) and all(key in data for key in ("player_info",)):

            # extracting player information
            playerData = data.get("player_info")

            self.playersDataList.append(playerData)
            self.playerWidget.append(PlayerInfo(self, 'red', playerData, self.len()))
            time.sleep(0.1)
        else:
            pass


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

        color = ['green', 'red', 'blue', 'yellow'][player_number - 1] if 1 <= player_number <= 4 else 'gray'

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

    def update_ir_sensor_status(self, status=False):
        if status:
            self.canvas.itemconfig(self.circle, fill="red")
        else:
            self.canvas.itemconfig(self.circle, fill="green")


class PlayerIDDialog(ctk.CTkToplevel):
    def __init__(self, parent, player_number):
        super().__init__(parent)
        self.title("Enter Player ID")

        # Set dialog to be on top and modal
        self.transient(parent)
        self.grab_set()

        # Create input fields for each player
        self.player_id = None
        self.label = ctk.CTkLabel(self, text=f"Player {player_number} ID:")
        self.label.grid(row=1 - 1, column=0, padx=10, pady=5)
        self.entry = ctk.CTkEntry(self)
        self.entry.grid(row=1 - 1, column=1, padx=10, pady=5)
        self.player_id = self.entry.get().strip()

        # Confirm button
        self.confirm_button = ctk.CTkButton(self, text="Confirm", command=self.on_confirm)
        self.confirm_button.grid(row=1, column=0, columnspan=2, pady=10)

    def on_confirm(self):
        # Collect data from entries
        self.player_id = self.entry.get().strip()
        print(f"Player id: {self.entry.get().strip()}")

        self.destroy()  # Close dialog window

    def get_player_id(self):
        self.wait_window()  # Wait until the dialog is closed
        return self.player_id


if __name__ == "__main__":
    App("Race Track", (1200, 600))
