=================================
Steps to start Jupyter on Casper
=================================

Go to the folder that you have jupyter notebooks (\*.ipynb) and start and interactive job from the NCAR HPC - Cheyenne:
    execcasper

Once the job has launched, in the same window load the following modules:
   | module load ncarenv
   | module load python

Enter the default Python interface using:
    ncar_pylib

Start the Jupyter Notebook using and following the instructions printed to the screen:
    start-jupyter


Two things will result:
    1. A ssh command that needs to be placed into a different window and logged in with yubikey/duo authentication. Note you will just get a blinking cursor as a result.

    2. The original terminal will provide a token for the Jupyter web interface. Open a browser (e.g. Firefox) then head to the web address in the original terminal window (usually http://localhost:8888) and add the token where required.

