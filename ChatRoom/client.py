import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

class AdvancedChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client = None
        self.running = False
        self.my_nickname = ""

        self.win = tk.Tk()
        self.win.title("Python 進階聊天室")
        self.win.geometry("450x550")

        self.login_frame = tk.Frame(self.win, padx=20, pady=20)
        self.chat_frame = tk.Frame(self.win, padx=10, pady=10)

        self.setup_login_ui()
        self.login_frame.pack(fill=tk.BOTH, expand=True)

        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.win.mainloop()

    def setup_login_ui(self):
        # 帳密輸入
        tk.Label(self.login_frame, text="帳號:").pack()
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.pack(pady=2)
        
        tk.Label(self.login_frame, text="密碼:").pack()
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.pack(pady=2)
        
        # 登入與註冊按鈕 (並排)
        btn_frame = tk.Frame(self.login_frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="登入", bg="lightblue", width=10, command=self.login_as_user).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="線上註冊", bg="lightgreen", width=10, command=self.register_user).pack(side=tk.LEFT, padx=5)

        tk.Frame(self.login_frame, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=15)

        # 訪客
        tk.Label(self.login_frame, text="訪客暱稱:").pack()
        self.guest_entry = tk.Entry(self.login_frame)
        self.guest_entry.pack(pady=2)
        self.guest_entry.insert(0, "訪客")
        tk.Button(self.login_frame, text="訪客進入", bg="lightgray", command=self.login_as_guest).pack(pady=5)

    def setup_chat_ui(self):
        # 聊天文字區域
        self.text_area = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, font=("Arial", 11))
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 重要：配置標籤顏色與對齊方式
        # 本人訊息：綠色背景，靠右對齊
        self.text_area.tag_configure("self_msg", background="#D9FDD3", justify="right")
        # 他人訊息：無背景（或自訂），靠左對齊
        self.text_area.tag_configure("other_msg", justify="left")
        # 系統訊息：灰色字，居中對齊
        self.text_area.tag_configure("system_msg", foreground="gray", justify="center")
        
        self.text_area.config(state='disabled')

        # 輸入框與發送
        input_frame = tk.Frame(self.chat_frame)
        input_frame.pack(fill=tk.X)
        self.input_area = tk.Entry(input_frame, font=("Arial", 11))
        self.input_area.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_area.bind("<Return>", lambda event: self.send_message())

        tk.Button(input_frame, text="發送", width=10, bg="lightblue", command=self.send_message).pack(side=tk.RIGHT)

    def connect_server(self):
        if self.client: return True
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.host, self.port))
            return True
        except:
            messagebox.showerror("錯誤", "無法連線到伺服器！")
            return False

    def login_as_user(self):
        if not self.connect_server(): return
        u, p = self.username_entry.get().strip(), self.password_entry.get().strip()
        self.client.send(f"LOGIN:{u}:{p}".encode('utf-8'))
        
        res = self.client.recv(1024).decode('utf-8')
        if res == "AUTH_SUCCESS":
            self.my_nickname = f"{u}(成員)"
            self.enter_chat_room()
        else:
            messagebox.showerror("失敗", res.split(":")[1] if ":" in res else "登入失敗")
            self.disconnect()

    def register_user(self):
        if not self.connect_server(): return
        u, p = self.username_entry.get().strip(), self.password_entry.get().strip()
        self.client.send(f"REGISTER:{u}:{p}".encode('utf-8'))
        
        res = self.client.recv(1024).decode('utf-8')
        if res == "REG_SUCCESS":
            messagebox.showinfo("成功", "註冊成功！現在可以使用該帳號登入。")
        else:
            messagebox.showerror("失敗", res.split(":")[1] if ":" in res else "註冊失敗")
        self.disconnect()

    def login_as_guest(self):
        if not self.connect_server(): return
        g = self.guest_entry.get().strip()
        self.client.send(f"GUEST:{g}".encode('utf-8'))
        
        res = self.client.recv(1024).decode('utf-8')
        if res == "AUTH_SUCCESS":
            self.my_nickname = f"{g}(訪客)"
            self.enter_chat_room()

    def enter_chat_room(self):
        self.login_frame.pack_forget()
        self.setup_chat_ui()
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        self.running = True
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def send_message(self):
        msg = self.input_area.get().strip()
        if msg:
            self.client.send(msg.encode('utf-8'))
            self.input_area.delete(0, tk.END)

    def receive_messages(self):
        while self.running:
            try:
                data = self.client.recv(1024).decode('utf-8')
                if data.startswith("MSG:"):
                    # 解析格式 MSG:發送者:內容
                    _, sender, content = data.split(":", 2)
                    
                    self.text_area.config(state='normal')
                    
                    if sender == "【系統】":
                        self.text_area.insert(tk.END, f"{content}\n", "system_msg")
                    elif sender == self.my_nickname:
                        # 本人發送的訊息：套用 self_msg 標籤 (背景綠、靠右)
                        self.text_area.insert(tk.END, f"我: {content}\n", "self_msg")
                    else:
                        # 他人發送的訊息：套用 other_msg 標籤 (靠左)
                        self.text_area.insert(tk.END, f"{sender}: {content}\n", "other_msg")
                    
                    self.text_area.yview(tk.END)
                    self.text_area.config(state='disabled')
            except:
                break

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None

    def stop(self):
        self.running = False
        self.disconnect()
        self.win.destroy()

if __name__ == "__main__":
    AdvancedChatClient('127.0.0.1', 55555)