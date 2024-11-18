class PlayerModel:
    def __init__(self, player_number, position, race_time, reaction_time, lap_time,
                 eliminated, race_type=None, race_date=None, player_id=None, track_distance=None):
        self.player_id = player_id
        self.player_number = player_number
        self.position = position
        self.race_time = race_time
        self.reaction_time = reaction_time
        self.lap_time = lap_time
        self.eliminated = eliminated
        self.race_type = race_type
        self.race_date = race_date
        self.track_distance = track_distance

    def __repr__(self):
        return (f"PlayerInfo(player_id={self.player_id}, player_number={self.player_number}, position={self.position}, "
                f"race_time={self.race_time}, reaction_time={self.reaction_time}, "
                f"lap_time={self.lap_time}, track_distance={self.track_distance}, "
                f"eliminated={self.eliminated}, "
                f"race_type={self.race_type}, race_date={self.race_date})")

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "player_number": self.player_number,
            "position": self.position,
            "race_time": self.race_time,
            "reaction_time": self.reaction_time,
            "lap_time": self.lap_time,
            "track_distance": self.track_distance,
            "eliminated": self.eliminated,
            "race_type": self.race_type,
            "race_date": self.race_date,
        }

    def to_sync_dict(self):
        return {
            "player_id": self.player_id,
            "position": self.position,
            "race_time": self.race_time,
            "reaction_time": self.reaction_time,
            "lap_time": self.lap_time,
            "track_distance": self.track_distance,
            "eliminated": self.eliminated,
            "race_type": self.race_type,
            "race_date": self.race_date,
        }

    def to_test(self):
        return {
            "player_id": self.player_id,
            "position": self.position,
            "race_time": self.race_time,
        }
