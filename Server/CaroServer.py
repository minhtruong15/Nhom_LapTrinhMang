import socket
import threading
import json
import random
from typing import Dict, List, Tuple
from datetime import datetime

class TicTacToeServer:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[int, socket.socket] = {}
        self.games: Dict[int, Dict] = {}
        self.client_counter = 0
        self.lock = threading.Lock()
        
    def start(self):
        """Khởi động server"""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"🎮 Server khởi động tại {self.host}:{self.port}")
        print(f"⏰ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                self.client_counter += 1
                client_id = self.client_counter
                
                with self.lock:
                    self.clients[client_id] = client_socket
                
                print(f"✅ Client {client_id} kết nối từ {address}")
                print(f"   Số client hiện tại: {len(self.clients)}")
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_id, client_socket)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\n🛑 Server dừng")
            self.shutdown()
    
    def handle_client(self, client_id: int, client_socket: socket.socket):
        """Xử lý kết nối từ client"""
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                
                if not data:
                    break
                
                message = json.loads(data)
                self.process_message(client_id, message, client_socket)
                
        except Exception as e:
            print(f"❌ Lỗi client {client_id}: {e}")
        finally:
            self.disconnect_client(client_id, client_socket)
    
    def process_message(self, client_id: int, message: Dict, client_socket: socket.socket):
        """Xử lý tin nhắn từ client"""
        action = message.get('action')
        
        if action == 'create_game':
            player_name = message.get('player_name', f'Player {client_id}')
            self.create_game(client_id, client_socket, player_name)
        
        elif action == 'join_game':
            game_id = message.get('game_id')
            player_name = message.get('player_name', f'Player {client_id}')
            self.join_game(client_id, game_id, client_socket, player_name)
        
        elif action == 'move':
            game_id = message.get('game_id')
            position = message.get('position')
            self.make_move(client_id, game_id, position)
        
        elif action == 'list_games':
            self.send_game_list(client_id, client_socket)
    
    def create_game(self, client_id: int, client_socket: socket.socket, player_name: str):
        """Tạo game mới"""
        with self.lock:
            game_id = len(self.games) + 1
            self.games[game_id] = {
                'player1': client_id,
                'player2': None,
                'player1_name': player_name,
                'player2_name': None,
                'board': ['' for _ in range(100)],
                'current_turn': 1,
                'status': 'waiting',
                'sockets': {client_id: client_socket},
                'first_player': None,
                'created_at': datetime.now()
            }
        
        response = {
            'action': 'game_created',
            'game_id': game_id,
            'player_symbol': 'X'
        }
        client_socket.send(json.dumps(response).encode('utf-8'))
        print(f"🎮 Game {game_id} được tạo bởi {player_name}")
    
    def join_game(self, client_id: int, game_id: int, client_socket: socket.socket, player_name: str):
        """Tham gia game"""
        with self.lock:
            if game_id not in self.games:
                response = {'action': 'error', 'message': 'Game không tồn tại'}
                client_socket.send(json.dumps(response).encode('utf-8'))
                return
            
            game = self.games[game_id]
            
            if game['player2'] is not None:
                response = {'action': 'error', 'message': 'Game đã đầy'}
                client_socket.send(json.dumps(response).encode('utf-8'))
                return
            
            game['player2'] = client_id
            game['player2_name'] = player_name
            game['status'] = 'playing'
            game['sockets'][client_id] = client_socket
            
            game['first_player'] = random.choice([1, 2])
            game['current_turn'] = game['first_player']
        
        for pid, sock in game['sockets'].items():
            symbol = 'X' if pid == game['player1'] else 'O'
            player1_name = game['player1_name']
            player2_name = game['player2_name']
            first_player_symbol = 'X' if game['first_player'] == 1 else 'O'
            first_player_name = player1_name if game['first_player'] == 1 else player2_name
            
            response = {
                'action': 'game_started',
                'game_id': game_id,
                'player_symbol': symbol,
                'player1_name': player1_name,
                'player2_name': player2_name,
                'board': game['board'],
                'current_turn': game['current_turn'],
                'first_player_symbol': first_player_symbol,
                'first_player_name': first_player_name
            }
            sock.send(json.dumps(response).encode('utf-8'))
        
        print(f"✅ {player_name} tham gia Game {game_id}")
        print(f"   Người chơi 1: {game['player1_name']} (X)")
        print(f"   Người chơi 2: {game['player2_name']} (O)")
        print(f"   Người đi trước: {first_player_name} ({first_player_symbol})")
    
    def make_move(self, client_id: int, game_id: int, position: int):
        """Thực hiện nước đi"""
        with self.lock:
            if game_id not in self.games:
                return
            
            game = self.games[game_id]
            
            # Kiểm tra lượt chơi
            if game['current_turn'] == 1 and client_id != game['player1']:
                return
            if game['current_turn'] == 2 and client_id != game['player2']:
                return
            
            # Kiểm tra ô hợp lệ
            if game['board'][position] != '':
                return
            
            # Cập nhật bảng
            symbol = 'X' if client_id == game['player1'] else 'O'
            game['board'][position] = symbol
            
            winner = self.check_winner(game['board'])
            is_draw = all(cell != '' for cell in game['board'])
            
            # Gửi cập nhật cho cả 2 người chơi
            for pid, sock in game['sockets'].items():
                response = {
                    'action': 'board_updated',
                    'board': game['board'],
                    'current_turn': 3 - game['current_turn'],
                    'last_move': position,
                    'last_symbol': symbol
                }
                
                if winner:
                    response['action'] = 'game_over'
                    response['winner'] = 'X' if winner == 1 else 'O'
                    response['winner_id'] = game['player1'] if winner == 1 else game['player2']
                    winner_name = game['player1_name'] if winner == 1 else game['player2_name']
                    print(f"🏆 Game {game_id} kết thúc! {winner_name} thắng với {response['winner']}")
                elif is_draw:
                    response['action'] = 'game_over'
                    response['winner'] = 'draw'
                    print(f"🤝 Game {game_id} kết thúc - Hòa!")
                
                sock.send(json.dumps(response).encode('utf-8'))
            
            # Cập nhật lượt chơi
            if not winner and not is_draw:
                game['current_turn'] = 3 - game['current_turn']
    
    def check_winner(self, board: List[str]) -> int:
        """Kiểm tra người thắng (1 cho X, 2 cho O, 0 nếu chưa)"""
        board_size = 10
        win_length = 5
        
        # Kiểm tra hàng ngang
        for row in range(board_size):
            for col in range(board_size - win_length + 1):
                start = row * board_size + col
                if all(board[start + i] == board[start] and board[start] != '' for i in range(win_length)):
                    return 1 if board[start] == 'X' else 2
        
        # Kiểm tra cột dọc
        for col in range(board_size):
            for row in range(board_size - win_length + 1):
                start = row * board_size + col
                if all(board[start + i * board_size] == board[start] and board[start] != '' for i in range(win_length)):
                    return 1 if board[start] == 'X' else 2
        
        # Kiểm tra đường chéo (từ trái sang phải)
        for row in range(board_size - win_length + 1):
            for col in range(board_size - win_length + 1):
                start = row * board_size + col
                if all(board[start + i * (board_size + 1)] == board[start] and board[start] != '' for i in range(win_length)):
                    return 1 if board[start] == 'X' else 2
        
        # Kiểm tra đường chéo (từ phải sang trái)
        for row in range(board_size - win_length + 1):
            for col in range(win_length - 1, board_size):
                start = row * board_size + col
                if all(board[start + i * (board_size - 1)] == board[start] and board[start] != '' for i in range(win_length)):
                    return 1 if board[start] == 'X' else 2
        
        return 0
    
    def send_game_list(self, client_id: int, client_socket: socket.socket):
        """Gửi danh sách game đang chờ"""
        with self.lock:
            waiting_games = [
                {'game_id': gid, 'player1': g['player1'], 'player1_name': g['player1_name']}
                for gid, g in self.games.items()
                if g['status'] == 'waiting'
            ]
        
        response = {
            'action': 'game_list',
            'games': waiting_games
        }
        client_socket.send(json.dumps(response).encode('utf-8'))
    
    def disconnect_client(self, client_id: int, client_socket: socket.socket):
        """Ngắt kết nối client"""
        with self.lock:
            if client_id in self.clients:
                del self.clients[client_id]
            
            # Xóa game nếu client là người tạo
            games_to_remove = []
            for game_id, game in self.games.items():
                if client_id in game['sockets']:
                    del game['sockets'][client_id]
                
                if not game['sockets']:
                    games_to_remove.append(game_id)
            
            for game_id in games_to_remove:
                del self.games[game_id]
        
        client_socket.close()
        print(f"❌ Client {client_id} ngắt kết nối")
        print(f"   Số client còn lại: {len(self.clients)}")
    
    def shutdown(self):
        """Tắt server"""
        self.server_socket.close()

if __name__ == '__main__':
    server = TicTacToeServer('localhost', 5000)
    server.start()
