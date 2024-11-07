import sqlite3
import random
import time
import json
import requests
from datetime import datetime


class RaceSimulator:
    def __init__(self, db_path='mk8cv.db', api_url='http://localhost:3000/api/racer-update'):
        self.db_path = db_path
        self.api_url = api_url
        self.players = [f'P{i}' for i in range(1, 13)]  # P1 through P12
        self.race_id = f"RACE_{int(time.time())}"
        self.positions = {player: idx + 1 for idx, player in enumerate(self.players)}
        self.laps = {player: 1 for player in self.players}
        self.coins = {player: 0 for player in self.players}

        # List of possible items
        self.items = [
            None,
            'Banana',
            'Blooper',
            'Bob-omb',
            'Boomerang Flower',
            'Bullet Bill',
            'Coin',
            'Crazy Eight',
            'Fire Flower',
            'Golden Mushroom',
            'Green Shell',
            'Lightning',
            'Mushroom',
            'Piranha Plant',
            'Spiny Shell',
            'Star',
            'Super Horn',
            'Triple Bananas',
            'Triple Green Shells',
            'Triple Mushrooms',
            'Triple Red Shells'
        ]

        # Current items for each player (item1, item2)
        self.player_items = {player: ('None', 'None') for player in self.players}

        # Connect to database
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        # Simulation parameters
        self.overtake_probability = 0.3
        self.blue_shell_probability = 0.1
        self.catchup_probability = 0.2
        self.item_change_probability = 0.4
        self.coin_probability = 0.3

    def simulate_item_changes(self):
        """Simulate item box pickups and usage"""
        for player in self.players:
            if random.random() < self.item_change_probability:
                item1 = random.choice(self.items)
                item2 = random.choice(self.items) if random.random() < 0.3 else 'None'
                self.player_items[player] = (item1, item2)

    def simulate_coin_changes(self):
        """Simulate coin collection and loss"""
        for player in self.players:
            if random.random() < self.coin_probability:
                # 70% chance to gain a coin, 30% to lose one
                if random.random() < 0.7:
                    self.coins[player] = min(10, self.coins[player] + 1)
                else:
                    self.coins[player] = max(0, self.coins[player] - 1)

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
            idx = random.randint(0, len(positions) - 2)
            positions[idx], positions[idx + 1] = positions[idx + 1], positions[idx]
            print(f"🏎 Overtake! {positions[idx][0]} passes {positions[idx + 1][0]}")

        # Simulate catchup mechanics
        elif random.random() < self.catchup_probability:
            if len(positions) > 4:
                idx = random.randint(len(positions) - 3, len(positions) - 1)
                player = positions.pop(idx)
                new_pos = max(0, idx - random.randint(2, 3))
                positions.insert(new_pos, player)
                print(f"🚀 Catchup! {player[0]} moves up to position {new_pos + 1}")

        # Update positions dictionary
        self.positions = {player: idx + 1 for idx, (player, _) in enumerate(positions)}

    def send_updates(self):
        """Send individual position updates to the API"""
        timestamp = int(time.time() * 1000)  # Use milliseconds

        for player_id, position in self.positions.items():
            item1, item2 = self.player_items[player_id]
            data = {
                "raceId": self.race_id,
                "timestamp": timestamp,
                "playerId": player_id,
                "position": position,
                "lap": self.laps[player_id],
                "coins": self.coins[player_id],
                "item1": item1,
                "item2": item2
            }

            try:
                response = requests.post(self.api_url, json=data)
                if response.status_code == 200:
                    print(f"✅ Update sent for {player_id} at {datetime.fromtimestamp(timestamp / 1000)}")
                else:
                    print(f"❌ Failed to send update for {player_id}: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Error sending update for {player_id}: {e}")

    def run(self, duration=60, update_interval=1.0):
        """Run the simulation for a specified duration"""
        print(f"🏁 Starting race simulation (Race ID: {self.race_id})")
        print(f"⏱ Duration: {duration}s, Update interval: {update_interval}s")

        start_time = time.time()
        iteration = 0

        try:
            while time.time() - start_time < duration:
                iteration += 1
                print(f"\n📍 Update {iteration}")

                self.simulate_position_changes()
                self.simulate_item_changes()
                self.simulate_coin_changes()
                self.send_updates()

                # Print current standings
                print("\nCurrent positions:")
                for pid, pos in sorted(self.positions.items(), key=lambda x: x[1]):
                    items = self.player_items[pid]
                    print(f"{pos}. {pid} - {self.coins[pid]} coins - Items: {items[0]}, {items[1]}")

                time.sleep(update_interval)

        except KeyboardInterrupt:
            print("\n⚠️ Simulation interrupted by user")
        finally:
            self.conn.close()
            print("\n🏁 Race simulation completed")


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
    simulator.run(duration=args.duration, update_interval=args.interval)