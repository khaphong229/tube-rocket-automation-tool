import tkinter as tk
from tkinter import ttk, messagebox

class AccountDialog:
    def __init__(self, parent, account_data=None):
        self.parent = parent
        self.account_data = account_data
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Account" if not account_data else "Edit Account")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.center_window()
        
        if account_data:
            self.load_account_data()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Basic Info Tab
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="Basic Info")
        
        # Account name
        ttk.Label(basic_frame, text="Account Name:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.name_entry = ttk.Entry(basic_frame, width=50)
        self.name_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        # Sign-in Token
        ttk.Label(basic_frame, text="Sign-in Token:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.token_signin_entry = ttk.Entry(basic_frame, width=50, show="*")
        self.token_signin_entry.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        # Show/Hide token button
        self.show_token_btn = ttk.Button(basic_frame, text="Show", command=self.toggle_token_visibility)
        self.show_token_btn.grid(row=1, column=3, padx=(5, 0), pady=(0, 10))
        
        # Info about real token
        token_info = ttk.Label(basic_frame, text="Real token will be obtained automatically from sign-in", 
                              font=('TkDefaultFont', 8), foreground='gray')
        token_info.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Device Info Tab
        device_frame = ttk.Frame(notebook, padding="10")
        notebook.add(device_frame, text="Device Info")
        
        # Version Code
        ttk.Label(device_frame, text="Version Code:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.version_code_var = tk.IntVar(value=187)
        self.version_code_spin = ttk.Spinbox(device_frame, from_=100, to=999, textvariable=self.version_code_var, width=15)
        self.version_code_spin.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))
        
        # Android Version
        ttk.Label(device_frame, text="Android Version:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.android_var = tk.IntVar(value=29)
        self.android_spin = ttk.Spinbox(device_frame, from_=21, to=34, textvariable=self.android_var, width=15)
        self.android_spin.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))
        
        # Device ID
        ttk.Label(device_frame, text="Device ID:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.device_entry = ttk.Entry(device_frame, width=50)
        self.device_entry.grid(row=2, column=1, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        # Locale
        ttk.Label(device_frame, text="Locale:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        self.locale_var = tk.StringVar(value="VN")
        self.locale_combo = ttk.Combobox(device_frame, textvariable=self.locale_var, values=["VN", "US", "EN", "TH", "ID"], width=15)
        self.locale_combo.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        # Device Token
        ttk.Label(device_frame, text="Device Token:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        self.device_token_entry = ttk.Entry(device_frame, width=50)
        self.device_token_entry.grid(row=4, column=1, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        # Network Tab
        network_frame = ttk.Frame(notebook, padding="10")
        notebook.add(network_frame, text="Network & Settings")
        
        # Proxy
        ttk.Label(network_frame, text="Proxy (optional):").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.proxy_entry = ttk.Entry(network_frame, width=50)
        self.proxy_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        # Test proxy button
        self.test_proxy_btn = ttk.Button(network_frame, text="Test", command=self.test_proxy)
        self.test_proxy_btn.grid(row=0, column=3, padx=(5, 0), pady=(0, 10))
        
        # Proxy format info
        proxy_info = ttk.Label(network_frame, text="Format: http://ip:port or http://user:pass@ip:port", font=('TkDefaultFont', 8))
        proxy_info.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Delay
        ttk.Label(network_frame, text="Delay (seconds):").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.delay_var = tk.IntVar(value=5)
        self.delay_spin = ttk.Spinbox(network_frame, from_=1, to=60, textvariable=self.delay_var, width=10)
        self.delay_spin.grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        # Notes
        ttk.Label(network_frame, text="Notes:").grid(row=3, column=0, sticky=tk.NW, pady=(0, 5))
        self.notes_text = tk.Text(network_frame, width=50, height=6)
        self.notes_text.grid(row=3, column=1, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, pady=(20, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save_account).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
        
        # Configure grid weights
        basic_frame.columnconfigure(1, weight=1)
        device_frame.columnconfigure(1, weight=1)
        network_frame.columnconfigure(1, weight=1)
    
    def center_window(self):
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def toggle_token_visibility(self):
        if self.token_signin_entry.cget("show") == "*":
            self.token_signin_entry.config(show="")
            self.show_token_btn.config(text="Hide")
        else:
            self.token_signin_entry.config(show="*")
            self.show_token_btn.config(text="Show")
    
    def load_account_data(self):
        self.name_entry.insert(0, self.account_data['name'])
        self.token_signin_entry.insert(0, self.account_data['token_signin'])
        self.version_code_var.set(self.account_data['version_code'])
        self.android_var.set(self.account_data['android'])
        self.device_entry.insert(0, self.account_data['device'])
        self.locale_var.set(self.account_data['locale'])
        self.device_token_entry.insert(0, self.account_data['device_token'])
        self.proxy_entry.insert(0, self.account_data['proxy'])
        self.delay_var.set(self.account_data['delay'])
        if 'notes' in self.account_data['config']:
            self.notes_text.insert(tk.END, self.account_data['config']['notes'])
    
    def save_account(self):
        name = self.name_entry.get().strip()
        token_signin = self.token_signin_entry.get().strip()
        
        if not name:
            messagebox.showwarning("Warning", "Please enter account name!")
            return
        
        if not token_signin:
            messagebox.showwarning("Warning", "Please enter sign-in token!")
            return
        
        # Auto-convert proxy format if provided
        proxy = self.proxy_entry.get().strip()
        if proxy:
            proxy = self.parse_proxy(proxy)
        
        self.result = {
            'name': name,
            'token_signin': token_signin,
            'version_code': self.version_code_var.get(),
            'android': self.android_var.get(),
            'device': self.device_entry.get().strip(),
            'locale': self.locale_var.get(),
            'device_token': self.device_token_entry.get().strip(),
            'proxy': proxy,
            'delay': self.delay_var.get(),
            'config': {
                'notes': self.notes_text.get(1.0, tk.END).strip()
            }
        }
        
        self.dialog.destroy()
    
    def parse_proxy(self, proxy_string):
        """Convert various proxy formats to standard format"""
        proxy_string = proxy_string.strip()
        
        # Already in correct format
        if proxy_string.startswith(('http://', 'https://', 'socks5://')):
            return proxy_string
        
        parts = proxy_string.split(':')
        
        if len(parts) == 2:
            # Format: ip:port
            ip, port = parts
            return f"http://{ip}:{port}"
        
        elif len(parts) == 4:
            # Format: ip:port:username:password or ip:username:password:port
            ip = parts[0]
            
            # Try to determine if second part is port or username
            try:
                port = int(parts[1])
                username = parts[2]
                password = parts[3]
                # Format: ip:port:username:password
                return f"http://{username}:{password}@{ip}:{port}"
            except ValueError:
                # Format: ip:username:password:port
                username = parts[1]
                password = parts[2]
                port = parts[3]
                return f"http://{username}:{password}@{ip}:{port}"
        
        elif len(parts) == 3:
            # Format: ip:username:password (assuming default port 8080)
            ip, username, password = parts
            return f"http://{username}:{password}@{ip}:8080"
        
        elif '@' in proxy_string:
            # Format: username:password@ip:port
            auth_part, server_part = proxy_string.split('@')
            return f"http://{auth_part}@{server_part}"
        
        # Return original if can't parse
        return proxy_string
    
    def test_proxy(self):
        proxy_url = self.proxy_entry.get().strip()
        if not proxy_url:
            messagebox.showwarning("Warning", "Please enter a proxy URL first!")
            return
        
        # Convert format before testing
        proxy_url = self.parse_proxy(proxy_url)
        
        # Disable button during test
        self.test_proxy_btn.config(state='disabled', text='Testing...')
        self.dialog.update()
        
        try:
            import requests
            import time
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            start_time = time.time()
            response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                response_data = response.json()
                ip = response_data.get('origin', 'Unknown')
                latency = round((end_time - start_time) * 1000, 2)
                messagebox.showinfo("Proxy Test", f"✅ Proxy working!\n\nOriginal: {self.proxy_entry.get()}\nConverted: {proxy_url}\nIP: {ip}\nLatency: {latency}ms")
                
                # Update the entry with converted format
                self.proxy_entry.delete(0, tk.END)
                self.proxy_entry.insert(0, proxy_url)
            else:
                messagebox.showerror("Proxy Test", f"❌ Proxy failed!\nStatus Code: {response.status_code}")
                
        except Exception as e:
            messagebox.showerror("Proxy Test", f"❌ Proxy test failed!\nError: {str(e)}")
        
        finally:
            self.test_proxy_btn.config(state='normal', text='Test')
