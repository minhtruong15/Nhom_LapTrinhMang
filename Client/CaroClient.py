import tkinter as tk
from tkinter import messagebox, simpledialog
import socket
import json
import threading
from typing import Dict, Optional
import winsound
import time
from PIL import Image, ImageTk
import math

class TicTacToeClient:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Cờ Caro - Tic Tac Toe Online")
        self.root.geometry("800x900")
        self.root.minsize(600, 700)
        self.root.resizable(True, True)
        self.root.configure(bg='#f5f7fa')
        
        # Cấu hình style
        self.setup_styles()
        
        self.button_animations = {}
        self.animation_active = False
        self.click_count = 0
        
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
        self.is_closing = False
        
        # Xử lý sự kiện đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.exit_game)
        
        # Hiển thị màn hình login trước
        self.show_login_screen()
    
    def setup_styles(self):
        """Cấu hình màu sắc và style"""
        self.bg_color = '#f5f7fa'
        self.fg_color = '#1a1a1a'
        self.x_color = '#ff3b5c'
        self.x_bg = '#ffe0e6'
        self.o_color = '#00d4aa'
        self.o_bg = '#e0f7f4'
        self.button_color = '#ffffff'
        self.button_hover = '#f0f2f5'
        self.button_border = '#d9d9d9'
        self.win_color = '#00aa00'
        self.header_bg = '#1e40af'
        self.header_accent = '#60a5fa'
        self.shadow_color = '#00000010'
        self.primary_btn = '#1e40af'
        self.primary_hover = '#1e3a8a'
        self.secondary_btn = '#0d9488'
        self.secondary_hover = '#0f766e'
    
    def create_rounded_button(self, parent, text, command, bg_color, fg_color, width=15, height=2):
        """Tạo button với bo góc"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=fg_color,
            font=("Segoe UI", 11, "bold"),
            width=width,
            height=height,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.primary_hover if bg_color == self.primary_btn else self.secondary_hover,
            activeforeground=fg_color,
            bd=0,
            padx=15,
            pady=8
        )
        btn.pack(side=tk.LEFT, padx=5, pady=0)
        return btn
    
    def show_login_screen(self):
        """Hiển thị màn hình nhập tên"""
        login_frame = tk.Frame(self.root, bg='#ffffff')
        login_frame.pack(fill=tk.BOTH, expand=True)
        
        logo_frame = tk.Frame(login_frame, bg='#1e40af', height=200)
        logo_frame.pack(fill=tk.X)
        
        logo_label = tk.Label(
            logo_frame,
            text="♟ CỜ CARO ONLINE",
            font=("Segoe UI", 48, "bold"),
            bg='#1e40af',
            fg='#ffffff'
        )
        logo_label.pack(pady=40)
        
        subtitle = tk.Label(
            logo_frame,
            text="Chơi cùng bạn bè trực tuyến",
            font=("Segoe UI", 14),
            bg='#1e40af',
            fg='#60a5fa'
        )
        subtitle.pack(pady=5)
        
        # Info label
        info_label = tk.Label(
            login_frame,
            text="Nhập tên của bạn để bắt đầu",
            font=("Segoe UI", 14, "bold"),
            bg='#ffffff',
            fg='#1a1a1a'
        )
        info_label.pack(pady=30)
        
        # Input frame
        input_frame = tk.Frame(login_frame, bg='#ffffff')
        input_frame.pack(pady=20)
        
        tk.Label(
            input_frame,
            text="Tên của bạn:",
            font=("Segoe UI", 12, "bold"),
            bg='#ffffff',
            fg='#1a1a1a'
        ).pack(side=tk.LEFT, padx=10)
        
        self.name_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 12),
            width=20,
            bg='#f5f7fa',
            fg='#1a1a1a',
            relief=tk.FLAT,
            bd=0
        )
        self.name_entry.pack(side=tk.LEFT, padx=10, ipady=8)
        self.name_entry.focus()
        
        # Nút bắt đầu
        start_btn = tk.Button(
            login_frame,
            text="Bắt Đầu",
            font=("Segoe UI", 14, "bold"),
            bg='#1e40af',
            fg='white',
            padx=40,
            pady=12,
            command=self.start_game_from_login,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground='#1e3a8a'
        )
        start_btn.pack(pady=30)
        
        self.name_entry.bind('<Return>', lambda e: self.start_game_from_login())
    
    def start_game_from_login(self):
        """Bắt đầu game từ màn hình login"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Thông báo", "Vui lòng nhập tên của bạn")
            return
        
        self.player_name = name
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.create_widgets()
        self.connect_to_server()
    
    def create_widgets(self):
        """Tạo giao diện game"""
        header_frame = tk.Frame(self.root, bg=self.header_bg, height=100)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="♟ CỜ CARO ONLINE",
            font=("Segoe UI", 24, "bold"),
            bg=self.header_bg,
            fg='#ffffff'
        )
        title_label.pack(pady=8)
        
        # Status bar
        status_frame = tk.Frame(header_frame, bg=self.header_accent)
        status_frame.pack(fill=tk.X, padx=0, pady=0)
        
        self.status_label = tk.Label(
            status_frame,
            text=f"Người chơi: {self.player_name}",
            font=("Segoe UI", 11),
            bg=self.header_accent,
            fg='#ffffff',
            padx=15,
            pady=8
        )
        self.status_label.pack(fill=tk.X)
        
        # Main content
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Turn label
        self.turn_label = tk.Label(
            main_frame,
            text="Chờ game bắt đầu...",
            font=("Segoe UI", 14, "bold"),
            bg=self.bg_color,
            fg='#1a1a1a',
            pady=10
        )
        self.turn_label.pack()
        
        # Board container để căn giữa
        board_container = tk.Frame(main_frame, bg=self.bg_color)
        board_container.pack(pady=15, padx=10)
        
        board_frame = tk.Frame(board_container, bg='#ffffff', relief=tk.RAISED, bd=0)
        board_frame.pack(padx=10, pady=10)
        
        # Inner board frame với kích thước cố định
        inner_board = tk.Frame(board_frame, bg='#e0e0e0')
        inner_board.pack(padx=10, pady=10)
        
        self.buttons = []
        # Kích thước cố định cho các nút để không bị thay đổi khi click
        button_font = ("Segoe UI", 10, "bold")
        button_width = 3
        button_height = 1
        
        for i in range(100):
            btn = tk.Button(
                inner_board,
                text='',
                font=button_font,
                width=button_width,
                height=button_height,
                bg='#ffffff',
                fg='#333333',
                activebackground='#f0f2f5',
                activeforeground='#000000',
                relief=tk.RAISED,
                cursor="hand2",
                command=lambda pos=i: self.on_button_click(pos),
                bd=1,
                highlightthickness=0,
                padx=2,
                pady=2
            )
            btn.grid(row=i//10, column=i%10, padx=1, pady=1, sticky='nsew')
            self.buttons.append(btn)
        
        # Cấu hình grid để các cột và hàng có kích thước đồng đều - tăng kích thước một chút
        for i in range(10):
            inner_board.grid_columnconfigure(i, weight=1, minsize=38)
            inner_board.grid_rowconfigure(i, weight=1, minsize=38)
        
        control_frame = tk.Frame(main_frame, bg=self.bg_color)
        control_frame.pack(fill=tk.X, pady=15)
        
        btn_frame = tk.Frame(control_frame, bg=self.bg_color)
        btn_frame.pack(fill=tk.X)
        
        self.create_btn = tk.Button(
            btn_frame,
            text="+ Tạo Game",
            font=("Segoe UI", 11, "bold"),
            bg=self.primary_btn,
            fg='white',
            padx=20,
            pady=10,
            command=self.create_game,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.primary_hover
        )
        self.create_btn.pack(side=tk.LEFT, padx=5)
        
        self.join_btn = tk.Button(
            btn_frame,
            text="⚡ Tham Gia Game",
            font=("Segoe UI", 11, "bold"),
            bg=self.secondary_btn,
            fg='white',
            padx=20,
            pady=10,
            command=self.show_join_dialog,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground=self.secondary_hover
        )
        self.join_btn.pack(side=tk.LEFT, padx=5)
        
        self.exit_btn = tk.Button(
            btn_frame,
            text="🚪 Thoát Game",
            font=("Segoe UI", 11, "bold"),
            bg='#dc2626',
            fg='white',
            padx=20,
            pady=10,
            command=self.exit_game,
            relief=tk.FLAT,
            cursor="hand2",
            activebackground='#b91c1c'
        )
        self.exit_btn.pack(side=tk.LEFT, padx=5)
        
        # Info panel
        info_frame = tk.Frame(main_frame, bg='#e8f4f8', relief=tk.FLAT, bd=0)
        info_frame.pack(fill=tk.X, pady=10, padx=5)
        
        self.info_label = tk.Label(
            info_frame,
            text="Chờ kết nối...",
            font=("Segoe UI", 10),
            bg='#e8f4f8',
            fg='#1a1a1a',
            justify=tk.LEFT,
            padx=15,
            pady=10
        )
        self.info_label.pack(fill=tk.X)
    
    def connect_to_server(self):
        """Kết nối đến server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', 8888))
            self.status_label.config(text=f"✓ Đã kết nối - {self.player_name}", fg='#ffffff')
            self.play_sound('connect')
            self.update_info("Kết nối thành công! Tạo hoặc tham gia game.")
            
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
        
        except Exception as e:
            self.status_label.config(text="✗ Lỗi kết nối", fg='#ffcccc')
            messagebox.showerror("Lỗi", f"Không thể kết nối đến server: {e}")
    
    def play_sound(self, sound_type: str):
        """Phát âm thanh cho các sự kiện"""
        try:
            if sound_type == 'move':
                winsound.Beep(400, 100)
            elif sound_type == 'win':
                for i in range(3):
                    winsound.Beep(800, 150)
                    time.sleep(0.1)
            elif sound_type == 'lose':
                winsound.Beep(300, 200)
            elif sound_type == 'connect':
                winsound.Beep(500, 100)
            elif sound_type == 'draw':
                winsound.Beep(600, 150)
        except:
            pass
    
    def animate_button(self, position: int):
        """Hiệu ứng khi click button - không thay đổi kích thước"""
        btn = self.buttons[position]
        # Chỉ thay đổi relief, không thay đổi kích thước
        btn.config(relief=tk.SUNKEN, bd=1)
        self.root.after(100, lambda: btn.config(relief=tk.RAISED, bd=1))
    
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
            self.animate_button(position)
            self.play_sound('move')
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
            turn_color = self.x_color if first_player_symbol == 'X' else self.o_color
            self.turn_label.config(text=turn_text, fg=turn_color)
            
            self.update_info(f"Game bắt đầu! Bạn là {self.player_symbol} vs {self.opponent_name}. {first_player_name} đi trước!")
            messagebox.showinfo("GAME BẮT ĐẦU", f"Ván caro mới bắt đầu!\n{first_player_name} ({first_player_symbol}) đi trước!")
        
        elif action == 'board_updated':
            self.board = message.get('board', [''] * 100)
            self.current_turn = message.get('current_turn', 1)
            self.update_board()
            current_player_symbol = 'X' if self.current_turn == 1 else 'O'
            current_player_name = self.player1_name if self.current_turn == 1 else self.player2_name
            turn_text = f"🎮 Tới lượt của {current_player_symbol} ({current_player_name})"
            turn_color = self.x_color if current_player_symbol == 'X' else self.o_color
            self.turn_label.config(text=turn_text, fg=turn_color)
        
        elif action == 'game_over':
            self.game_active = False
            winner = message.get('winner')
            winning_positions = message.get('winning_positions', [])
            
            # Cập nhật board từ message
            if 'board' in message:
                self.board = message.get('board', [''] * 100)
            
            # Highlight các nút thắng trước
            if winning_positions:
                self.highlight_winning_positions(winning_positions)
                # Đợi một chút để người dùng thấy 5 nút thắng
                self.root.after(500, lambda: self.show_game_over_message(winner))
            else:
                # Nếu hòa, hiển thị ngay
                self.update_board()
                self.show_game_over_message(winner)
        
        elif action == 'game_list':
            games = message.get('games', [])
            self.show_game_list(games)
        
        elif action == 'error':
            messagebox.showerror("Lỗi", message.get('message', 'Lỗi không xác định'))
    
    def show_game_list(self, games: list):
        """Cải tiến dialog chọn game"""
        if not games:
            messagebox.showinfo("Danh sách Game", "Không có game nào đang chờ")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Chọn Game để Tham Gia")
        dialog.geometry("450x350")
        dialog.configure(bg='#ffffff')
        
        title = tk.Label(
            dialog,
            text="📋 Các game đang chờ:",
            font=("Segoe UI", 13, "bold"),
            bg='#ffffff',
            fg='#1a1a1a'
        )
        title.pack(pady=15, padx=10)
        
        for game in games:
            player1_name = game.get('player1_name', f"Player {game['player1']}")
            btn = tk.Button(
                dialog,
                text=f"Game {game['game_id']} - {player1_name}",
                font=("Segoe UI", 11),
                bg=self.primary_btn,
                fg='white',
                width=45,
                padx=15,
                pady=8,
                relief=tk.FLAT,
                cursor="hand2",
                activebackground=self.primary_hover,
                command=lambda gid=game['game_id']: [self.join_game(gid), dialog.destroy()]
            )
            btn.pack(pady=8, padx=10)
    
    def update_board(self):
        """Cập nhật board với animation - giữ kích thước cố định"""
        # Font cố định để không thay đổi kích thước nút
        button_font = ("Segoe UI", 10, "bold")
        
        for i, btn in enumerate(self.buttons):
            symbol = self.board[i]
            if symbol == 'X':
                btn.config(
                    text='X',
                    fg=self.x_color,
                    bg=self.x_bg,
                    disabledforeground=self.x_color,
                    state=tk.DISABLED,
                    font=button_font,
                    width=3,
                    height=1,
                    relief=tk.RAISED,
                    bd=1
                )
            elif symbol == 'O':
                btn.config(
                    text='O',
                    fg=self.o_color,
                    bg=self.o_bg,
                    disabledforeground=self.o_color,
                    state=tk.DISABLED,
                    font=button_font,
                    width=3,
                    height=1,
                    relief=tk.RAISED,
                    bd=1
                )
            else:
                btn.config(
                    text='',
                    bg='#ffffff',
                    fg='#333333',
                    state=tk.NORMAL,
                    font=button_font,
                    width=3,
                    height=1,
                    relief=tk.RAISED,
                    bd=1
                )
    
    def update_info(self, text: str):
        """Cập nhật thông tin"""
        self.info_label.config(text=text)
    
    def highlight_winning_positions(self, winning_positions: list):
        """Highlight 5 nút thắng với màu đặc biệt"""
        # Cập nhật board trước
        self.update_board()
        
        # Highlight các nút thắng
        for pos in winning_positions:
            if 0 <= pos < len(self.buttons):
                btn = self.buttons[pos]
                symbol = self.board[pos]
                if symbol == 'X':
                    btn.config(bg='#ff6b9d', fg='#ffffff')
                elif symbol == 'O':
                    btn.config(bg='#00ffaa', fg='#ffffff')
    
    def show_game_over_message(self, winner: str):
        """Hiển thị thông báo kết thúc game sau khi đã highlight"""
        if winner == 'draw':
            self.turn_label.config(text="🤝 Game kết thúc - Hòa!", fg='#95a5a6')
            self.update_info("Game kết thúc - Hòa! Tạo hoặc tham gia game mới để chơi tiếp.")
            self.play_sound('draw')
            messagebox.showinfo("KẾT QUẢ GAME", "🤝 HÒA!")
        else:
            if winner == self.player_symbol:
                self.turn_label.config(text=f"🎉 Bạn thắng với {winner}!", fg=self.o_color if winner == 'O' else self.x_color)
                self.update_info(f"Bạn thắng với {winner}! Tạo hoặc tham gia game mới để chơi tiếp.")
                self.play_sound('win')
                messagebox.showinfo("KẾT QUẢ GAME", "🎉 BẠN THẮNG!")
            else:
                self.turn_label.config(text=f"😢 Bạn thua với {winner}!", fg=self.x_color if winner == 'X' else self.o_color)
                self.update_info(f"Bạn thua với {winner}! Tạo hoặc tham gia game mới để chơi tiếp.")
                self.play_sound('lose')
                messagebox.showinfo("KẾT QUẢ GAME", "😢 BẠN THUA!")
        
        # Reset board sau khi hiển thị thông báo
        self.root.after(1000, lambda: self.reset_board_after_game())
    
    def reset_board_after_game(self):
        """Reset board sau khi game kết thúc"""
        self.board = [''] * 100
        self.update_board()
    
    def exit_game(self):
        """Thoát game và đóng kết nối"""
        if self.is_closing:
            return
        
        self.is_closing = True
        
        # Xác nhận với người dùng
        if self.game_active:
            if not messagebox.askyesno("Thoát Game", "Bạn đang trong game. Bạn có chắc chắn muốn thoát?"):
                self.is_closing = False
                return
        
        try:
            # Gửi thông báo rời game nếu đang trong game
            if self.socket and self.game_id and self.game_active:
                try:
                    message = {
                        'action': 'leave_game',
                        'game_id': self.game_id,
                        'player_name': self.player_name
                    }
                    self.socket.send(json.dumps(message).encode('utf-8'))
                except:
                    pass
            
            # Đóng kết nối socket
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            
            # Đóng cửa sổ
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            # Nếu có lỗi, vẫn đóng cửa sổ
            try:
                if self.socket:
                    self.socket.close()
            except:
                pass
            self.root.quit()
            self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = TicTacToeClient(root)
    root.mainloop()
