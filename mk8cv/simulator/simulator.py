import sqlite3
import random
import time
import json
import requests
from datetime import datetime


class RaceSimulator:
    def __init__(self, db_path='mk8cv-viz/races.db', api_url='http://localhost:3000/api/position-update'):
        self.db_path = db_path
        self.api_url = api_url
        self.players = [f'P{i}' for i in range(1, 12)]
        self.race_id = f"RACE_{int(time.time())}"
        self.positions = {player: idx + 1 for idx, player in enumerate(self.players)}

        # Connect to database
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        # Simulation parameters
        self.overtake_probability = 0.3  # Chance of position change per update
        self.blue_shell_probability = 0.1  # Chance of leader falling back
        self.catchup_probability = 0.2  # Chance of back players moving up

    def simulate_position_changes(self):
        """Simulate realistic position changes based on various racing events"""
        positions = list(self.positions.items())

        # Simulate blue shell (leader falls back)
        if random.random() < self.blue_shell_probability:
            leader = positions[0]
            positions = positions[1:]
            fall_back_pos = random.randint(3, len(positions))
            positions.insert(fall_back_pos, leader)
            print(f"🔵 Blue shell! {leader[0]} falls to position {fall_back_pos + 1}")

        # Simulate regular overtaking
        elif random.random() < self.overtake_probability:
            # Pick two adjacent positions to swap
            idx = random.randint(0, len(positions) - 2)
            positions[idx], positions[idx + 1] = positions[idx + 1], positions[idx]
            print(f"🏎 Overtake! {positions[idx][0]} passes {positions[idx + 1][0]}")

        # Simulate catchup mechanics
        elif random.random() < self.catchup_probability:
            # Back player moves up 2-3 positions
            if len(positions) > 4:
                idx = random.randint(len(positions) - 3, len(positions) - 1)
                player = positions.pop(idx)
                new_pos = max(0, idx - random.randint(2, 3))
                positions.insert(new_pos, player)
                print(f"🚀 Catchup! {player[0]} moves up to position {new_pos + 1}")

        # Update positions dictionary
        self.positions = {player: idx + 1 for idx, (player, _) in enumerate(positions)}

    def send_update(self):
        """Send position update to the API"""
        timestamp = int(time.time())
        positions = [{"player_id": pid, "position": pos}
                     for pid, pos in self.positions.items()]

        data = {
            "raceId": self.race_id,
            "timestamp": timestamp,
            "positions": positions
        }

        try:
            response = requests.post(self.api_url, json=data)
            if response.status_code == 200:
                print(f"✅ Update sent successfully at {datetime.fromtimestamp(timestamp)}")
            else:
                print(f"❌ Failed to send update: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error sending update: {e}")

        # Also save to SQLite
        # for pid, pos in self.positions.items():
        #     try:
        #         self.cursor.execute("""
        #             INSERT INTO race_positions (timestamp, player_id, position, race_id)
        #             VALUES (?, ?, ?, ?)
        #         """, (timestamp, pid, pos, self.race_id))
        #     except sqlite3.Error as e:
        #         print(f"❌ Error saving race position ({timestamp=}, {pid=}, {pos=}, {self.race_id=}) to database: {e}")
        # self.conn.commit()

    def run(self, duration=60, update_interval=1.0):
        """Run the simulation for a specified duration"""
        print(f"🏁 Starting race simulation (Race ID: {self.race_id})")
        print(f"⏱ Duration: {duration}s, Update interval: {update_interval}s")

        start_time = time.time()
        iteration = 0

        try:
            while time.time() - start_time < duration:
                iteration += 1
                print(f"\n📍 Lap {iteration}")
                self.simulate_position_changes()
                self.send_update()

                # Print current standings
                print("\nCurrent positions:")
                for pid, pos in sorted(self.positions.items(), key=lambda x: x[1]):
                    print(f"{pos}. {pid}")

                time.sleep(update_interval)

        except KeyboardInterrupt:
            print("\n⚠️ Simulation interrupted by user")
        finally:
            self.conn.close()
            print("\n🏁 Race simulation completed")

    def reset_database(self):
        """Clear existing race data and reinitialize the database"""
        self.cursor.execute("DELETE FROM race_positions")
        self.conn.commit()
        print("🗑 Database cleared")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Simulate Mario Kart race position changes')
    parser.add_argument('--duration', type=int, default=60,
                        help='Duration of the race in seconds')
    parser.add_argument('--interval', type=float, default=1.0,
                        help='Interval between updates in seconds')
    parser.add_argument('--reset-db', action='store_true',
                        help='Reset the database before starting')

    args = parser.parse_args()

    simulator = RaceSimulator()

    if args.reset_db:
        simulator.reset_database()

    simulator.run(duration=args.duration, update_interval=args.interval)