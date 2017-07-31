import os
import xml.etree.ElementTree as ET

class XMLTools():
    EMAIL_KEY = "email"
    PASSWORD_KEY = "password"
    BACKUPPATH_KEY = "backup_path"
    
    tree = None
    filename = None
    
    def __init__(self,filename=None):
        if filename is not None:
            self._filename = filename
            self._load_settings(filename)
    
    def _load_settings(self,filename,createIfNew=True):
        if os.path.isfile(filename):
            tree = ET.parse(filename)
        else:
            root = ET.Element("GCB_Settings")
            ET.SubElement(root, self.EMAIL_KEY).text=""
            ET.SubElement(root, self.PASSWORD_KEY).text=""
            ET.SubElement(root, self.BACKUPPATH_KEY).text=""
            tree = ET.ElementTree(root)
            if createIfNew:
                tree.write(filename)
        self.filename = filename
        self.tree = tree
        return tree
    
    def _get_xml_text(self,key):
        root = self.tree.getroot()
        if root.find(key).text is None:
            return ""
        else:
            return root.find(key).text
        #email = root.find("email").text
        #password = root.find("password").text
        #filepath = root.find("filepath").text'''
        
    def _write_xml_text(self,key,newtext):
        self.tree.getroot().find(key).text = newtext
        
    def _save_settings(self,filename=None):
        if filename is None:
            filename = self.filename
        else:
            self.filename = filename
        print("FILENAME:")
        print(filename)
        self.tree.write(self.filename)
    