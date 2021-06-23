from tkinter import *
import Dialog

class cDialogBands(Dialog.cDialog):
    def __init__(self, parent, title, AcT_name, bands_name, initial_value):
        self.AcT_name = AcT_name
        self.bands_name = bands_name
        self.checkbutton_bands = [None]*len(self.bands_name)
        self.bands = [None]*len(self.bands_name)
        self.initial_value = initial_value
        Dialog.cDialog.__init__(self, parent, title)

    def body(self, master):
        label_AcT_name = Label(master, text=self.AcT_name, justify="left", font=("Verdana", 10), bd=0)
        label_AcT_name.grid(row=0, column=0, sticky="w")

        result = None   # widget that should be in focus
        for i in range(0, len(self.bands_name)):
            self.bands[i] = BooleanVar(value=0 != (self.initial_value & (1 << i)))
            self.checkbutton_bands[i] = Checkbutton(master, text=self.bands_name[i], variable=self.bands[i], command=None, font=("Verdana", 8), state="normal")
            self.checkbutton_bands[i].grid(row=0, column=i+1, sticky="w")

            if result is None:
                result = self.checkbutton_bands[i]

        return result # initial focus

    def apply(self):
        self.result = 0
        for i in range(0, len(self.bands)):
            if self.bands[i].get():
                self.result += 1 << i


class cDialog_GSM_bands(cDialogBands):
    def __init__(self, parent, initial_value=0):
        cDialogBands.__init__(self, parent, title="Setting GSM bands", AcT_name="GSM bands:", bands_name=["900MHz", "1.8GHz", "850MHz", "1.9GHz"], initial_value=initial_value)


class cDialog_LTE_cat_M1_bands(cDialogBands):
    def __init__(self, parent, initial_value=0):
        cDialogBands.__init__(self, parent, title="Setting LTE cat. M1 bands", AcT_name="LTE cat. M1 bands:", bands_name=["B1", "B2", "B3", "B4", "B5", "B8", "B12", "B13", "B18", "B19", "B20", "B26", "B28", "B39"], initial_value=initial_value)


class cDialog_LTE_cat_NB1_bands(cDialogBands):
    def __init__(self, parent, initial_value=0):
        cDialogBands.__init__(self, parent, title="Setting LTE cat. NB1 bands", AcT_name="LTE cat. NB1 bands:", bands_name=["B1", "B2", "B3", "B4", "B5", "B8", "B12", "B13", "B18", "B19", "B20", "B26", "B28"], initial_value=initial_value)
