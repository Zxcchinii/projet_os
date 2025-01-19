import asyncio
import json
import random
import uuid
import logging
import os
from typing import Dict, List

import websockets
from websockets.server import WebSocketServerProtocol, serve


class Connect4Game:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        self.current_player = 1
        self.players: Dict[int, str] = {}  # {player_number: player_id}
        self.game_over = False
        self.winner = None
        self.lock = asyncio.Lock()  # Prevent race conditions

    async def make_move(self, player, column):
        async with self.lock:
            # Validate column
            if column < 0 or column >= 7:
                return False, "Invalid column"

            # Find first empty row in the column
            for row in range(5, -1, -1):
                if self.board[row][column] == 0:
                    self.board[row][column] = player

                    # Check for winner
                    if self.check_winner(player):
                        self.game_over = True
                        self.winner = player

                    # Switch player
                    self.current_player = 3 - player
                    return True, "Move successful"

            return False, "Column is full"

    def check_winner(self, player):
        # Horizontal check
        for row in range(6):
            for col in range(4):
                if all(self.board[row][col + i] == player for i in range(4)):
                    return True

        # Vertical check
        for col in range(7):
            for row in range(3):
                if all(self.board[row + i][col] == player for i in range(4)):
                    return True

        # Diagonal checks
        for row in range(3):
            for col in range(4):
                if all(self.board[row + i][col + i] == player for i in range(4)):
                    return True
                if all(self.board[row + i][col + 3 - i] == player for i in range(4)):
                    return True

        return False


class Connect4Server:
    def __init__(self):
        self.games: Dict[str, Connect4Game] = {}
        self.player_connections: Dict[str, WebSocketServerProtocol] = {}
        self.game_waiting = None
        self.logger = logging.getLogger('Connect4Server')
        logging.basicConfig(level=logging.INFO)

    async def register_player(self, websocket: WebSocketServerProtocol, mode: str):
        player_id = str(uuid.uuid4())
        self.player_connections[player_id] = websocket

        if mode == "server":
            # Create a single-player game
            game_id = str(uuid.uuid4())
            game = Connect4Game(game_id)
            self.games[game_id] = game

            game.players[1] = player_id  # Player is always Player 1
            await websocket.send(json.dumps({
                'type': 'game_status',
                'status': 'started',
                'player_number': 1,
                'game_id': game_id
            }))

            asyncio.create_task(self.play_as_server(game))
            self.logger.info(f"Player {player_id} started a single-player game {game_id}")

        elif mode == "client":
            # Handle multiplayer registration
            if not self.game_waiting:
                game_id = str(uuid.uuid4())
                game = Connect4Game(game_id)
                self.games[game_id] = game
                self.game_waiting = game

                game.players[1] = player_id
                await websocket.send(json.dumps({
                    'type': 'game_status',
                    'status': 'waiting',
                    'player_number': 1,
                    'game_id': game_id
                }))
                self.logger.info(f"Player {player_id} created game {game_id}")

                asyncio.create_task(self.timeout_waiting_game(game_id, 60))  # Add timeout for waiting games
            else:
                game = self.game_waiting
                game.players[2] = player_id
                self.game_waiting = None

                for player_number, p_id in game.players.items():
                    player_socket = self.player_connections[p_id]
                    await player_socket.send(json.dumps({
                        'type': 'game_status',
                        'status': 'started',
                        'player_number': player_number,
                        'game_id': game.game_id
                    }))
                self.logger.info(f"Game {game.game_id} started with two players")

        else:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Invalid mode selected'
            }))
            self.logger.warning(f"Player {player_id} selected invalid mode: {mode}")
            return player_id

        return player_id

    async def timeout_waiting_game(self, game_id, timeout):
        """Timeout for waiting games."""
        await asyncio.sleep(timeout)
        if self.game_waiting and self.game_waiting.game_id == game_id:
            self.logger.info(f"Timeout for waiting game {game_id}")
            del self.games[game_id]
            self.game_waiting = None

    async def play_as_server(self, game: Connect4Game):
        """Simulate server moves for a single-player game."""
        max_turns = 42
        turns = 0
        while not game.game_over and turns < max_turns:
            if game.current_player == 2:  # Server's turn
                valid_move = False
                while not valid_move:
                    column = random.randint(0, 6)
                    valid_move, _ = await game.make_move(2, column)
                self.logger.info(f"Server played in column {column}")

                for player_id in game.players.values():
                    if player_id in self.player_connections:
                        await self.player_connections[player_id].send(json.dumps({
                            'type': 'game_update',
                            'board': game.board,
                            'current_player': game.current_player,
                            'game_over': game.game_over,
                            'winner': game.winner
                        }))
            await asyncio.sleep(1)
            turns += 1

    async def handle_move(self, player_id, data):
        for game in self.games.values():
            if player_id in game.players.values():
                player_number = list(game.players.keys())[list(game.players.values()).index(player_id)]
                if game.current_player != player_number:
                    return {'success': False, 'message': 'Not your turn'}

                success, message = await game.make_move(player_number, data['column'])
                if success:
                    for p_number, p_id in game.players.items():
                        player_socket = self.player_connections[p_id]
                        await player_socket.send(json.dumps({
                            'type': 'game_update',
                            'board': game.board,
                            'current_player': game.current_player,
                            'game_over': game.game_over,
                            'winner': game.winner
                        }))
                return {'success': success, 'message': message}

        return {'success': False, 'message': 'Game not found'}

    async def handle_websocket(self, websocket: WebSocketServerProtocol, path):
        player_id = None
        try:
            mode = None
            async for message in websocket:
                data = json.loads(message)
                if data['type'] == 'select_mode':
                    mode = data['mode']
                    break

            if mode:
                player_id = await self.register_player(websocket, mode)

                async for message in websocket:
                    data = json.loads(message)
                    if data['type'] == 'move':
                        response = await self.handle_move(player_id, data)
                        await websocket.send(json.dumps(response))

        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Player {player_id} disconnected")
            if player_id in self.player_connections:
                del self.player_connections[player_id]

        finally:
            if player_id in self.player_connections:
                del self.player_connections[player_id]

    async def start_server(self):
        port = int(os.getenv('PORT', 5000))
        server = await serve(self.handle_websocket, "0.0.0.0", port)
        self.logger.info(f"Server started on port {port}")
        await server.wait_closed()


if __name__ == "__main__":
    game_server = Connect4Server()
    asyncio.run(game_server.start_server())
