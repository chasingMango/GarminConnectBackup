from tkinter import *
#from garminconnect_simple import GarminConnectService

class Graphics:
    
    _root = None
    GarminConnect = None
    xmltools = None
    entries = []
    buttons = []
    
    status_bar = None
    
    BACKUP_NOW_TEXT = "Backup Now"
    AUTHENTICATE_TEXT = "Connect"
    
    def __init__(self, GarminConnect, xmltools, auto_setup_display=True, auto_authorize_garmin_connection=False):
        self.xmltools = xmltools
        
        if auto_setup_display:
            self._setup_display(run_mainloop_when_done=False)
            
        self.GarminConnect = GarminConnect
        self.GarminConnect._set_gui(self)
        
        if auto_authorize_garmin_connection:
            self._authorize_garmin_connection()
            
        self._get_root().mainloop()
        
    def _setup_display(self,run_mainloop_when_done=True):
        root = Tk()
        self._set_root(root)
        
        email = self.xmltools._get_xml_text(self.xmltools.EMAIL_KEY)
        password = self.xmltools._get_xml_text(self.xmltools.PASSWORD_KEY)
        backupupath = self.xmltools._get_xml_text(self.xmltools.BACKUPPATH_KEY)
        
        #set window caption
        root.wm_title("Garmin Connect Backup")
        
        #create user input fields
        self._create_entry(field_label="Username: ", entry_name=self.xmltools.EMAIL_KEY,entry_text=email)
        self._create_entry(field_label="Password: ", entry_name=self.xmltools.PASSWORD_KEY,isPassword=True,entry_text=password)
        self._create_entry(field_label="Backup location: ", entry_name=self.xmltools.BACKUPPATH_KEY,entry_text=backupupath)
       
        #entry_username = Smart_entry(name="email", content=email, label_text="Email: ",toplevel=root,column=0,row=1, width=50)
        #entry_password = Smart_entry(name="password", content=password, label_text="Password: ",toplevel=root,column=0,row=2, width=50,isPassword=True)
        #entry_filepath = Smart_entry(name="filepath", content=filepath, label_text="Backup location: ",toplevel=root,column=0,row=2, width=50,isPassword=True)
        #self.smartfields.extend([entry_username,entry_password,entry_filepath])
        
        #----GCP BUTTONS-------
        button_group_gcb_options = LabelFrame(root,text="GCB Commands")
        button_group_gcb_options.pack(padx=10,pady=10)
        btn_save_options = Button(button_group_gcb_options,text="Save Options",command=self._btn_save_options_click)
        btn_save_options.pack()
        self.buttons.append(["btn_save_options",btn_save_options])
        #----BACKUP BUTTONS----
        button_group_commands = LabelFrame(root, text="Backup Commands", padx=5, pady=5)
        button_group_commands.pack(padx=10, pady=10)
        btn_authenticate = Button(button_group_commands,text=self.AUTHENTICATE_TEXT,command=self._btn_authenticate_click)
        btn_authenticate.pack()
        btn_backup_now = Button(button_group_commands,text=self.BACKUP_NOW_TEXT,command=self._btn_backup_now_click)
        btn_backup_now['state']='disabled'
        btn_backup_now.pack()
        self.buttons.append(["btn_authenticate",btn_authenticate])
        self.buttons.append(["btn_backup_now",btn_backup_now])
        
        #-----SETUP STATUS BAR-----
        self.status_bar = Label(root,text="Welcome!")
        self.status_bar.pack()
        
        #OCD things
        self._center_window(root)
        
        #run the main loop (depending on option value)
        if run_mainloop_when_done:
            root.mainloop()
        self._set_root(root)
        
    def _set_root(self,root):
        self._root=root
        
    def _get_root(self):
        return self._root
    
    def _center_window(self,toplevel):
        toplevel.update_idletasks()
        w = toplevel.winfo_screenwidth()
        h = toplevel.winfo_screenheight()
        size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        toplevel.geometry("%dx%d+%d+%d" % (size + (x, y)))

    def _create_entry(self,toplevel=None,field_label=None,entry_name=None,entry_text=None,height=1,width=50,isPassword=False):    
        if toplevel is None:
            toplevel = self._get_root()
            
        if field_label is not None:
            label = Label(toplevel,text=field_label)
            label.pack(anchor=W)
        entry = Entry(toplevel, width=width)
        entry.insert(0,entry_text)
        if isPassword:
            entry.config(show="*")
        entry.pack()
        self.entries.append([entry_name,entry])
        
    def _get_entry_text(self,entry_name):
        for entry in self.entries:
            if entry[0] == entry_name:
                return entry[1].get()
        return None
    
    def _get_button(self,text):
        for button in self.buttons:
            if button[0] == text:
                return button[1]
        return None
        
    def _btn_backup_now_click(self):
        #print("You clicked: Backup Now!")
        self.GarminConnect._download_all_activities_original(self.xmltools._get_xml_text(self.xmltools.BACKUPPATH_KEY))
        
    def _btn_save_options_click(self):
        #print("You clicked: Save Options")
        self.xmltools._write_xml_text(self.xmltools.EMAIL_KEY,self._get_entry_text(self.xmltools.EMAIL_KEY))
        self.xmltools._write_xml_text(self.xmltools.PASSWORD_KEY,self._get_entry_text(self.xmltools.PASSWORD_KEY))
        self.xmltools._write_xml_text(self.xmltools.BACKUPPATH_KEY,self._get_entry_text(self.xmltools.BACKUPPATH_KEY))
        self.xmltools._save_settings()
        
    def _btn_authenticate_click(self):        
        self.GarminConnect._set_email(self._get_entry_text(self.xmltools.EMAIL_KEY))
        self.GarminConnect._set_password(self._get_entry_text(self.xmltools.PASSWORD_KEY))
        self._authorize_garmin_connection(handle_buttons=True)
    
    def _authorize_garmin_connection(self, handle_buttons=True):
        btn_authenticate = self._get_button("btn_authenticate")
        btn_backup_now = self._get_button("btn_backup_now")
        if handle_buttons:
            btn_authenticate['state']='disabled'
            btn_backup_now['state']='disabled'
        self.GarminConnect._authorize(post_authentication=self._post_authentication)
    
    def _post_authentication(self):
        btn_authenticate = self._get_button("btn_authenticate")
        btn_backup_now = self._get_button("btn_backup_now")
        btn_authenticate.text = self.AUTHENTICATE_TEXT
        btn_backup_now.text = self.BACKUP_NOW_TEXT
        btn_authenticate['state']='normal'
        btn_backup_now['state']='normal'
            
    def _set_status_text(self,text):
        self.status_bar['text'] = "Status: " + text