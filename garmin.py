import requests
import json
import time
import os
import re
import zipfile
import datetime
import math
from threading import Thread

class Garmin():
    
    ACTIVITY_LIST_FILENAME = "activity_list.json"
    DOWNLOAD_PATH_DEFAULT = "./garmin_data/"
    
    def __init__(self,debug=True,gui=None, email=None,password=None,backup_path="./"):
        self._gui=None
        self.gui=gui
        self._status = 0 # 0=idle
        self.status=0
        self.debug=debug
        self.email=email
        self.password=password
        self.backup_path = backup_path
        self.connected=False
        self.session=None
        self.activities=[]
        self.headers=None #this never changes but could be updated later if adding headers would enable some additional functionality
        
    def connect(self,email,password,wait_for_completion=False, post_connection_functions=[]):
        self.status = 1 # 1=connecting
        self.email=email
        self.password=password
        background_thread = Thread(target=self._connect, args=(post_connection_functions,))
        background_thread.start()
        if wait_for_completion:
            while self.status is 1: #loop/wait until status goes back to 0 (idle)
                time.sleep(.25)

    def _connect(self,post_connection_functions=[]):
        #prevent over-pinging Garmin and getting locked out
        def _rate_limit():
            time.sleep(1)
        
        self._msg("Logging into Garmin with " + self.email + "...")
        session = requests.Session()
        data = {
            "username": self.email,
            "password": self.password,
            "_eventId": "submit",
            "embed": "true",
            # "displayNameRequired": "false"
        }
        params = {
            "service": "https://connect.garmin.com/post-auth/login",
            # "redirectAfterAccountLoginUrl": "http://connect.garmin.com/post-auth/login",
            # "redirectAfterAccountCreationUrl": "http://connect.garmin.com/post-auth/login",
            # "webhost": "olaxpw-connect00.garmin.com",
            "clientId": "GarminConnect",
            "gauthHost": "https://sso.garmin.com/sso",
            # "rememberMeShown": "true",
            # "rememberMeChecked": "false",
            "consumeServiceTicket": "false",
            # "id": "gauth-widget",
            # "embedWidget": "false",
            # "cssUrl": "https://static.garmincdn.com/com.garmin.connect/ui/src-css/gauth-custom.css",
            # "source": "http://connect.garmin.com/en-US/signin",
            # "createAccountShown": "true",
            # "openCreateAccount": "false",
            # "usernameShown": "true",
            # "displayNameShown": "false",
            # "initialFocus": "true",
            # "locale": "en"
        }
        
        preResp = session.get("https://sso.garmin.com/sso/login", params=params)
        if preResp.status_code != 200:
            raise APIException("SSO prestart error %s %s" % (preResp.status_code, preResp.text))
        ssoResp = session.post("https://sso.garmin.com/sso/login", params=params, data=data, allow_redirects=False)
        if ssoResp.status_code != 200 or "temporarily unavailable" in ssoResp.text:
            raise APIException("SSO error %s %s" % (ssoResp.status_code, ssoResp.text))

        if ">sendEvent('FAIL')" in ssoResp.text:
            raise APIException("Invalid login", block=True, user_exception=UserException(UserExceptionType.Authorization, intervention_required=True))
        if ">sendEvent('ACCOUNT_LOCKED')" in ssoResp.text:
            raise APIException("Account Locked", block=True, user_exception=UserException(UserExceptionType.Locked, intervention_required=True))
        if "renewPassword" in ssoResp.text:
            raise APIException("Reset password", block=True, user_exception=UserException(UserExceptionType.RenewPassword, intervention_required=True))

        # ...AND WE'RE NOT DONE YET!
    
        _rate_limit()
        gcRedeemResp = session.get("https://connect.garmin.com/post-auth/login", allow_redirects=False)
        if gcRedeemResp.status_code != 302:
            raise APIException("GC redeem-start error %s %s" % (gcRedeemResp.status_code, gcRedeemResp.text))
        url_prefix = "https://connect.garmin.com"
        # There are 6 redirects that need to be followed to get the correct cookie
        # ... :(
        max_redirect_count = 7
        current_redirect_count = 1
        connected=False
        
        while current_redirect_count<=max_redirect_count:
            _rate_limit()
            url = gcRedeemResp.headers["location"]
            # Fix up relative redirects.
            if url.startswith("/"):
                url = url_prefix + url
            url_prefix = "/".join(url.split("/")[:3])
            gcRedeemResp = session.get(url, allow_redirects=False)
            
            #This could change, but i've found that this is an indicator or a successful
            #connection.  If the connection is not successful, then the url will not
            #contain ticket date in this url.  There might be better more reliable
            #indicators of a successful connectdion, but this is all I have been
            #able to figure out so far.
            if current_redirect_count is 6 and "?ticket=" in url:
                connected=True

            if current_redirect_count >= max_redirect_count and gcRedeemResp.status_code != 200:
                raise APIException("GC redeem %d/%d error %s %s" % (current_redirect_count, max_redirect_count, gcRedeemResp.status_code, gcRedeemResp.text))
            if gcRedeemResp.status_code == 200 or gcRedeemResp.status_code == 404:
                break
            current_redirect_count += 1

        #self.headers is None by default and never changes, but could be modified
        #in the future if it would result in additional functionaity or if the 
        #GarminConnectd API changes and requires it
        if self.headers is not None:
            session.headers.update(self.headers)
        
        if connected:
            self.session=session
            self._msg("Connection established.")
            self.connected=True
        else:
            self.session=None
            self._msg("Error: connection failed. Maybe you entered incorrect email and password.")
            self.connected=True
        
        #run other functions passed to be run after connecting:
        for function in post_connection_functions:
            function()
        
        #function is over, set status back to 0 (idle)
        self.status=0
        
    def download_all_activities(self,download_path=None,force_activity_list_refresh=False):                    
        if download_path is None:
            download_path=self.DOWNLOAD_PATH_DEFAULT
        if download_path[:-1] is not ("\\" or "/"):
            download_path=download_path+"/"
            
        background_thread = Thread(target=self._download_all_activities, args=(download_path,force_activity_list_refresh,))
        background_thread.start()
    
    def _download_all_activities(self, download_path,force_activity_list_refresh=False):
            self._msg("Downloading new activities...")
            
            if not os.path.exists(download_path):
                os.makedirs(download_path)

            self.update_activity_list(download_path=download_path,force_refresh=force_activity_list_refresh)
            ids=self.get_activity_ids()

            count=0
            new_count=0
            for id in ids:
                self._msg("Downloading activites: " + str(math.floor((count/len(ids))*100)) + "%",console=False)
                
                count+=1
                filename=self._form_filename(path=download_path,id=id,extension="zip",id_index=count-1)

                if not os.path.isfile(filename) and not os.path.isfile(filename[0:-3]+"zip") and not os.path.isfile(filename[0:-3]+"fit") and not os.path.isfile(filename[0:-3]+"tcx"):
                    #print("Downloading activity",count,"out of",len(ids),count-1, ".  Activity_ID=",id)
                    #Download the activity and also increment the count if it was successful
                    if self.download_activity_original(id,download_path):
                        new_count+=1
                #else:
                #    print("Already downloaded activity",count,"out of",len(ids))
            self._msg("Download complete.  Found " + str(new_count) + " new activities.")
            
    def download_activity_original(self,activity_id,download_path,extract_zip=True,delete_zip_after_extract=True,change_date_modified=True):
        result=self.session.get("https://connect.garmin.com/modern/proxy/download-service/files/activity/" + str(activity_id))
        
        result_filename = self._get_filename_from_result(result)
        if result_filename is None:
            self._msg("Could not find a download for activity " + str(activity_id) + ". Skipped.", gui=False)
            return False
        result_filename_extension=result_filename[-3:]
        
        download_filename = self._form_filename(download_path,activity_id,extension=result_filename_extension)
        
        with open(download_filename, 'wb') as f:
            for chunk in result.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    #f.flush() commented by recommendation from J.F.Sebastian
        if result_filename_extension=="zip" and extract_zip is True:
            zip_ref = zipfile.ZipFile(download_filename, 'r')
            zip_ref.extractall()
            zip_ref.close()
            
            extracted_filename=zipfile.ZipFile(download_filename).namelist()[0]
            new_filename = download_filename[0:-3] + extracted_filename[-3:]
            os.rename(extracted_filename,new_filename)            
            if delete_zip_after_extract is True:
                os.remove(download_filename)
            download_filename=new_filename
                
        if change_date_modified is True:
            modification_time = self._get_epoch_time(self._get_activity_datetime(activity_id),"%Y-%m-%d %H:%M:%S")
            access_time = modification_time
            os.utime(download_filename, (access_time, modification_time))
        
        return True
    
    def _get_filename_from_result(self,result):
        try:
            d = result.headers['content-disposition']
            fname = re.findall("filename=(.+)", d)
            return fname[0][1:-1]
        except:
            return None  #If this happens, there is no file to download, probably a manual entry with no GPS or other fitness data
            
    def _form_filename(self,path,id,extension="fit",id_index=None):
        if id_index is None:
            id_index = self.get_activity_ids().index(id) 
        return path + '\\' + self._get_activity_date(id) + " " + str(id) + " " + self._sanitize_filename(self._get_activity_name(id)) + "." + extension
    
    def _sanitize_filename(self,s):
        """Take a string and return a valid filename constructed from the string.
        Uses a whitelist approach: any characters not present in valid_chars are    
        removed. Also spaces are replaced with underscores.

        Note: this method may produce invalid filenames such as ``, `.` or `..`
        When I use this method I prepend a date string like '2009_01_15_19_46_32_'
        and append a file extension like '.txt', so I avoid the potential of using
        an invalid filename.

        """
        import string
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in s if c in valid_chars)
        #filename = filename.replace(' ','_')
        return filename 
    
    def _get_activity_date(self,activity_id):
        id_index = self.get_activity_ids().index(activity_id) 
        return self.activities[id_index]["activity"]["beginTimestamp"]["value"]
    
    def _get_activity_datetime(self,activity_id):
        id_index = self.get_activity_ids().index(activity_id) 
        millis_from_epoch = self.activities[id_index]["activity"]["beginTimestamp"]["millis"]
        seconds_from_epoc = int(millis_from_epoch[:-3])
        return datetime.datetime.fromtimestamp(seconds_from_epoc).strftime('%Y-%m-%d %H:%M:%S')
    
    def _get_activity_name(self,activity_id):
        id_index = self.get_activity_ids().index(activity_id) 
        return self.activities[id_index]["activity"]["activityName"]["value"]
        
    def _get_epoch_time(self,date_time,pattern):
        return int(time.mktime(time.strptime(date_time, pattern))) 
    
    def update_activity_list(self,exhaustive=True,save_to_file=True,download_path=None,force_refresh=False):
        self._msg("Updating activity lists...",gui=False)
        
        if download_path is None:
            download_path=self.DOWNLOAD_PATH_DEFAULT
        
        if not force_refresh:
            self.load_activity_list(load_path=download_path)
        else:
            if save_to_file: #only delete the existing activities file if about to save the forced update
                self.delete_activity_list(download_path=download_path)
            self.activities=[]
            
        
        page = 1
        pageSz=100
        new_activity_count=0

        exit_loop=False
        while(not exit_loop):
            result = self.session.get("https://connect.garmin.com/modern/proxy/activity-search-service-1.0/json/activities", params={"start": (page - 1) * pageSz, "limit": pageSz})
            try:
                result = result.json()["results"]
            except ValueError:
                print("ERROR: Failed to load page %i",page)
                
            if "activities" not in result:
                break  # No activities on this page - empty account, or reached end of activity list.
                
            for activity in result["activities"]:
                #activies appear from most recent to oldest, so once we see an activity
                #that appears in our saved list, the rest will be in there too, so
                #break from the loop
                if activity in self.activities:
                        self._msg("\tActivity ID " + activity["activity"]["activityId"] + " found in saved list.  Breaking from download.",gui=False)
                        exit_loop=True
                        break
                else:
                    self.activities.append(activity)
                    new_activity_count+=1
                
            totalpages=int(result["search"]["totalPages"])
                
            if not exit_loop:
                self._msg("Updating activity lists: " + str(math.floor((page/totalpages)*100)) + "%")
            else:
                self._msg("Updating activity lists: 100%")
                
            if not exhaustive or page == totalpages:
                break
            else:
                page += 1
        
        self._msg("Updated with " + str(new_activity_count) + " new activites.")
        #Return True if any new activities were loaded, otherwise return False.
        #This is to determine if saving is necessary
        if new_activity_count>0:
            if save_to_file:
                self.save_activity_list(download_path)
            return True
        else:
            return False

    def get_activity_ids(self):
        ids=[]
        for activity in self.activities:
            ids.append(activity["activity"]["activityId"])
        return ids
    
    def load_activity_list(self, load_path=".\\"):
        if load_path[-1:] is not ("\\" or "/"):
            load_path = load_path + "/"
        filename = load_path + self.ACTIVITY_LIST_FILENAME
        
        if os.path.isfile(filename):
            with open(filename) as json_data:
                self.activities = json.load(json_data)
                self._msg("Loaded " + str(len(self.activities)) + " activities from " + os.path.abspath(filename),gui=False)
        else:
            self.activities = []

    def save_activity_list(self,download_path=None):
        if download_path is None:
            download_path=self.DOWNLOAD_PATH_DEFAULT
        filename = download_path + self.ACTIVITY_LIST_FILENAME
        with open(filename, 'w') as outfile:
                json.dump(self.activities, outfile)
                self._msg("Saved activty list to " + os.path.abspath(filename),gui=False)
                
    def delete_activity_list(self,download_path=None):
        if download_path is None:
            download_path=self.DOWNLOAD_PATH_DEFAULT
        filename = download_path + self.ACTIVITY_LIST_FILENAME
        os.remove(filename)
        
    def _msg(self, text, console=True, gui=True):
        #if in debug mode, print to the console
        if console and self.debug:
            print(text)
        #if gui parameter is set to true, and we have a GUI loaded into this object,
        #then send the messsage to the GUI as well
        if gui is True and self.gui is not None:
            self.gui.set_status_text(text)
   
    @property
    def gui(self):
        return self._gui
    
    @gui.setter
    def gui(self, gui):
        if gui is None:
            return False
        gui.garmin=self
        self._gui = gui
        self.gui.refresh_display()
        return True
    
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, new_status):
        self._status=new_status
        if self.gui is not None:
            self.gui.refresh_display()
        return True
        