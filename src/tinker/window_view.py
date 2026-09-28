import tkinter as tk 

def make_input_form(window, fields): 
    """Makes for filling the input"""
    entries = {}
    for field in fields: 
        row = tk.Frame(window)
        label = tk.Label(row, text=field+":", anchor='w')
        entry = tk.Entry(row,width=20)
        row.pack(side=tk.TOP, fill=tk.X, pady=2)
        label.pack(side=tk.LEFT)
        entry.pack(side=tk.LEFT, padx=5, fill=tk.X)
        entries[field] = entry
    return entries 