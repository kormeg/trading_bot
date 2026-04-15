
import sys
import tkinter as tk
from tkinter import ttk
import threading
from tkinter.ttk import Progressbar
import time


class Window():

    def __init__(
            self, name="", 
            main_label=False,
            labels=False, 
            entry=False, 
            drop_down_list=False, 
            default_ddl=False, 
            yes_no_buttons=False, 
            exit=False, 
            width=600, 
            height=350,
            progress_bar=False, 
            func=False,
            interrupt=False,
            closing_window=False,
            root=False,
            *args,
            **kwargs):
        if root:
            self.window = tk.Toplevel(root)
        else:
            self.window = tk.Tk()
        self.window.title(name)
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = int((screen_width/2) - width/2)
        y = int((screen_height)/2 - height/2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.interrupt=interrupt
        self.closing_window=closing_window
        self.exit = exit
        self.window.columnconfigure(0, weight=1)
        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure(0, weight=3)
        self.window.rowconfigure(1, weight=2)
        self.window.rowconfigure(2, weight=1)
        self.window.rowconfigure(3, weight=2)
        self.window.rowconfigure(4, weight=1)
        self.window.rowconfigure(5, weight=1)
        self.window.rowconfigure(6, weight=1)
        self.window.rowconfigure(7, weight=1)
        self.window.rowconfigure(8, weight=1)
        labels_map = [[[1, 0, 2]],
                      [[1, 0, 1], [1, 1, 1]],
                      [[1, 0, 1], [1, 0, 2], [1, 1, 1]],
                      [[1, 0, 1], [1, 1, 1], [3, 0, 1], [3, 1, 1]],
                      [[1, 0, 1], [1, 0, 2], [1, 1, 1], [3, 0, 1], [3, 1, 1]],
                      [[1, 0, 1], [1, 0, 2], [1, 1, 1], [3, 0, 1], [3, 0, 2], [3, 1, 1]]]

        if main_label:
            self.label = tk.Label(self.window, text=main_label, wraplength=width*0.8, font=28)
            self.label.grid(row=0, column=0, columnspan=2, sticky="s")

        if labels:
            if type(labels) == str:
                labels = [labels]
            for i in range(len(labels)):
                label = tk.Label(self.window, text=labels[i])#, wraplength=width*0.8, font=28)
                label.grid(row=labels_map[len(labels)-1][i][0], column=labels_map[len(labels)-1][i][1], columnspan=labels_map[len(labels)-1][i][2], sticky="s")

        if entry:
            self.entry = tk.Entry(self.window)
            self.entry.grid(row=3, column=0, columnspan=2)      

        if drop_down_list:
            self.combo = ttk.Combobox(self.window, values=drop_down_list, state="readonly")
            self.combo.set(default_ddl)
            self.combo.grid(row=1, column=0, columnspan=2)
            if not exit:
                self.combo.bind("<<ComboboxSelected>>", self.get_value)
        
        if yes_no_buttons:
            self.yes_button = tk.Button(self.window, text=yes_no_buttons[0], width=10,height=1, command=lambda:self.yes("event"))
            self.no_button = tk.Button(self.window, text=yes_no_buttons[1], width=10,height=1, command=lambda:self.no("event"))
            self.yes_button.grid(row=2,column=0, sticky="e")
            self.no_button.grid(row=2,column=1, sticky="w")
            # self.yes_button.pack(side='left', anchor='e', expand=True)
            # self.no_button.pack(side='right', anchor='w', expand=True)

        if progress_bar:
            self.func = func
            self.args=args
            self.kwargs=kwargs
            self.progress = Progressbar(self.window, orient=tk.HORIZONTAL, length=400, mode='indeterminate')
            
            threading.Thread(target=self.prog_func).start()

        if exit:
            self.button = tk.Button(self.window, text=exit, width=10,height=1, command=lambda:self.get_value("event"))
            self.button.grid(row=4, column=0, columnspan=2)
        
        if interrupt:
            self.window.protocol("WM_DELETE_WINDOW",lambda:self.on_closing())
        if root:
            self.window.transient(root)
            self.window.grab_set()
            self.window.focus_set()
            self.window.wait_window()
        else:
            self.window.mainloop()


    def get_value(self, event):

        try:
            self.entered_value = self.entry.get()
        except:
            pass
        try:
            self.selected_value = self.combo.get()
        except:
            pass
        self.window.destroy()


    def yes(self, event):
        self.yes_no = True
        if self.closing_window:
            sys.exit()
        self.window.destroy()


    def no(self, event):
        self.yes_no = False
        self.window.destroy()


    def prog_func(self):
        self.progress.grid(row=3, column=0, columnspan=2, sticky="n")
        self.progress.start()
        try:
            self.func(*self.args, **self.kwargs)
        except:
            print("error")
        self.progress.stop()
        # self.progress.grid_forget()
        self.window.destroy()

    def on_closing(self):
        Window("Quit", main_label="Do you want to quit?", yes_no_buttons=["Да", "Нет"], closing_window=True)

        
