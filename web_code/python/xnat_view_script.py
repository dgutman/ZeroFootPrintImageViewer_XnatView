from mod_python import apache
from pyxnat import Interface
import os, json, tempfile, re, dicom, hashlib

def index(req):
    return "XNAT View"

def get_projects(req,username,password,instance):
    # setup the connection
    #instance = 'http://xnat.cci.emory.edu:8080/xnat'
    xnat = Interface(server=instance,
                     user=username, 
                     password=password,
                     cachedir=os.path.join(os.path.expanduser('~'),'XNATVIEW/.store')) 
    try: 
        project_list = xnat.select.projects().get()
        json_obj = []
        for project in project_list:
            json_obj.append({"project_name":project, "status":"success"})
    except:
        json_obj = [{"status":"fail"}]
    return json.dumps(json_obj)

def get_subjects(req,username,password, instance,project_name):
    # setup the connection
    
    xnat = Interface(server=instance,
                     user=username,
                     password=password,
                     cachedir=os.path.join(os.path.expanduser('~'),'XNATVIEW/.store'))
   
    json_obj = []
    for sid in xnat.select.project(project_name).subjects().get('label'):
        json_obj.append({'subject_label':sid})
    return json.dumps(json_obj)


def get_experiments(req,username,instance, password,project_name,subject_label):
    # setup the connection
   
    xnat = Interface(server=instance,
                     user=username,
                     password=password,
                     cachedir=os.path.join(os.path.expanduser('~'),'XNATVIEW/.store'))

  
    json_obj = []
    if len( xnat.select.project(project_name).subject(subject_label) \
                      .experiments().get()) == 0:
        json_obj.append({'experiment_label':"None"})
    else:
        for label in xnat.select.project(project_name).subject(subject_label).experiments().get('label'):        
            json_obj.append({'experiment_label':label})

    return json.dumps(json_obj)
    
def get_scans(req,username,password,instance, project_name,subject_label,experiment_label):
    # setup the connection
   
    xnat = Interface(server=instance,
                     user=username,
                     password=password,
                     cachedir=os.path.join(os.path.expanduser('~'),'XNATVIEW/.store'))
   
    json_obj = []
    for scan in xnat.select.project(project_name).subject(subject_label) \
                      .experiment(experiment_label).scans():
        try:
            attr = scan.attrs.mget(['type','frames','xnat:mrScanData/parameters/tr','xnat:mrScanData/parameters/te','xnat:mrscandata/parameters/voxelres/x','xnat:mrscandata/parameters/voxelres/y','xnat:mrscandata/parameters/voxelres/z'])
        except:
            attr = ["","","","","","",""]
        json_obj.append({'scan_id':scan.id(),"scan_type":attr[0],"scan_frames":attr[1],"scan_tr":attr[2], "scan_te":attr[3], "x_res":attr[4], "y_res":attr[5], 'z_res':attr[6]})
    return json.dumps(json_obj)


def downloadDicomScan(scan_object, png_folder, thumbnail_folder):

    tempDir = tempfile.mkdtemp(dir='/var/www/XNATVIEW/IMAGE_CACHE/DCM_TMP/')
    scan_map = {}
    os.system("mkdir "+png_folder)
    os.system("mkdir "+thumbnail_folder)

    files = scan_object.resource('DICOM').files()
    for each_file in files:
        #download from XNAT
        path = os.path.join(tempDir,each_file.id())
        each_file.get(path,False)
        file_name = re.search('.(.*).dcm',each_file.id()).group(1)
        dicomData = dicom.read_file(path)
        key =  str(dicomData.InstanceNumber) 
        scan_map[key] = file_name

        #convert to png 
        os.system("dcm2pnm "+path+" +Wn +on "+png_folder+file_name+".png")

        #create thumbnails 
        os.system("dcm2pnm "+path+" +Wn +on +Sxv 100 +Syv 100 "+thumbnail_folder+file_name+".png")
         
    #cleanup dicom folder - no longer needed 
    os.system("rm -r "+tempDir)

    return scan_map


def get_dicom_scans(req,username,password,instance ,project_name,subject_label,experiment_label,scan_id):
    # setup the connection
    #instance = 'http://xnat.cci.emory.edu:8080/xnat'
    xnat = Interface(server=instance,
                     user=username,
                     password=password,
                     cachedir=os.path.join(os.path.expanduser('~'),'XNATVIEW/.store'))

    instance = hashlib.sha1(instance).hexdigest()
    

    ## PATHS ON THE FS
    png_path = '/var/www/XNATVIEW/IMAGE_CACHE/PNG_CACHE/'+instance+'/'
    thumbnail_path = '/var/www/XNATVIEW/IMAGE_CACHE/THUMBNAIL_CACHE/'+instance+'/'
    xml_path = '/var/www/XNATVIEW/IMAGE_CACHE/XML_FILES/'+instance+'/'
    if not os.path.exists(thumbnail_path):
         os.system("mkdir "+thumbnail_path)
    if not os.path.exists(png_path):
         os.system("mkdir "+png_path)
    if not os.path.exists(xml_path):
         os.system("mkdir "+xml_path)

    folder_id = project_name+'-'+subject_label+'-'+experiment_label+'-SCAN_'+scan_id
    png_folder = png_path+folder_id+'/'    
    thumbnail_folder = thumbnail_path+folder_id+'/'
    xml_folder = xml_path+folder_id+'/'
    thumbnail_loc = 'http://cerebro.cci.emory.edu/XNATVIEW/IMAGE_CACHE/THUMBNAIL_CACHE/'+instance+'/'+folder_id+'/'
    png_loc = 'http://cerebro.cci.emory.edu/XNATVIEW/IMAGE_CACHE/PNG_CACHE/'+instance+'/'+folder_id+'/'
    ##

    if (os.path.exists(thumbnail_folder) and os.path.exists(png_folder) and os.path.exists(xml_folder)):
        f = open(xml_folder+folder_id+'.xml','r+')
        xml_doc = f.read()
        f.close()
    else:
        scan_object = xnat.select.project(project_name).subject(subject_label) \
                      .experiment(experiment_label).scan(scan_id)
        dicom_map = downloadDicomScan(scan_object, png_folder, thumbnail_folder)
        
        xml_doc = make_xml(dicom_map, folder_id, thumbnail_loc, png_loc, xml_folder)
        
    # compatibility with new format from xnatview_backend.py
    xml_doc = xml_doc % {'host': 'http://cerebro.cci.emory.edu/XNATVIEW/'}
    
    return xml_doc

def make_xml(dicom_map,folder_id, thumbnail_loc, png_loc, xml_folder):
   
    os.system("mkdir "+xml_folder)

    slices = []
    #convert the keys to int and then sort
    for key in dicom_map.keys():
         slices.append(int(key))
    slices.sort()

    f = open(xml_folder+folder_id+".xml",'w')
    xml_string = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<gallery>\n"

    for key in slices:
        file_name = dicom_map[str(key)]

        #create the xml
        image_string="<image title=\""+file_name+"\" thumbnailImage=\""+thumbnail_loc+file_name \
                     +".png\" fullImage=\""+png_loc+file_name+".png\"/>\n"
        xml_string += image_string

    xml_string += "</gallery>"
    f.write(xml_string)
    f.close()
    return xml_string











