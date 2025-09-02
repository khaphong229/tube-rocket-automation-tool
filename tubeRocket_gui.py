import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests as ss
import time
import os
from os import path

class TubeRocketGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TubeRocket Tool")
        self.root.geometry("600x500")
        
        self.session = ss.Session()
        self.running = False
        self.thread = None
        
        self.setup_ui()
        self.load_token()
    
    def setup_ui(self):
        # Token frame
        token_frame = ttk.Frame(self.root, padding="10")
        token_frame.pack(fill=tk.X)
        
        ttk.Label(token_frame, text="TubeRocket Token:").pack(anchor=tk.W)
        self.token_entry = ttk.Entry(token_frame, width=50, show="*")
        self.token_entry.pack(fill=tk.X, pady=(5, 0))
        
        # Buttons frame
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(button_frame, text="Start", command=self.start_process)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_process, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_token_btn = ttk.Button(button_frame, text="Save Token", command=self.save_token)
        self.save_token_btn.pack(side=tk.LEFT)
        
        # Status frame
        status_frame = ttk.Frame(self.root, padding="10")
        status_frame.pack(fill=tk.X)
        
        ttk.Label(status_frame, text="Account Info:").pack(anchor=tk.W)
        self.status_label = ttk.Label(status_frame, text="Not connected", foreground="red")
        self.status_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Log frame
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(log_frame, text="Activity Log:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Progress frame
        progress_frame = ttk.Frame(self.root, padding="10")
        progress_frame.pack(fill=tk.X)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
    
    def load_token(self):
        if path.exists("token_tube_rocket.txt"):
            try:
                with open("token_tube_rocket.txt", "r") as f:
                    token = f.readline().strip()
                    self.token_entry.insert(0, token)
            except:
                pass
    
    def save_token(self):
        token = self.token_entry.get().strip()
        if token:
            try:
                with open("token_tube_rocket.txt", "w") as f:
                    f.write(token)
                self.log_message("Token saved successfully!")
                messagebox.showinfo("Success", "Token saved successfully!")
            except Exception as e:
                self.log_message(f"Error saving token: {str(e)}")
                messagebox.showerror("Error", f"Error saving token: {str(e)}")
        else:
            messagebox.showwarning("Warning", "Please enter a token first!")
    
    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def start_process(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showwarning("Warning", "Please enter your TubeRocket token!")
            return
        
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_bar.start()
        
        self.thread = threading.Thread(target=self.run_tuberocket, args=(token,))
        self.thread.daemon = True
        self.thread.start()
    
    def stop_process(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_label.config(text="Stopping...")
        self.log_message("Stop requested by user")
    
    def run_tuberocket(self, token):
        try:
            # Get account info
            self.progress_label.config(text="Connecting...")
            self.log_message("Connecting to TubeRocket...")
            
            head_get_info = {
                "Host": "tuberocket.app:3000",
                "token": token,
            }
            
            get_info = self.session.get("http://tuberocket.app:3000/api/member", headers=head_get_info).json()
            email = get_info["result"]["email"]
            coin = get_info["result"]["coin"]
            
            self.status_label.config(text=f"{email} | Coins: {coin}", foreground="green")
            self.log_message(f"Connected: {email} | Coins: {coin}")
            
            head_run_video = {
                "Host": "tuberocket.app:3000",
                "token": token,
                "Content-Length": "71",
                "Content-Type": "application/json; charset=UTF-8",
            }
            
            cnt = 0
            
            while self.running:
                try:
                    # Get video
                    get_video = self.session.get(
                        "http://tuberocket.app:3000/api/video", headers=head_get_info
                    ).json()
                    id_video = get_video["result"]["videoId"]
                    time_video = get_video["result"]["playSecond"]
                    
                    self.log_message(f"Processing video {id_video} - Wait {time_video} seconds")
                    
                    # Wait for video duration
                    for i in range(time_video, 0, -1):
                        if not self.running:
                            break
                        self.progress_label.config(text=f"Waiting {i} seconds for video {id_video}")
                        time.sleep(1)
                    
                    if not self.running:
                        break
                    
                    # Receive coin
                    data_receive_coin = {
                        "id": id_video,
                        "playCount": 0,
                        "playSecond": 0,
                        "boost": 0,
                        "status": "",
                    }
                    
                    receive = self.session.put(
                        "http://tuberocket.app:3000/api/video",
                        headers=head_run_video,
                        json=data_receive_coin,
                    ).json()
                    
                    received_coin = receive["result"]["coin"]
                    cnt += 1
                    
                    self.log_message(f"#{cnt} | Video {id_video} | Coins: {received_coin}")
                    self.progress_label.config(text=f"Completed #{cnt} videos")
                    
                except Exception as e:
                    self.log_message(f"Error processing video: {str(e)}")
                    if "banned" in str(e).lower() or "expired" in str(e).lower():
                        self.status_label.config(text="Account banned or token expired!", foreground="red")
                        break
                    time.sleep(5)  # Wait before retry
            
        except Exception as e:
            self.log_message(f"Connection error: {str(e)}")
            self.status_label.config(text="Connection failed!", foreground="red")
        
        finally:
            self.running = False
            self.root.after(0, self.stop_process)
            self.progress_label.config(text="Stopped")

def main():
    root = tk.Tk()
    app = TubeRocketGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
