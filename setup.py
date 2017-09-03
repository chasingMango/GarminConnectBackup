from setuptools import setup, find_packages

setup (
       name='GarminConnectBackup',
       version='0.1',
       packages=find_packages(),

       # Declare your packages' dependencies here, for eg:
       install_requires=[''],
       
       python_requires='>=3',
       
       classifiers=[
            # How mature is this project? Common values are
            #   3 - Alpha
            #   4 - Beta
            #   5 - Production/Stable
            'Development Status :: 3 - Alpha',

            # Indicate who your project is intended for
            'Intended Audience :: Athletes',


            # Specify the Python versions you support here. In particular, ensure
            # that you indicate whether you support Python 2, Python 3 or both.
            'Programming Language :: Python :: 3',  
        ],

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