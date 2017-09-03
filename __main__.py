from garmin import Garmin
from xmltools import XMLTools
from gui.tk_gui import tk_GUI
import sys
#import os
#import xml.etree.ElementTree as ET

DEFAULT_SETTINGS_FILENAME = "GCB_settings.xml"

#load settings from file, if exists
xmltools = XMLTools(DEFAULT_SETTINGS_FILENAME)

#intialize Garmin Connect
email = xmltools.get_xml_text(xmltools.EMAIL_KEY)
password = xmltools.get_xml_text(xmltools.PASSWORD_KEY)
backup_path = xmltools.get_xml_text(xmltools.BACKUPPATH_KEY)

#initialize GUI
gui = tk_GUI(xmltools)

#initialize Garmin connection
if email is not "" and password is not "":
    garmin = Garmin(email=email,password=password,backup_path=backup_path)
else:
    garmin = Garmin()
#garmin = Garmin()
garmin.gui = gui
if email is not "" and password is not "":
    garmin.connect(email,password,wait_for_completion=False)

gui.run_mainloop()

#garmin.load_activity_list()
#garmin.update_activity_list(save_if_new_activites=True)


    

#initialize GUI
#gui = Tk_GUI(GarminConnect, xmltools, auto_authorize_garmin_connection=(email is not "" and password is not ""))

sys.exit()
