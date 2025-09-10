import tkinter as tk
from tkinter import ttk
from datetime import datetime

class ImportDialog:
    def __init__(self, parent, import_data):
        self.parent = parent
        self.import_data = import_data
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Import Accounts")
        self.dialog.geometry("500x450")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.center_window()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File info
        info_frame = ttk.LabelFrame(main_frame, text="File Information", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        export_info = self.import_data.get('export_info', {})
        accounts = self.import_data.get('accounts', [])
        
        info_text = f"Tool: {export_info.get('tool', 'Unknown')}\n"
        info_text += f"Export Date: {export_info.get('export_date', 'Unknown')}\n"
        info_text += f"Accounts Found: {len(accounts)}"
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Preview accounts
        preview_frame = ttk.LabelFrame(main_frame, text="Account Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create treeview for preview
        columns = ('Name', 'Sign-in Token', 'Proxy', 'Real Token')
        preview_tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=8)
        
        preview_tree.heading('Name', text='Account Name')
        preview_tree.heading('Sign-in Token', text='Sign-in Token')
        preview_tree.heading('Proxy', text='Proxy')
        preview_tree.heading('Real Token', text='Real Token')
        
        preview_tree.column('Name', width=120)
        preview_tree.column('Sign-in Token', width=100)
        preview_tree.column('Proxy', width=80)
        preview_tree.column('Real Token', width=80)
        
        # Add accounts to preview
        for account in accounts[:10]:  # Show first 10 accounts
            name = account.get('name', 'Unknown')
            signin_token = '✅ Yes' if account.get('token_signin') else '❌ No'
            proxy = '✅ Yes' if account.get('proxy') else '❌ No'
            real_token = '✅ Yes' if account.get('token') else '❌ No'
            
            preview_tree.insert('', tk.END, values=(name, signin_token, proxy, real_token))
        
        if len(accounts) > 10:
            preview_tree.insert('', tk.END, values=(f"... and {len(accounts) - 10} more accounts", '', '', ''))
        
        preview_tree.pack(fill=tk.BOTH, expand=True)
        
        # Import options
        options_frame = ttk.LabelFrame(main_frame, text="Import Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.overwrite_existing = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Overwrite existing accounts (same name)", 
                       variable=self.overwrite_existing).pack(anchor=tk.W, pady=2)
        
        self.import_proxy = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Import proxy settings", 
                       variable=self.import_proxy).pack(anchor=tk.W, pady=2)
        
        self.import_real_token = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Import real tokens (if available)", 
                       variable=self.import_real_token).pack(anchor=tk.W, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM)
        
        ttk.Button(button_frame, text="Import", command=self.import_accounts).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
    
    def center_window(self):
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def import_accounts(self):
        self.result = {
            'overwrite_existing': self.overwrite_existing.get(),
            'import_proxy': self.import_proxy.get(),
            'import_real_token': self.import_real_token.get()
        }
        self.dialog.destroy()
