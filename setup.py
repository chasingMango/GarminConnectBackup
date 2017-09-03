from setuptools import setup, find_packages

setup (
       name='GarminConnectBackup',
       version='0.1',
       packages=find_packages(),

       # Declare your packages' dependencies here, for eg:
       install_requires=[''],

       # Fill in these to make your Egg ready for upload to
       # PyPI
       author='Jonathan McGrath',
       author_email='mcgrath.jon@gmail.com',

       #summary = 'Just another Python package for the cheese shop',
       url='',
       license='',
       long_description='This project will allow you to log into Garmin Connect and download raw fitness files to your local hard drive.',

       # could also include long_description, download_url, classifiers, etc.

  
       )