from tkinter import *
import os
#from garminconnect_simple import GarminConnectService

class Tk_GUI_old:
    
    _root = None
    GarminConnect = None
    xmltools = None
    entries = []
    buttons = []
    
    status_bar = None
    
    BACKUP_NOW_TEXT = "Backup Now"
    AUTHENTICATE_TEXT = "Connect"
    
    def __init__(self, xmltools, auto_setup_display=True, auto_authorize_garmin_connection=False):
        self.xmltools = xmltools
        
        if auto_setup_display:
            self._setup_display(run_mainloop_when_done=False)
        
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
            
    def set_status_text(self,text):
        self.status_bar['text'] = "Status: " + text
        
        
class tk_GUI:
    
    BACKUP_NOW_TEXT = "Backup Now"
    AUTHENTICATE_TEXT = "Connect"
    
    def __init__(self, xmltools, auto_setup_display=True,run_mainloop=False):
        self.garmin=None
        self.entries=[]
        self.buttons=[]
        self.checkboxes = []
        self.xmltools = xmltools
        
        self.root = Tk()
        self.option_force_activity_list_refresh = IntVar(master=self.root)
        
        if auto_setup_display:
            self.setup_display(root=self.root, run_mainloop=run_mainloop)
    
    def setup_display(self,root=None,run_mainloop=True):
        if root is None:
            root = Tk()
            self.root = root
        
        if self.garmin is not None:
            self.email=garmin.email
            self.password=garmin.email
            self.backup_path=garmin.backup_path
        else:
            self.email=""
            self.password=""
            self.backup_path=""
        
        #set window caption
        root.wm_title("Garmin Connect Backup")
        
        #create user input fields
        self._create_entry(field_label="Username: ", entry_name="email")
        self._create_entry(field_label="Password: ", entry_name="password",isPassword=True)
        self._create_entry(field_label="Backup location: ", entry_name="backup_path")
       
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
        
        btn_connect = Button(button_group_commands,text=self.AUTHENTICATE_TEXT,command=self._btn_connect_click)
        btn_connect.pack()
        self.buttons.append(["btn_connect",btn_connect])
        
        btn_backup_now = Button(button_group_commands,text=self.BACKUP_NOW_TEXT,command=self._btn_backup_now_click)
        btn_backup_now['state']='disabled'
        btn_backup_now.pack()
        self.buttons.append(["btn_backup_now",btn_backup_now])
        
         #----ADVANCED OPTIONS GROUP-------
        button_group_advanced = LabelFrame(root,text="Advanced Options")
        button_group_advanced.pack(padx=10,pady=10)
        chk_force_activity_list_refresh = Checkbutton(button_group_advanced, text="Force activity list refresh", var=self.option_force_activity_list_refresh)
        if self.xmltools.get_xml_text(self.xmltools.FORCE_ACTIVITY_LIST_REFRESH_KEY) is not "":
            self.option_force_activity_list_refresh.set(int(self.xmltools.get_xml_text(self.xmltools.FORCE_ACTIVITY_LIST_REFRESH_KEY)))
        else:
            self.option_force_activity_list_refresh.set(0)
        self.checkboxes.append(['chk_force_activity_list_refresh',chk_force_activity_list_refresh])
        chk_force_activity_list_refresh.pack()
        
        #-----SETUP STATUS BAR-----
        self.status_bar = Label(root,text="Welcome!")
        self.status_bar.pack()
        
        #OCD things
        self.center_window(root)
        
        self.root = root
        #run the main loop (depending on option value)
        if run_mainloop:
            root.mainloop()
        
    def _create_entry(self,toplevel=None,field_label=None,entry_name=None,entry_text="",height=1,width=50,isPassword=False):    
        if toplevel is None:
            toplevel = self.root
            
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
    
    def _get_entry(self,text):
        for entry in self.entries:
            if entry[0] == text:
                return entry[1]
        return None
    
    def _get_checkbox_value(self,chk_name):
        for checkbox in self.checkboxes:
            if checkbox[0] == chk_name:
                return checkbox[1]
        return None
    
    def center_window(self,toplevel):
        toplevel.update_idletasks()
        w = toplevel.winfo_screenwidth()
        h = toplevel.winfo_screenheight()
        size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
        x = w/2 - size[0]/2
        y = h/2 - size[1]/2
        toplevel.geometry("%dx%d+%d+%d" % (size + (x, y)))
        
    def set_status_text(self,text):
        self.status_bar['text'] = "Status: " + text
        
    def set_entry_text(self,name,text):
        entry = self._get_entry(name)
        if entry is not None:
            entry.delete(0, END) #deletes the current value
            if text is not None:
                entry.insert(0,text)
            else:
                entry.insert(0,"")
        
    def run_mainloop(self):
        self.root.mainloop()
        
    def _btn_backup_now_click(self):
        self.garmin.download_all_activities(download_path=self._get_entry_text("backup_path"),force_activity_list_refresh=self.option_force_activity_list_refresh.get())
        
    def _btn_save_options_click(self):
        #print("You clicked: Save Options")
        #self.xmltools._write_xml_text(self.xmltools.EMAIL_KEY,self._get_entry_text(self.xmltools.EMAIL_KEY))
        #self.xmltools._write_xml_text(self.xmltools.PASSWORD_KEY,self._get_entry_text(self.xmltools.PASSWORD_KEY))
        #self.xmltools._write_xml_text(self.xmltools.BACKUPPATH_KEY,self._get_entry_text(self.xmltools.BACKUPPATH_KEY))
        self.xmltools.save_settings(
                                email=self._get_entry_text(self.xmltools.EMAIL_KEY),
                                password=self._get_entry_text(self.xmltools.PASSWORD_KEY),
                                backup_path=self._get_entry_text(self.xmltools.BACKUPPATH_KEY),
                                force_activity_list_refresh=str(self.option_force_activity_list_refresh.get()))
        self.set_status_text("Options saved to " + os.path.abspath(self.xmltools.get_filename()))
    
    def _btn_connect_click(self):
        if self.garmin is None:
            self.set_status_text("Error: No Garmin module loaded.")
            return False
        self.garmin.connect(email=self._get_entry_text("email"),password=self._get_entry_text("password"))
        self.garmin.email=self._get_entry_text("email")
        self.garmin.password=self._get_entry_text("password")
        return True
    
    def _set_button_state(self,btnName,state_text):
        button = self._get_button(btnName)
        if button is not None:
            button['state']=state_text
        
        
    def refresh_display(self):
        if self.garmin is not None:            
            self.email = self.garmin.email
            self.password = self.garmin.password
            self.backup_path = self.garmin.backup_path
        
        self.set_entry_text("email",self.email)
        self.set_entry_text("password",self.password)
        self.set_entry_text("backup_path",self.backup_path)
        
        if self.garmin is not None:        
            if self.garmin.status is 0: #Not actively connecting to Garmin...
                self._set_button_state("btn_connect","normal")
            else: #Actively connecting to Garmin...
                self._set_button_state("btn_connect","disabled")
            
            if self.garmin.connected: # connected to garmin
                self._set_button_state("btn_backup_now","normal")
            else: #not connected to garmin
                self._set_button_state("btn_backup_now","disabled")