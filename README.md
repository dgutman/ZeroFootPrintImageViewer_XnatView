ZeroFootPrintImageViewer_XnatView
=================================

I agree this is a terrible name--- this is a Zero Foot Print Image Viewer (aka XnatView) that allows PACS like functionality from XNAT

This is a web-based image viewer that connects to an XNAT desktop, although the pipeline that generates the images
could be later to ideally view images from any PACS..


Installation/Dependencies:

Installing initial version on Stock Ubuntu 12.04LTS Desktop

After base install, and setting up IP address

sudo apt-get update  ### get latest set of packages
sudo apt-get upgrade # install new packages-- then rebooted
sudo reboot ## just to apply any kernel patches

sudo apt-get install openssh-server 
sudo apt-get install php5 apache2 
sudo apt-get install libapache2-mod-python

### need to install pyxnat-- two options are available.... can build from source or install from repo
sudo apt-get install python-pyxnat

### dcm2pnm is another dependency-- used to transcode the dcm files to something I can use on the web
### this is part of the dcmtk toolkit
sudo apt-get install libdcmtk2






#### TO DO ###
### need to add a bash script and/or config utilitity that creates all the requires directories
### whre the cache, dicom temp, and other files are stored..






#created a directory in my rootdir to place pyxnat and other programs I am pulling from git
mkdir dev_source_code

#Depending on your level of apache sophistication, the web root can be anywhere, but for simplicity
mkdir /var/www/xnatview




#need to set up modpython
   <Directory /var/www/xnatview_dev/python>
        AddHandler mod_python .py
        PythonHandler hello
        PythonDebug On
    </Directory>
