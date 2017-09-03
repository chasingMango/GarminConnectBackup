import os
import xml.etree.ElementTree as ET

class XMLTools():
    EMAIL_KEY = "email"
    PASSWORD_KEY = "password"
    BACKUPPATH_KEY = "backup_path"
    FORCE_ACTIVITY_LIST_REFRESH_KEY = "force_activity_list_refresh"
    
    tree = None
    filename = None
    
    def __init__(self,filename=None):
        if filename is not None:
            self._filename = filename
            self.load_settings(filename)
    
    def load_settings(self,filename,createIfNew=True):
        if os.path.isfile(filename):
            tree = ET.parse(filename)
        else:
            tree = self._create_tree([
                                    [self.EMAIL_KEY,""],
                                    [self.PASSWORD_KEY,""],
                                    [self.BACKUPPATH_KEY,""],
                                    [self.FORCE_ACTIVITY_LIST_REFRESH_KEY,""]])
            if createIfNew:
                tree.write(filename)
        self.filename = filename
        self.tree = tree
        return tree
        
    def save_settings(self, email,password,backup_path,force_activity_list_refresh,filename=None):
        if filename is None:
            filename = self.filename
        
        tree = self._create_tree([
                                    [self.EMAIL_KEY,email],
                                    [self.PASSWORD_KEY,password],
                                    [self.BACKUPPATH_KEY,backup_path],
                                    [self.FORCE_ACTIVITY_LIST_REFRESH_KEY,force_activity_list_refresh]])
                                    
        tree.write(filename)
        self.tree=tree
        return tree
    
    def _create_tree(self,settings):
        root = ET.Element("GCB_Settings")
        for setting in settings:
            ET.SubElement(root,setting[0]).text=setting[1]
        tree = ET.ElementTree(root)
        return tree
    
    def get_xml_text(self,key):
        root = self.tree.getroot()
        if root.find(key).text is None:
            return ""
        else:
            return root.find(key).text
        #email = root.find("email").text
        #password = root.find("password").text
        #filepath = root.find("filepath").text'''
        
    def write_xml_text(self,key,newtext):
        self.tree.getroot().find(key).text = newtext
        
    def get_filename(self):
        return self.filename
    