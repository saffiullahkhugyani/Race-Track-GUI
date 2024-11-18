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
        while True:
            if self.check_internet():
                data = self.local_data.fetch_all_data()
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
                        "eliminated": record[9]
                    }

                    # print(player_data)

                    # Insert into Supabase
                    result = supabase_client.table("player_data_testing").insert(player_data).execute()
                    print(f"Record synced to supabase: {result.data}")
                    if result.data:
                        print("data synced successfully")
                        self.local_data.synced_record(record[0])
                    else:
                        print("something went wrong")

            # Sleep for 1 minute before the next sync attempt
            time.sleep(60)

    def update_player_data(self, player_model):
        if self.check_internet():
            # Attempt to save directly to Supabase
            response = supabase_client.table("player_data_testing").insert(player_model.to_sync_dict()).execute()
            if response.data:
                print("Successfully sync with Supabase, saving locally with synced.")
                print(f"Player model Synced: {player_model.to_sync_dict()}")
                self.local_data.save_locally_synced(player_model)
            else:
                print("Failed to sync with Supabase, saving locally.")
                self.local_data.save_locally(player_model)
        else:
            print("No internet connection, saving locally.")
            self.local_data.save_locally(player_model)
