import time
import threading
import requests
from supabase import create_client
from dotenv import load_dotenv
import os
from local_data import LocalData

load_dotenv()

# Constants
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Initialize Supabase Client
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)


class RemoteData:
    def __init__(self):

        # Initializing local data class
        self.local_data = LocalData()

        # Start the background sync thread
        self.sync_thread = threading.Thread(target=self.automated_sync_data)
        self.sync_thread.daemon = True
        self.sync_thread.start()

        # Initialize the LocalData instance
        self.local_data = LocalData()

    @staticmethod
    def check_internet():
        try:
            response = requests.get('https://www.google.com', timeout=5)
            return response.status_code == 200
        except requests.exceptions.ReadTimeout:
            print("Connection timed out. Internet may be slow or unavailable.")
            return False
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return False

    def automated_sync_data(self):
        print("Starting automated sync thread...")
        while True:
            try:
                start_time = time.time()
                print("Checking internet connection...")
                if self.check_internet():
                    print("Internet connection detected.")
                    data = self.local_data.fetch_all_data()
                    print(f"Fetched local data: {data}")
                    all_synced = True  # Flag to check if all records synced successfully
                    for record in data:
                        player_data = {
                            "player_id": record[1],
                            "race_date": record[2],
                            "race_type": record[3],
                            "position": record[4],
                            "race_time": record[5],
                            "reaction_time": record[6],
                            "lap_time": record[7],
                            "track_distance": record[8],
                            "eliminated": record[9],
                        }
                        try:
                            result = supabase_client.table("player_data_testing").insert(player_data).execute()
                            if result.data:
                                print(f"Record synced to Supabase: {result.data}")
                                self.local_data.synced_record(record[0])
                            else:
                                print("Failed to sync data.")
                                all_synced = False
                        except Exception as e:
                            print(f"Failed to sync record: {record}. Error: {e}")
                            all_synced = False

                            # **Trigger the Supabase function after successful sync**
                            if all_synced:
                                print("All records synced successfully. Running Supabase function...")
                                self.calculate_player_stats("calculate_player_stats")
                else:
                    print("No internet connection detected.")

                # Ensure the loop runs every 60 seconds
                elapsed_time = time.time() - start_time
                sleep_time = max(60 - elapsed_time, 0)
                print(f"Sleeping for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)

            except Exception as e:
                print(f"An unexpected error occurred in the sync thread: {e}")

    def update_player_data(self, player_model):
        if self.check_internet():
            # Attempt to save directly to Supabase
            response = supabase_client.table("player_data_testing").insert(player_model.to_sync_dict()).execute()
            if response.data:
                print("Successfully sync with Supabase, saving locally with synced.")
                print(f"Player model Synced: {player_model.to_sync_dict()}")
                self.local_data.save_locally_synced(player_model)

                # **Trigger Supabase function after successful player update**
                print("Running Supabase function after player update...")
                self.calculate_player_stats("calculate_player_stats")

            else:
                print("Failed to sync with Supabase, saving locally.")
                self.local_data.save_locally(player_model)
        else:
            print("No internet connection, saving locally.")
            self.local_data.save_locally(player_model)

    def calculate_player_stats(self, function_name, params=None):
        """
            Executes a stored function in Supabase.

            :param function_name: Name of the Supabase function to call.
            :param params: Dictionary of parameters to pass to the function (if required).
            :return: Function response or error.
        """
        try:
            if params is None:
                params = {}

            response = supabase_client.rpc(function_name, params).execute()

            if response.data:
                print(f"Function '{function_name}' executed successfully: {response.data}")
                return response.data
            else:
                print(f"Function '{function_name}' executed but returned no data.")
                return None
        except Exception as e:
            print(f"Error executing function '{function_name}': {e}")
            return None
