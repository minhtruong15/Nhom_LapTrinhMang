import tkinter as tk
from tkinter import messagebox, simpledialog
import socket
import json
import threading
from typing import Dict, Optional

class TicTacToeClient:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Cờ Caro - Tic Tac Toe")
        self.root.geometry("800x900")
        self.root.configure(bg='#ffffff')
        
        # Cấu hình style
        self.setup_styles()
        
        # Biến trạng thái
        self.socket: Optional[socket.socket] = None
        self.game_id: Optional[int] = None
        self.player_symbol: Optional[str] = None
        self.player_name: str = ""
        self.board = [''] * 100
        self.current_turn = 1
        self.game_active = False
        self.opponent_name: str = ""
        self.player1_name: str = ""
        self.player2_name: str = ""
        
        # Hiển thị màn hình login trước
        self.show_login_screen()
    
    def setup_styles(self):
        """Cấu hình màu sắc và style"""
        self.bg_color = '#ffffff'
        self.fg_color = '#000000'
        self.x_color = '#e74c3c'  # Đỏ đậm cho X
        self.x_bg = '#ffeaea'     # Nền hồng nhạt cho X
        self.o_color = '#27ae60'  # Xanh lá đậm cho O
        self.o_bg = '#e8f8f5'     # Nền xanh nhạt cho O
        self.button_color = '#f8f9fa'
        self.button_hover = '#dfe6e9'
        self.win_color = '#00aa00'
        self.header_bg = '#2c3e50'
    
    def show_login_screen(self):
        """Hiển thị màn hình nhập tên"""
        login_frame = tk.Frame(self.root, bg='#ffffff')
        login_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo
        logo_label = tk.Label(
            login_frame,
            text="🎮 CỜ CARO ONLINE",
            font=("Arial", 32, "bold"),
            bg='#ffffff',
            fg='#2c3e50'
        )
        logo_label.pack(pady=40)
        
        # Hướng dẫn
        info_label = tk.Label(
            login_frame,
            text="Nhập tên của bạn để bắt đầu",
            font=("Arial", 14),
            bg='#ffffff',
            fg='#555555'
        )
        info_label.pack(pady=10)
        
        # Input tên
        name_frame = tk.Frame(login_frame, bg='#ffffff')
        name_frame.pack(pady=20)
        
        tk.Label(
            name_frame,
            text="Tên của bạn:",
            font=("Arial", 12),
            bg='#ffffff',
            fg='#000000'
        ).pack(side=tk.LEFT, padx=10)
        
        self.name_entry = tk.Entry(
            name_frame,
            font=("Arial", 12),
            width=20,
            bg='#e0e0e0',
            fg='#000000'
        )
        self.name_entry.pack(side=tk.LEFT, padx=10)
        self.name_entry.focus()
        
        # Nút bắt đầu
        start_btn = tk.Button(
            login_frame,
            text="Bắt Đầu",
            font=("Arial", 14, "bold"),
            bg='#2c3e50',
            fg='white',
            padx=30,
            pady=10,
            command=self.start_game_from_login
        )
        start_btn.pack(pady=20)
        
        # Bind Enter key
        self.name_entry.bind('<Return>', lambda e: self.start_game_from_login())
    
    def start_game_from_login(self):
        """Bắt đầu game từ màn hình login"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Thông báo", "Vui lòng nhập tên của bạn")
            return
        
        self.player_name = name
        
        # Xóa login frame
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Tạo giao diện game
        self.create_widgets()
        
        # Kết nối server
        self.connect_to_server()
    
    def create_widgets(self):
        """Tạo giao diện game"""
        # Header
        header_frame = tk.Frame(self.root, bg=self.header_bg, height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        title_label = tk.Label(
            header_frame,
            text="🎮 CỜ CARO ONLINE (5 Ô THẮNG)",
            font=("Arial", 24, "bold"),
            bg=self.header_bg,
            fg='#ffffff'
        )
        title_label.pack(pady=10)
        
        self.status_label = tk.Label(
            header_frame,
            text=f"Người chơi: {self.player_name}",
            font=("Arial", 12),
            bg=self.header_bg,
            fg='#95e1d3'
        )
        self.status_label.pack()
        
        # Main content
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.turn_label = tk.Label(
            main_frame,
            text="Chờ game bắt đầu...",
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
            fg='#2c3e50',
            pady=10
        )
        self.turn_label.pack()
        
        # Game board
        board_frame = tk.Frame(main_frame, bg='#cccccc', relief=tk.SUNKEN, bd=3)
        board_frame.pack(pady=10)
        
        self.buttons = []
        for i in range(100):
            btn = tk.Button(
                board_frame,
                text='',
                font=("Arial", 10, "bold"),
                width=2,
                height=0,
                bg='#f8f9fa',
                fg='#333333',
                activebackground='#dfe6e9',
                activeforeground='#000000',
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda pos=i: self.on_button_click(pos)
            )
            btn.grid(row=i//10, column=i%10, padx=1, pady=1)
            self.buttons.append(btn)
        
        # Control panel
        control_frame = tk.Frame(main_frame, bg=self.bg_color)
        control_frame.pack(fill=tk.X, pady=20)
        
        self.create_btn = tk.Button(
            control_frame,
            text="➕ Tạo Game Mới",
            font=("Arial", 12, "bold"),
            bg='#ff6b6b',
            fg='white',
            padx=15,
            pady=10,
            command=self.create_game,
            relief=tk.RAISED,
            bd=2
        )
        self.create_btn.pack(side=tk.LEFT, padx=5)
        
        self.join_btn = tk.Button(
            control_frame,
            text="🔗 Tham Gia Game",
            font=("Arial", 12, "bold"),
            bg='#4ecdc4',
            fg='white',
            padx=15,
            pady=10,
            command=self.show_join_dialog,
            relief=tk.RAISED,
            bd=2
        )
        self.join_btn.pack(side=tk.LEFT, padx=5)
        
        # Info panel
        info_frame = tk.Frame(main_frame, bg='#e0e0e0', relief=tk.SUNKEN, bd=2)
        info_frame.pack(fill=tk.X, pady=10)
        
        self.info_label = tk.Label(
            info_frame,
            text="Chờ kết nối...",
            font=("Arial", 11),
            bg='#e0e0e0',
            fg='#000000',
            justify=tk.LEFT,
            padx=10,
            pady=10
        )
        self.info_label.pack(fill=tk.X)
    
    def connect_to_server(self):
        """Kết nối đến server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', 5000))
            self.status_label.config(text=f"✅ Đã kết nối - {self.player_name}", fg='#00aa00')
            self.update_info("Kết nối thành công! Tạo hoặc tham gia game.")
            
            # Bắt đầu thread nhận tin nhắn
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
        
        except Exception as e:
            self.status_label.config(text="❌ Lỗi kết nối", fg='#ff0000')
            messagebox.showerror("Lỗi", f"Không thể kết nối đến server: {e}")
    
    def create_game(self):
        """Tạo game mới"""
        if not self.socket:
            messagebox.showerror("Lỗi", "Chưa kết nối đến server")
            return
        
        try:
            message = {'action': 'create_game', 'player_name': self.player_name}
            self.socket.send(json.dumps(message).encode('utf-8'))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi tạo game: {e}")
    
    def show_join_dialog(self):
        """Hiển thị dialog tham gia game"""
        if not self.socket:
            messagebox.showerror("Lỗi", "Chưa kết nối đến server")
            return
        
        try:
            message = {'action': 'list_games'}
            self.socket.send(json.dumps(message).encode('utf-8'))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi lấy danh sách game: {e}")
    
    def join_game(self, game_id: int):
        """Tham gia game"""
        if not self.socket:
            messagebox.showerror("Lỗi", "Chưa kết nối đến server")
            return
        
        try:
            message = {'action': 'join_game', 'game_id': game_id, 'player_name': self.player_name}
            self.socket.send(json.dumps(message).encode('utf-8'))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi tham gia game: {e}")
    
    def on_button_click(self, position: int):
        """Xử lý click nút"""
        if not self.game_active or not self.socket:
            messagebox.showwarning("Thông báo", "Game chưa bắt đầu")
            return
        
        if self.board[position] != '':
            messagebox.showwarning("Thông báo", "Ô này đã được đánh")
            return
        
        try:
            message = {
                'action': 'move',
                'game_id': self.game_id,
                'position': position
            }
            self.socket.send(json.dumps(message).encode('utf-8'))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi gửi nước đi: {e}")
    
    def receive_messages(self):
        """Nhận tin nhắn từ server"""
        while True:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                message = json.loads(data)
                self.handle_message(message)
            
            except Exception as e:
                print(f"Lỗi nhận tin nhắn: {e}")
                break
    
    def handle_message(self, message: Dict):
        """Xử lý tin nhắn từ server"""
        action = message.get('action')
        
        if action == 'game_created':
            self.game_id = message.get('game_id')
            self.player_symbol = message.get('player_symbol')
            self.update_info(f"Game {self.game_id} được tạo. Bạn là {self.player_symbol}. Chờ người chơi khác...")
        
        elif action == 'game_started':
            self.game_id = message.get('game_id')
            self.player_symbol = message.get('player_symbol')
            self.board = message.get('board', [''] * 100)
            self.current_turn = message.get('current_turn', 1)
            self.game_active = True
            self.player1_name = message.get('player1_name', 'Player 1')
            self.player2_name = message.get('player2_name', 'Player 2')
            self.opponent_name = self.player2_name if self.player_symbol == 'X' else self.player1_name
            
            self.update_board()
            
            first_player_symbol = message.get('first_player_symbol', 'X')
            first_player_name = message.get('first_player_name', self.player1_name)
            turn_text = f"🎮 Tới lượt của {first_player_symbol} ({first_player_name})"
            turn_color = '#e74c3c' if first_player_symbol == 'X' else '#27ae60'
            self.turn_label.config(text=turn_text, fg=turn_color)
            
            self.update_info(f"Game bắt đầu! Bạn là {self.player_symbol} ({self.player_name}) vs {self.opponent_name}. {first_player_name} đi trước!")
            messagebox.showinfo("Bắt Đầu Ván Mới", f"Ván mới bắt đầu!\n\nBạn: {self.player_symbol} ({self.player_name})\nĐối thủ: {self.opponent_name}\n\n{first_player_name} đi trước!")
        
        elif action == 'board_updated':
            self.board = message.get('board', [''] * 100)
            self.current_turn = message.get('current_turn', 1)
            self.update_board()
            current_player_symbol = 'X' if self.current_turn == 1 else 'O'
            current_player_name = self.player1_name if self.current_turn == 1 else self.player2_name
            turn_text = f"🎮 Tới lượt của {current_player_symbol} ({current_player_name})"
            turn_color = '#e74c3c' if current_player_symbol == 'X' else '#27ae60'
            self.turn_label.config(text=turn_text, fg=turn_color)
        
        elif action == 'game_over':
            self.game_active = False
            winner = message.get('winner')
            if winner == 'draw':
                messagebox.showinfo("Kết thúc", "🤝 Hòa!")
                self.turn_label.config(text="🤝 Game kết thúc - Hòa!", fg='#95a5a6')
                self.update_info("Game kết thúc - Hòa! Tạo hoặc tham gia game mới để chơi tiếp.")
            else:
                if winner == self.player_symbol:
                    messagebox.showinfo("Kết thúc", f"🎉 Bạn thắng! ({winner})")
                    self.turn_label.config(text=f"🎉 Bạn thắng với {winner}!", fg='#27ae60')
                    self.update_info(f"Bạn thắng với {winner}! Tạo hoặc tham gia game mới để chơi tiếp.")
                else:
                    messagebox.showinfo("Kết thúc", f"😢 Bạn thua! ({winner})")
                    self.turn_label.config(text=f"😢 Bạn thua với {winner}!", fg='#e74c3c')
                    self.update_info(f"Bạn thua với {winner}! Tạo hoặc tham gia game mới để chơi tiếp.")
            
            # Tự động reset bàn đấu
            self.board = [''] * 100
            self.update_board()
        
        elif action == 'game_list':
            games = message.get('games', [])
            self.show_game_list(games)
        
        elif action == 'error':
            messagebox.showerror("Lỗi", message.get('message', 'Lỗi không xác định'))
    
    def show_game_list(self, games: list):
        """Hiển thị danh sách game"""
        if not games:
            messagebox.showinfo("Danh sách Game", "Không có game nào đang chờ")
            return
        
        # Tạo dialog chọn game
        dialog = tk.Toplevel(self.root)
        dialog.title("Chọn Game")
        dialog.geometry("400x300")
        dialog.configure(bg=self.bg_color)
        
        label = tk.Label(
            dialog,
            text="Chọn game để tham gia:",
            font=("Arial", 12),
            bg=self.bg_color,
            fg=self.fg_color
        )
        label.pack(pady=10)
        
        for game in games:
            player1_name = game.get('player1_name', f"Player {game['player1']}")
            btn = tk.Button(
                dialog,
                text=f"Game {game['game_id']} - {player1_name}",
                font=("Arial", 11),
                bg=self.button_color,
                fg=self.fg_color,
                width=40,
                command=lambda gid=game['game_id']: [self.join_game(gid), dialog.destroy()]
            )
            btn.pack(pady=5)
    
    def update_board(self):
        """Cập nhật giao diện bảng với màu đẹp"""
        for i, btn in enumerate(self.buttons):
            symbol = self.board[i]
            if symbol == 'X':
                btn.config(
                    text='X',
                    fg=self.x_color,
                    bg=self.x_bg,
                    disabledforeground=self.x_color,
                    state=tk.DISABLED
                )
            elif symbol == 'O':
                btn.config(
                    text='O',
                    fg=self.o_color,
                    bg=self.o_bg,
                    disabledforeground=self.o_color,
                    state=tk.DISABLED
                )
            else:
                btn.config(
                    text='',
                    bg='#f8f9fa',
                    state=tk.NORMAL
                )
    
    def update_info(self, text: str):
        """Cập nhật thông tin"""
        self.info_label.config(text=text)

if __name__ == '__main__':
    root = tk.Tk()
    app = TicTacToeClient(root)
    root.mainloop()
