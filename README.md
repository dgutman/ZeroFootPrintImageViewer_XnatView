ZeroFootPrintImageViewer_XnatView
=================================

I agre this is a terrible name--- this is a Zero Foot Print Image Viewer (aka XnatView) that allows PACS like functionality from XNAT


This is a web-based image viewer that connects to an XNAT desktop, although the pipeline that generates the images
could be later to ideally view images from any PACS..



Installation/Dependencies:

Installing initial version on Stock Ubuntu 12.04LTS Desktop

After base install, and setting up IP address

sudo apt-get update  ### get latest set of packages
sudo apt-get upgrade # install new packages-- then rebooted
sudo reboot ## just to apply any kernel patches

sudo apt-get install openssh-server 
sudo apt-get install php5  apache2 


### need to install pyxnat-- will install from source

#created a directory in my rootdir to place pyxnat and other programs I am pulling from git
mkdir dev_source_code
