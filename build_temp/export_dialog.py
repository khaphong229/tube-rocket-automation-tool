import tkinter as tk
from tkinter import ttk

class ExportDialog:
    def __init__(self, parent, account_count):
        self.parent = parent
        self.account_count = account_count
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Export Accounts")
        self.dialog.geometry("400x350")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.center_window()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text=f"Export {self.account_count} Accounts", 
                               font=('TkDefaultFont', 12, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Export options
        options_frame = ttk.LabelFrame(main_frame, text="Export Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Basic data (always included)
        ttk.Label(options_frame, text="✅ Basic account data (name, sign-in token, device info)", 
                 foreground='green').pack(anchor=tk.W, pady=2)
        
        # Optional data
        self.include_proxy = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Include proxy settings", 
                       variable=self.include_proxy).pack(anchor=tk.W, pady=2)
        
        self.include_real_token = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Include real tokens (⚠️ Sensitive data)", 
                       variable=self.include_real_token).pack(anchor=tk.W, pady=2)
        
        self.include_stats = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Include statistics (email, coins, videos)", 
                       variable=self.include_stats).pack(anchor=tk.W, pady=2)
        
        # Security warning
        warning_frame = ttk.LabelFrame(main_frame, text="⚠️ Security Warning", padding="10")
        warning_frame.pack(fill=tk.X, pady=(0, 20))
        
        warning_text = ("The exported file will contain sensitive information.\n"
                       "• Keep the file secure and don't share it publicly\n"
                       "• Consider encrypting the file for additional security\n"
                       "• Delete the file after use if not needed")
        ttk.Label(warning_frame, text=warning_text, font=('TkDefaultFont', 8), 
                 justify=tk.LEFT, foreground='red').pack()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM)
        
        ttk.Button(button_frame, text="Export", command=self.export).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
    
    def center_window(self):
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def export(self):
        self.result = {
            'include_proxy': self.include_proxy.get(),
            'include_real_token': self.include_real_token.get(),
            'include_stats': self.include_stats.get()
        }
        self.dialog.destroy()
