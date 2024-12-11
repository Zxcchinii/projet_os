import requests
import random
import time

class Connect4Player:
    def __init__(self, server_url, player_number):
        self.server_url = server_url
        self.player_number = player_number

    def get_game_state(self):
        response = requests.get(f'{self.server_url}/game_state')
        return response.json()

    def make_move(self):
        # Simple strategy: random column selection
        available_columns = [col for col in range(7) if self._is_column_available(col)]
        if not available_columns:
            print("No available moves!")
            return False

        column = random.choice(available_columns)
        move_data = {
            'player': self.player_number,
            'column': column
        }

        response = requests.post(f'{self.server_url}/move', json=move_data)
        result = response.json()
        
        print(f"Player {self.player_number} moved to column {column}")
        print(f"Move result: {result['message']}")
        
        return result['success']

    def _is_column_available(self, column):
        game_state = self.get_game_state()
        return game_state['board'][0][column] == 0

    def play_game(self):
        while True:
            game_state = self.get_game_state()
            
            if game_state['game_over']:
                print(f"Game over! Winner: Player {game_state['winner']}")
                break
            
            if game_state['current_player'] == self.player_number:
                self.make_move()
            
            time.sleep(2)  # Wait between moves

if __name__ == '__main__':
    SERVER_URL = 'http://192.168.200.16:8000'
    player = Connect4Player(SERVER_URL, player_number=2)  # Or 2
    player.play_game()
