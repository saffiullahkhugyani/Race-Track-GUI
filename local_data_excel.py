# local_data.py
import pandas as pd
from player_model import PlayerModel
import os


class LocalDataExcel:
    def __init__(self):
        # Define the Excel file path
        self.file_path = "player_data.xlsx"
        # Initialize the Excel file with headers if it doesn't exist
        if not os.path.exists(self.file_path):
            self.initialize_excel()

    def initialize_excel(self):
        # Create a DataFrame with headers to initialize the Excel file
        headers = ['player_id', 'race_date', 'race_type' , 'race_time'
                   , 'lap_time', 'player_city', 'player_country']
        pd.DataFrame(columns=headers).to_excel(self.file_path, index=False)

    def save_to_excel(self, player_model: PlayerModel):
        # Convert the player data to a DataFrame
        data = {
            'player_id': [player_model.player_id],
            'race_date': [player_model.race_date],
            'race_type': [player_model.race_type],
            'race_time': [player_model.race_time],
            'lap_time': [player_model.lap_time],
            'player_city': [player_model.player_city],
            'player_country': [player_model.player_country],
        }
        df = pd.DataFrame(data)

        # Append the data to the existing Excel file
        with pd.ExcelWriter(self.file_path, mode='a', engine='openpyxl', if_sheet_exists="overlay") as writer:
            df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)

    def fetch_all_data(self):
        # Read data from the Excel file
        df = pd.read_excel(self.file_path)
        return df[df['synced'] == 0]  # Filter unsynced records

    def mark_as_synced(self, player_id):
        # Load data from Excel, update the 'synced' column, and save it back
        df = pd.read_excel(self.file_path)
        df.loc[df['player_id'] == player_id, 'synced'] = 1
        df.to_excel(self.file_path, index=False)
