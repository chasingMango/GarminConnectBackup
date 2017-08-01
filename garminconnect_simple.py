import requests
import json
import time
import os
import re
import zipfile
import datetime
import math
from threading import Thread

class GarminConnectService():
    _reauthAttempts = 1 # per request
    ACTIVITY_LIST_FILENAME = "activity_list.json"
    
    AUTENTICATION_STATUS_UNAUTHENTICATED = 0
    AUTHENICATION_STATUS_AUTHENTICATING = 1
    AUTHENTICATION_STATUS_AUTHENTICATED = 2
    AUTHENTICATION_STATUS_FAILED = 3
    
    gui=None
    email=None
    password=None
    headers=None
    session=None
    activity_list=None
    autentication_status = AUTENTICATION_STATUS_UNAUTHENTICATED
    
    def __init__(self, email, password):
        self.email=email
        self.password=password
        
    def _get_activity_hierarchy(self):
        rawdata = requests.get("https://connect.garmin.com/proxy/activity-service-1.2/json/activity_types", headers=self.headers).text    
        return json.loads(rawdata)["dictionary"]
    
    def _authorize(self,post_authentication=None):
        background_thread = Thread(target=self._get_new_session, args=(post_authentication,))
        background_thread.start()
    
    def _get_new_session(self,post_authentication=None):
        print("Establishing new session with Garmin...")
        self._display_status("Establishing new session with Garmin...")
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
    
        self._rate_limit()
        gcRedeemResp = session.get("https://connect.garmin.com/post-auth/login", allow_redirects=False)
        if gcRedeemResp.status_code != 302:
            raise APIException("GC redeem-start error %s %s" % (gcRedeemResp.status_code, gcRedeemResp.text))
        url_prefix = "https://connect.garmin.com"
        # There are 6 redirects that need to be followed to get the correct cookie
        # ... :(
        max_redirect_count = 7
        current_redirect_count = 1
        while True:
            self._rate_limit()
            url = gcRedeemResp.headers["location"]
            # Fix up relative redirects.
            if url.startswith("/"):
                url = url_prefix + url
            url_prefix = "/".join(url.split("/")[:3])
            gcRedeemResp = session.get(url, allow_redirects=False)

            if current_redirect_count >= max_redirect_count and gcRedeemResp.status_code != 200:
                raise APIException("GC redeem %d/%d error %s %s" % (current_redirect_count, max_redirect_count, gcRedeemResp.status_code, gcRedeemResp.text))
            if gcRedeemResp.status_code == 200 or gcRedeemResp.status_code == 404:
                break
            current_redirect_count += 1
            if current_redirect_count > max_redirect_count:
                break

        if self.headers is not None:
            session.headers.update(self.headers)
        
        self.session=session
        print("Session established.")
        self._display_status("Session established.")
        
        if post_authentication is not None:
                post_authentication()
        return session
    
    def _get_session(self):
        return self.session
    
    def _get_user_profile(self):
        rawdata = self._get_session().get("http://connect.garmin.com/proxy/userprofile-service/socialProfile/", headers=self.headers).text    
        return json.loads(rawdata)["dictionary"]
    
    def _get_username(self):
        return self._get_session().get("http://connect.garmin.com/user/username").json()["username"]
    
    def _rate_limit(self):
        time.sleep(1)
        
    def _download_activity_list(self,exhaustive=True,save_to_file=False,save_path="",load_from_saved=True):
        self._display_status("Updating activity lists...")
        
        page = 1
        pageSz=100
        activities = []
        saved_activities = []
        
        if load_from_saved:
            #print("Loaded activites from saved file")
            self._load_activity_list(save_path)
            saved_activities = self._get_activity_list()
            #print("Number of saved activities: ",len(saved_activities))
            
        
        exit_loop=False
        while(not exit_loop):
            result = self._get_session().get("https://connect.garmin.com/modern/proxy/activity-search-service-1.0/json/activities", params={"start": (page - 1) * pageSz, "limit": pageSz})
            try:
                result = result.json()["results"]
            except ValueError:
                print("ERROR: Failed to load page %i",page)
                
            if "activities" not in result:
                break  # No activities on this page - empty account, or reach end of activity list.
                
            for activity in result["activities"]:
                #activies appear from most recent to oldest, so once we see an activity
                #that appears in our saved list, the rest will be in there too, so
                #break from the loop
                if saved_activities is not None and activity in saved_activities:
                        print("Activity ID ",activity["activity"]["activityId"]," found in saved list.  Breaking.")
                        exit_loop=True
                        break
                else:
                    activities.append(activity)
                
            totalpages=int(result["search"]["totalPages"])
                
            print("Downloaded page ",page, " out of ",totalpages)
            self._display_status("Updating activity lists: " + str(math.floor((page/totalpages)*100)) + "%")
            #use this save method if desired to save activites by page
            #if save_to_file:
            #    page_filename = self._get_activity_list_filename(save_path,page)
            #    self._save_activity_list(page_filename,activities[(page-1)*pageSz:])
                
            if not exhaustive or totalpages == page:
                break
            else:
                page += 1
        
        if saved_activities is not None:
            activities.extend(saved_activities)
        
        if save_to_file:
            self._save_activity_list(save_path + "\\" + self.ACTIVITY_LIST_FILENAME,activities)
        
        self._set_activity_list(activities)
        self._display_status("Updated activity lists.")
        return activities
    
    def _load_activity_list(self,path):
        activity_list_filename = path + "\\" + self.ACTIVITY_LIST_FILENAME
        if os.path.isfile(activity_list_filename):
            with open(activity_list_filename) as json_data:
                self._set_activity_list(json.load(json_data))
        else:
            self._set_activity_list(None)
        #convert to list
        #activity_list = json.loads(activity_list)
        
    
    def _save_activity_list(self,filename,activities=None):
        if activities is None:
            activities = self._get_activity_list()
            
        with open(filename, 'w') as outfile:
                json.dump(activities, outfile)
    
    def _get_activity_list_filename(self,path,page):
        return path + "\\" + self.ACTIVITY_LIST_FILENAME[0:-5]+"_"+str(page)+self.ACTIVITY_LIST_FILENAME[-5:]
                
    def _get_activity_list(self):
        return self.activity_list
    
    def _set_activity_list(self,activity_list):
        self.activity_list=activity_list
            
    def _get_activity_ids(self):
        ids=[]
        for activity in self._get_activity_list():
            ids.append(activity["activity"]["activityId"])
        return ids
    
    def _form_filename(self,path,id,extension="fit",id_index=None):
        if id_index is None:
            id_index = self._get_activity_ids().index(id) 
        return path + '\\' + self._get_activity_date(id) + " " + str(id) + " " + self._format_filename(self._get_activity_name(id)) + "." + extension
    
    def _format_filename(self,s):
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
    
    def _download_all_activities_original(self,download_path):
        if download_path == "":
            download_path = "./garmin_data"
        
        def separate_thread(download_path):
            if self._get_activity_list() is None:
                activity_list_path = download_path #+ "\\activity lists"
                if not os.path.exists(activity_list_path):
                    os.makedirs(activity_list_path)
                self._download_activity_list(save_to_file=True,save_path=activity_list_path)
            ids=self._get_activity_ids()

            if not os.path.exists(download_path):
                os.makedirs(download_path)

            count=0
            new_count=0
            for id in ids:
                self._display_status("Downloading activites: " + str(math.floor((count/len(ids))*100)) + "%")
                count+=1
                filename=self._form_filename(path=download_path,id=id,extension="zip",id_index=count-1)

                if not os.path.isfile(filename) and not os.path.isfile(filename[0:-3]+"zip") and not os.path.isfile(filename[0:-3]+"fit") and not os.path.isfile(filename[0:-3]+"tcx"):
                    print("Downloading activity",count,"out of",len(ids),count-1, ".  Activity_ID=",id)
                    #Download the activity and also increment the count if it was successful
                    if self.download_activity_original(id,download_path):
                        new_count+=1
                else:
                    print("Already downloaded activity",count,"out of",len(ids))
            self._display_status("Download " + str(new_count) + " new activities.")
                    
        background_thread = Thread(target=separate_thread, args=(download_path,))
        background_thread.start()
    
    def _download_all_activities_json(self,download_path):
        if self._get_activity_list() is None:
            self._download_activity_list()
        ids=self._get_activity_ids()
        
        if not os.path.exists(download_path):
            os.makedirs(download_path)
            
        count=0
        for id in ids:
            count+=1
            filename=self._form_filename(path=download_path,id=id,id_index=count-1)
            
            if not os.path.isfile(filename):
                print("Downloading activity",count,"out of",len(ids),count-1)
                json_data=download_activity_json(id)
                with open(filename, 'w') as outfile:
                    json.dump(json_data, outfile)
            else:
                print("Already downloaded activity",count,"out of",len(ids))
                
    def download_activity_json(self,activity_id):
        raw_data = None
        result=self._get_session().get("https://connect.garmin.com/modern/proxy/activity-service-1.3/json/activityDetails/" + str(activity_id) + "?maxSize=999999999")
        try:
            #raw_data = result.json()["com.garmin.activity.details.json.ActivityDetails"]
            raw_data = result.json()
        except ValueError:
            print("ERROR downloading JSON for activity ",id)
        return raw_data
    
    def download_activity_original(self,activity_id,download_path,extract_zip=True,delete_zip_after_extract=True,change_date_modified=True):
        result=self._get_session().get("https://connect.garmin.com/modern/proxy/download-service/files/activity/" + str(activity_id))
        
        result_filename = self._get_filename_from_result(result)
        if result_filename is None:
            print("Could not find a download for activity ",activity_id,". Skipped.")
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
    
    def _get_activity_date(self,activity_id):
        id_index = self._get_activity_ids().index(activity_id) 
        return self._get_activity_list()[id_index]["activity"]["beginTimestamp"]["value"]
    
    def _get_activity_datetime(self,activity_id):
        id_index = self._get_activity_ids().index(activity_id) 
        millis_from_epoch = self._get_activity_list()[id_index]["activity"]["beginTimestamp"]["millis"]
        seconds_from_epoc = int(millis_from_epoch[:-3])
        return datetime.datetime.fromtimestamp(seconds_from_epoc).strftime('%Y-%m-%d %H:%M:%S')
    
    def _get_activity_name(self,activity_id):
        id_index = self._get_activity_ids().index(activity_id) 
        return self._get_activity_list()[id_index]["activity"]["activityName"]["value"]
        
    def _get_epoch_time(self,date_time,pattern):
        return int(time.mktime(time.strptime(date_time, pattern))) 
    
    def _set_gui(self,gui):
        self.gui = gui
        
    def _set_email(self,email):
        self.email = email
        
    def _set_password(self,password):
        self.password = password
        
    def _get_gui(self):
        return self.gui
    
    def _display_status(self,text):
        if self._get_gui is not None:
            self._get_gui()._set_status_text(text)