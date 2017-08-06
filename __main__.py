from garminconnect_simple import GarminConnectService
from xmltools import XMLTools
from gfx.tk_gui import Graphics
import sys
#import os
#import xml.etree.ElementTree as ET

DEFAULT_SETTINGS_FILENAME = "GCB_settings.xml"

#load settings from file, if exists
xmltools = XMLTools(DEFAULT_SETTINGS_FILENAME)

#intialize Garmin Connect
email = xmltools._get_xml_text(xmltools.EMAIL_KEY)
password = xmltools._get_xml_text(xmltools.PASSWORD_KEY)
GarminConnect = GarminConnectService(email,password)

#initialize GUI
gui = Graphics(GarminConnect, xmltools, auto_authorize_garmin_connection=(email is not "" and password is not ""))

sys.exit()
