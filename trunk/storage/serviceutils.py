from models  import File, Service

from re import match

class ServiceError(Exception):
    def __init__(self, value):
	self.value = value
    def __str__(self):
	return repr(self.value)


def CalculateFreeSpace(service = None):

    if service is None:
	raise ServiceError('CalculateFreeSpace(): service argument can not be None')
    FileList = File.objects.filter(service=service)

    UsedSpace = 0
    for file in FileList:
	if file.status == 'O':
	    UsedSpace = UsedSpace + file.vfilesize
	elif file.status == 'C':
	    UsedSpace = UsedSpace + file.pfilesize

    return service.servicesize - UsedSpace


def SplitUriSchema(Uri=None):

    if Uri is None:
	raise ServiceError('SplitUriSchema(): Uri can not be None')

    ftp_uri_re  = '(ftp://)(.+):([0-9]*)/(.+)'
    cred_uri_re = '(.+):(.+)@(.+)'
    ftp_uri_result = match(ftp_uri_re, Uri)


    if ftp_uri_result:
	credentials = ftp_uri_result.group(2)
	if ftp_uri_result.group(3) != '':
	    port = int(ftp_uri_result.group(3))
	else:
	    port = 21

	abs_path    = ftp_uri_result.group(4)
	cred_uri_result = match(cred_uri_re, credentials)
	if cred_uri_result:
	    username	= cred_uri_result.group(1)
	    password	= cred_uri_result.group(2)
	    hostname	= cred_uri_result.group(3)
	else:
	    hostname	= credentials
	    username	= ''
	    password	= ''

	PathList = abs_path.split('/')
	filename = PathList[len(PathList)-1]
	path = ''
	for p in PathList[:len(PathList)-1]:
	    path = path + '/' + p

	if not path.endswith('/'):
	    path = path + '/'
	
	return dict([( 'username',username ),
		     ( 'password',password ),
		     ( 'hostname',hostname ),
		     ( 'filename',filename ),
		     ( 'path',path ),
		     ( 'port',port )])
    else:
	raise ServiceError('SplitUriSchema(): Uri Sintax Wrong [%s] expect: %s' % (Uri,ftp_uri_re))

