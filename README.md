# Garmin Connect Backup
This project will allow you to log into Garmin Connect and download your raw ".FIT" data to local hardrive.

This is an alpha, so please help out by reporting errors and feature suggestions.

# Setup
First, Must have python 3 installed!  Get it here:
https://www.python.org/downloads/

On GCB page on GitHub, click "Clone or Download" > "Download ZIP"
Download .zip file to hard drive and extract the folder.
Open terminal and navigate inside the folder just extracted.
Enter the following
> py setup.py install

This will install required python packages for GCB to run.

# Usage
In same folder as above, enter:
> py __main.py__

New window will launch.  Enter email, username, and place you want to backup the data.  If you don’t put a backup location, it will create a folder called “garmin_data” at current directory.

Click Connect.

Wait.

If you entered wrong credentials, it can’t catch that yet.  It will act like it is connected. 

Click Backup.

If you click anything while backing up, it will likely crash.

It will download every activity from your account to the folder specified.  Garmin serves them as a zip, and GBC will automatically extract them and renames them to a currently immutable convention.  The file’s date modified and date accessed will be changed to the starting date/time of the activity.  This is for easy sorting, although the filename already starts with the date.  In the [distant] future filenames will be configurable.

Click Save Options if you want it to auto-load and authenticate next time.
