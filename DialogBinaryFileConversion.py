from tkinter import *
import Dialog

class cDialogBinaryFileConverter(Dialog.cDialog):
    def __init__(self, parent, callback_convert):
        self.callback_convert = callback_convert
        # Style definitions
        self.style = ttk.Style()
        # helpers.OUT(str(self.style.theme_names()))
        self.style.theme_use('default')
        self.style.configure("BinaryFileConverter.Horizontal.TProgressbar", foreground='black', throughcolor="blue", background='green')
        Dialog.cDialog.__init__(self, parent, title="Binary file converter")

    def body(self, master):
        label_AcT_name = Label(master, text="Test", justify="left", font=("Verdana", 10), bd=0)
        label_AcT_name.grid(row=0, column=0, sticky="w")
        self.progressbar = ttk.Progressbar(master, style="BinaryFileConverter.Horizontal.TProgressbar", orient="horizontal", mode="determinate", value=0, maximum=self.callback_convert(0))
        self.progressbar.grid(row=10, column=0, columnspan=2, padx=5, pady=10, sticky="we")

        return self.progressbar  # initial focus

    def apply(self):
        return

    def progress_change_color(self, color):
        self.style.configure("BinaryFileConverter.Horizontal.TProgressbar", background=color)
        self.progressbar.configure(style="BinaryFileConverter.Horizontal.TProgressbar")
        self.progressbar.update()


    def __progressbar_update__(self):
        self.progressbar.configure(value=self.address)
        self.progressbar.update()