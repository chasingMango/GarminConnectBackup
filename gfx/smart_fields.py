from tkinter import *

class Smart_entry(Entry):

    textvar = None
    _name = None
    _label = None

    def __init__(self,toplevel,column,row,width=50,content="",name=None,isPassword=False,autoPack=True,label_text=None):
        
        if label_text is not None:
            label = Label(toplevel,text=label_text)
            label.pack(anchor=W)
            self._set_label(label)
        
        self.textvar = StringVar(toplevel,content,name)
        Entry.__init__(self,toplevel,textvariable=self.textvar,width=width)
        #self.config(column=column, row=row, sticky="W")
        #Entry.config(self,anchor=W)
        if name is not None:
            self._set_name(name)
        if isPassword:
            self.config(show="*")
        if autoPack:
            self.pack()

    def _get(self):
        return self.textvar.get()

    def _set(self,value):
        return self.textvar.set(value)
    
    def _get_name(self):
        return self._name
    
    def _set_name(self,name):
        self._name = name
        
    def _get_label(self):
        return self._label
    
    def _set_label(self,label):
        self._label = label