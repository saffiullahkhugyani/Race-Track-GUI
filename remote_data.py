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
            requests.get('https://www.google.com', timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def automated_sync_data(self):
        while True:
            if self.check_internet():
                data = self.local_data.fetch_all_data()
                for record in data:
                    player_data = {
                        "player_id": record[1],
                        "player_number": record[2],
                        "position": record[3],
                        "race_time": record[4],
                        "reaction_time": record[5],
                        "lap_time": record[6],
                        "eliminated": record[7]
                    }

                    # Insert into Supabase
                    result = supabase_client.table("testing_python").insert(player_data).execute()
                    print(f"Result from supabase: {result.data}")
                    if result.data:
                        print(f"Data is present")
                    else:
                        print("something went wrong")

                    #     self.local_data.synced_record(record[0])

            # Sleep for 1 minute before the next sync attempt
            time.sleep(60)

    def update_player_data(self, player_model):
        if self.check_internet():
            # Attempt to save directly to Supabase
            response = supabase_client.table("player_data_testing").insert(player_model.to_dict()).execute()
            if response.data:
                print("Successfully sync with Supabase, saving locally with synced.")
                print(f"Player model dict: {player_model.to_dict}")
                print(f"Player model: {player_model}")
                self.local_data.save_locally_synced(player_model)
            else:
                print("Failed to sync with Supabase, saving locally.")
                self.local_data.save_locally(player_model)
        else:
            print("No internet connection, saving locally.")
            self.local_data.save_locally(player_model)
