# GarminConnectBackup
Backup activities from Garmin Connect to local hard drive.

This is an alpha.  Lots of error handling / exceptions not handled as of right now. 

Enter email, username, and place you want to backup the data.  If you don’t put a backup location, it will create a folder called “garmin_data” at current directory.

Click Connect.

Wait.

If you entered wrong credentials, it can’t catch that yet.  It will act like it is connected. 

Click Backup.

If you click anything while backing up, it will likely crash.

It will download every activity from your account to the folder specified.  Garmin serves them as a zip, and GBC will automatically extract them and renames them to a currently immutable convention.  The file’s date modified and date accessed will be changed to the starting date/time of the activity.  This is for easy sorting, although the filename already starts with the date.  In the [distant] future filenames will be configurable.

Click Save Options if you want it to auto-load and authenticate next time.

LAST: If you are python savvy and look at the source code, buckle your seatbelt and hold on tight.  Its going to be a bumpy ride.
