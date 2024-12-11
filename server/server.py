from flask import Flask, request, jsonify
import threading
import json

app = Flask(__name__)

class Connect4Server:
    def __init__(self):
        self.game_state = {
            'board': [[0 for _ in range(7)] for _ in range(6)],
            'current_player': 1,
            'game_over': False,
            'winner': None
        }
        self.lock = threading.Lock()

    def check_winner(self, board, player):
        # Horizontal check
        for row in range(6):
            for col in range(4):
                if all(board[row][col+i] == player for i in range(4)):
                    return True
        
        # Vertical check
        for col in range(7):
            for row in range(3):
                if all(board[row+i][col] == player for i in range(4)):
                    return True
        
        # Diagonal checks
        for row in range(3):
            for col in range(4):
                # Diagonal down-right
                if all(board[row+i][col+i] == player for i in range(4)):
                    return True
                # Diagonal down-left
                if all(board[row+i][col+3-i] == player for i in range(4)):
                    return True
        
        return False

    def make_move(self, player, column):
        with self.lock:
            # Validate column
            if column < 0 or column >= 7:
                return False, "Invalid column"
            
            # Find first empty row in the column
            for row in range(5, -1, -1):
                if self.game_state['board'][row][column] == 0:
                    self.game_state['board'][row][column] = player
                    
                    # Check for winner
                    if self.check_winner(self.game_state['board'], player):
                        self.game_state['game_over'] = True
                        self.game_state['winner'] = player
                    
                    # Switch player
                    self.game_state['current_player'] = 3 - player
                    return True, "Move successful"
            
            return False, "Column is full"

game_server = Connect4Server()

@app.route('/move', methods=['POST'])
def handle_move():
    data = request.json
    player = data.get('player')
    column = data.get('column')
    
    success, message = game_server.make_move(player, column)
    return jsonify({
        'success': success,
        'message': message,
        'game_state': game_server.game_state
    })

@app.route('/game_state', methods=['GET'])
def get_game_state():
    return jsonify(game_server.game_state)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)