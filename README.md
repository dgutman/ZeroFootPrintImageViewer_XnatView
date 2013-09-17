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



sudo apt-get install open-vm-toolbox
sudo apt-get install php5 apache2  libapache2-mod-python openssh-server
#I installed apache2 and openssh-server during the VM install, but can install like this as well
#also installing open-vm-tools for vmware, not necessary on bare steel installs


### need to install pyxnat-- two options are available.... can build from source or install from repo
#sudo apt-get install python-pyxnat
# I recommend install from source control, as their are a number of bug fixes



### dcm2pnm is another dependency-- used to transcode the dcm files to something I can use on the web
### this is part of the dcmtk toolkit
sudo apt-get install libdcmtk2
sudo apt-get install php5-curl


### must enable curl support in php as well
#e CURL extension ext/curl is not installed or enabled in your PHP installation. Check the manual for information on how to install or enable CURL on your system.
# on ubuntu
sudo nano /etc/php5/apache2/php.ini
 nano /etc/php5/apache2/php.ini 
[sudo] password for dagutman: 
dagutman@sideshowbob:~$ sudo apt-get install curl libcurl3 libcurl3-dev php5-curl
Reading package lists... Done




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
