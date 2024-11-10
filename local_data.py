# local_data.py
import sqlite3
from threading import local
from player_model import PlayerModel


class LocalData:
    _thread_local = local()

    def __init__(self):
        # Initializing the database and creating the table with a single connection
        self.create_local_table()

    @staticmethod
    def get_connection():
        if not hasattr(LocalData._thread_local, "connection"):
            LocalData._thread_local.connection = sqlite3.connect('local_data.db')
        return LocalData._thread_local.connection

    @staticmethod
    def close_connection():
        if hasattr(LocalData._thread_local, "connection"):
            LocalData._thread_local.connection.close()
            del LocalData._thread_local.connection

    def create_local_table(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT,
                player_number TEXT,
                race_date TEXT,
                race_type TEXT,
                position INTEGER,
                race_time REAL,
                reaction_time REAL,
                lap_time REAL,
                eliminated INTEGER,
                synced INTEGER DEFAULT 0)
        ''')
        conn.commit()
        self.close_connection()

    def save_locally(self, player_model: PlayerModel):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO player_data (player_id, player_number, race_date, race_type, position, race_time, reaction_time, 
            lap_time, eliminated, synced)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (player_model.player_id, player_model.player_number, player_model.race_date, player_model.race_type,
              player_model.position, player_model.race_time, player_model.reaction_time,
              player_model.lap_time, player_model.eliminated, 0))
        conn.commit()
        self.close_connection()

    def save_locally_synced(self, player_model: PlayerModel):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
                INSERT INTO player_data (player_id, player_number, race_date, race_type, position, 
                race_time, reaction_time, lap_time, eliminated, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (player_model.player_id, player_model.player_number, player_model.race_date, player_model.race_type,
                  player_model.position, player_model.race_time, player_model.reaction_time,
                  player_model.lap_time, player_model.eliminated, 1))
        conn.commit()
        self.close_connection()

    def fetch_all_data(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM player_data WHERE synced = 0")
        un_synced_records = cursor.fetchall()
        self.close_connection()
        return un_synced_records

    def delete_record(self, record_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM player_data WHERE id = ?", (record_id,))
        conn.commit()
        self.close_connection()

    def synced_record(self, player_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE player_data SET synced = 1 WHERE id = ?", (player_id,))
        conn.commit()
        self.close_connection()
