from mod_python import apache, Session, Cookie
from pyxnat import Interface
import os, json, tempfile, re, dicom, hashlib
import sys

def index(req):
    return "XNAT View"
 
def dump_server(req):
    """Helper for debugging, should be removed eventually."""
    result = 'req.server:'
    for attr in dir(req.server):
      result += attr + ' -> ' + repr(getattr(req.server, attr)) + '\n'
    result += '\n\nreq:'
    for attr in dir(req):
        result += attr + ' -> ' + repr(getattr(req, attr)) + '\n'
    return result

def get_web_root(req, script_depth=2, protocol='http'):
    """Gets the web root by cutting off this script's nesting level."""
    hostname = req.server.server_hostname
    
    # cut off the trailing paths from the web path
    basepath = '/'.join(req.subprocess_env['SCRIPT_NAME'].split('/')[:-script_depth]) 
        
    # FIXME protocol and port handling
    webroot = protocol + '://' + hostname + basepath
    if not webroot.endswith('/'):
        webroot += '/'
    return webroot

def is_authenticated(req, encode_output=True, session=None):
    if session is None:
        session = Session.Session(req)
    result = {'authenticated': False, 'session': [Session.COOKIE_NAME, session.id()] }
 
    if 'username' in session and 'password' in session and 'instance' in session:
        # test whether this is valid or not
        xnat = Interface(server=session['instance'],
                         user=session['username'], 
                         password=session['password'],
                         cachedir=os.path.join(req.document_root(), '.store'))
        try:
            xnat.select.projects().get()
            result['authenticated'] = True
        except:
            print >>sys.stderr, "Authentication failed."
    else:
        print >>sys.stderr, "Missing information in session."
        
    if encode_output:
        req.headers_out['Content-type'] = 'text/json'
        result = json.dumps(result)
    return result
    
def authenticate(req, username, password, instance):
    session = Session.Session(req)
    session['username'] = username
    session['password'] = password
    session['instance'] = instance
    
    auth_json = is_authenticated(req, encode_output=False, session=session)
    if not auth_json['authenticated']:
        del session['username'], session['password'], session['instance']
    
    session.save()
    req.headers_out['Content-type'] = 'text/json'
    auth_json = json.dumps(auth_json)
    return auth_json
    
def logout(req):
    session = Session.Session(req)
    if 'username' in session: del session['username']
    if 'password' in session: del session['password']
    if 'instance' in session: del session['instance']
    session.save()

def session_test(req):
    session = Session.Session(req)
    return repr(session)

def get_projects(req, *args, **kwargs):
    session = Session.Session(req)
    username = session.get('username', '')
    password = session.get('password', '')
    instance = session.get('instance', '')
    
    try:
        # setup the connection
        #instance = 'http://xnat.cci.emory.edu:8080/xnat'
        xnat = Interface(server=instance,
                        user=username, 
                        password=password,
                        cachedir=os.path.join(req.document_root(), '.store')) 
        project_list = xnat.select.projects().get()
        json_obj = []
        for project in project_list:
            json_obj.append({"project_name":project, "status":"success"})
    except:
        json_obj = [{"status":"fail"}]
    return json.dumps(json_obj)

def get_subjects(req, project_name, *args, **kwargs):
    session = Session.Session(req)
    username = session.get('username', '')
    password = session.get('password', '')
    instance = session.get('instance', '')
    try:
        # setup the connection
        xnat = Interface(server=instance,
                        user=username,
                        password=password,
                        cachedir=os.path.join(req.document_root(), '.store'))
      
        json_obj = []
        for sid in xnat.select.project(project_name).subjects().get('label'):
            json_obj.append({'subject_label':sid})
    except:
        json_obj = [{"status":"fail"}]
    return json.dumps(json_obj)


def get_experiments(req, project_name, subject_label, *args, **kwargs):
    session = Session.Session(req)
    username = session.get('username', '')
    password = session.get('password', '')
    instance = session.get('instance', '')
    
    try:
        # setup the connection
        xnat = Interface(server=instance,
                        user=username,
                        password=password,
                        cachedir=os.path.join(req.document_root(), '.store'))
   
     
        json_obj = []
        if len( xnat.select.project(project_name).subject(subject_label) \
                         .experiments().get()) == 0:
            json_obj.append({'experiment_label':"None"})
        else:
            for label in xnat.select.project(project_name).subject(subject_label).experiments().get('label'):        
                json_obj.append({'experiment_label':label})
    except:
        json_obj = [{"status": "fail"}]
    return json.dumps(json_obj)
    
def get_scans(req, project_name, subject_label, experiment_label, *args, **kwargs):
    session = Session.Session(req)
    username = session.get('username', '')
    password = session.get('password', '')
    instance = session.get('instance', '')
    
    try:
        # setup the connection
        xnat = Interface(server=instance,
                        user=username,
                        password=password,
                        cachedir=os.path.join(req.document_root(), '.store'))
      
        json_obj = []
        for scan in xnat.select.project(project_name).subject(subject_label) \
                         .experiment(experiment_label).scans():
            try:
                attr = scan.attrs.mget(['type','frames','xnat:mrScanData/parameters/tr','xnat:mrScanData/parameters/te','xnat:mrscandata/parameters/voxelres/x','xnat:mrscandata/parameters/voxelres/y','xnat:mrscandata/parameters/voxelres/z'])
            except:
                attr = ["","","","","","",""]
            json_obj.append({'scan_id':scan.id(),"scan_type":attr[0],"scan_frames":attr[1],"scan_tr":attr[2], "scan_te":attr[3], "x_res":attr[4], "y_res":attr[5], 'z_res':attr[6]})
    except:
        json_obj = [{'status': 'fail'}]
    return json.dumps(json_obj)


def downloadDicomScan(scan_object, png_folder, thumbnail_folder, docroot='/var/www/XNATVIEW'):
    temproot = os.path.join(docroot, 'IMAGE_CACHE', 'DCM_TMP')
    if not os.path.isdir(temproot): os.makedirs(temproot)
    tempDir = tempfile.mkdtemp(dir=temproot)
    scan_map = {}
    if not os.path.isdir(png_folder): os.makedirs(png_folder)
    if not os.path.isdir(thumbnail_folder): os.makedirs(thumbnail_folder)

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
        os.system("dcm2pnm "+path+" +Wn +on "+ os.path.join(png_folder, file_name+".png"))

        #create thumbnails 
        os.system("dcm2pnm "+path+" +Wn +on +Sxv 100 +Syv 100 " + os.path.join(thumbnail_folder, file_name+".png"))
         
    #cleanup dicom folder - no longer needed 
    os.system("rm -r "+tempDir)

    return scan_map


def get_dicom_scans(req, project_name, subject_label, experiment_label, scan_id):
    session = Session.Session(req)
    username = session.get('username', '')
    password = session.get('password', '')
    instance = session.get('instance', '')
    
    try:
       # setup the connection
       #instance = 'http://xnat.cci.emory.edu:8080/xnat'
       xnat = Interface(server=instance,
                        user=username,
                        password=password,
                        cachedir=os.path.join(req.document_root(), '.store'))
   
       instance = hashlib.sha1(instance).hexdigest()
       
   
       ## PATHS ON THE FS
       cache_root = os.path.join(req.document_root(), 'IMAGE_CACHE')
       png_path = os.path.join(cache_root, 'PNG_CACHE', instance)
       thumbnail_path = os.path.join(cache_root, 'THUMBNAIL_CACHE', instance)
       xml_path = os.path.join(cache_root, 'XML_FILES', instance)
       if not os.path.exists(thumbnail_path): os.makedirs(thumbnail_path)
       if not os.path.exists(png_path): os.makedirs(png_path)
       if not os.path.exists(xml_path): os.makedirs(xml_path)
            
       webroot = get_web_root(req)
   
       folder_id = project_name+'-'+subject_label+'-'+experiment_label+'-SCAN_'+scan_id
       png_folder = os.path.join(png_path, folder_id)    
       thumbnail_folder = os.path.join(thumbnail_path, folder_id)
       xml_folder = os.path.join(xml_path, folder_id)
       thumbnail_loc = '%(host)sIMAGE_CACHE/THUMBNAIL_CACHE/'+instance+'/'+folder_id+'/'
       png_loc = '%(host)sIMAGE_CACHE/PNG_CACHE/'+instance+'/'+folder_id+'/'
       ##
   
       if (os.path.exists(thumbnail_folder) and os.path.exists(png_folder) and os.path.exists(xml_folder)):
           f = open(xml_folder+folder_id+'.xml','r+')
           xml_doc = f.read()
           f.close()
       else:
           if not os.path.isdir(thumbnail_folder): os.makedirs(thumbnail_folder)
           if not os.path.isdir(png_folder): os.makedirs(png_folder)

           scan_object = xnat.select.project(project_name).subject(subject_label) \
                         .experiment(experiment_label).scan(scan_id)
           dicom_map = downloadDicomScan(scan_object, png_folder, thumbnail_folder, docroot=req.document_root())
           
           xml_doc = make_xml(dicom_map, folder_id, thumbnail_loc, png_loc, xml_folder)
           
       # FIXME temp workaround previously generated XML files
       xml_doc = xml_doc.replace('http://cerebro.cci.emory.edu/XNATVIEW/', '%(host)s')
       return xml_doc % {'host': webroot}
    except Exception, e:
        print >>sys.stderr, "Exception in get_dicom_scans:", e
        raise

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
