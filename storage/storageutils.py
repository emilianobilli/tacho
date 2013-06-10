from models  import File, Service
from time    import time
from hashlib import md5
from re	     import match

import os

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Class StorageError(): Clase para raisear
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
class StorageError(Exception):
    def __init__(self, value):
	self.value = value
    def __str__(self):
	return repr(self.value)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Comprueba la existencia de un archivo
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ 
def FileExist(path, file):

    pfile = None
    try:
	pfile = File.objects.get(pfilename=file)
    except:
	pass

    if not path.endswith('/'):
	path = path + '/'
    if os.path.isfile(path+file) or pfile is not None:
        return True

    return False


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Elimina las extensiones (Considera que puede haber puntos en el medio del archivo)
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def SplitExtension(FileName=None):
    
    if FileName is not None:
        basename_tmp_list = FileName.split('.')
        i = 1
        basename = basename_tmp_list[0]
        while i < len(basename_tmp_list) -1:
            basename = basename + '.' + basename_tmp_list[i]
            i = i + 1
        return basename, basename_tmp_list[len(basename_tmp_list)-1]
    return None, None


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# GetPhysicalFileName(): Retorna el nombre real del archivo en el sistema 
# 
# Intenta utilizar el nombre pasado por parametro, de no ser posible
# agrega _VER-[0-9] hasta encontrar un file que si pueda crear
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def GetPhysicalFileName(Path, FileName):

    if FileExist(Path,FileName):
	BaseName, Ext = SplitExtension(FileName)
	result = match('(.+)(_VER-)([0-9]+)', BaseName)
	if result:
	    Base = result.group(1)
	    Ver	 = result.group(2)
	    Vern = result.group(3)
	    return GetPhysicalFileName(Path,Base + Ver + str( int (Vern) + 1 ) + '.' + Ext)
	else:
	    return GetPhysicalFileName(Path,BaseName + '_VER-0.' + Ext )
    else:
	return FileName


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# GetUniqueFileID(): Genera un id de file, basado en el nombre del archivo y
# el timestamp generando un resumen md5
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def GetUniqueFileID(FileName=None):
    
    if FileName is None:
	raise StorageError('GetUniqueFileID(): FileName can not be None')

    timestamp = str(time())
    hasher = md5()    
    hasher.update(FileName)
    hasher.update(timestamp)
    return hasher.hexdigest()


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# StringSizeToBytes(): Convierte un tamanio en bytes
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def StringSizeToBytes(StringSize):

    result = match('([0-9]+)(B|K|M|G|T|b|k|g|t)', StringSize)
    if result:
        size = int(result.group(1))
        unit = result.group(2).upper()
    else:
        raise StorageError('StringSizeToBytes(): StringSize is not a valid value [%s]' % str(StringSize))

    if   unit == 'B':
        return size
    elif unit == 'K':
        return size * 1024
    elif unit == 'M':
        return size * 1024 * 1024
    elif unit == 'G':
        return size * 1024 * 1024 * 1024
    else:
        return size * 1024 * 1024 * 1024 * 1024


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CloseFile(): Cierra un archivo
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def CloseFile(ufid):
    try:
	file = File.objects.get(ufid=ufid)
    except:
	raise StorageError('CloseFile(): File [ufid=%s] not found' % ufid)

    if file.status == 'O':
	file.vfilesize = 0
	try:
	    file.pfilesize = os.stat(file.service.localpath + file.pfilename).st_size
	except OSError as e:
	    raise StorageError(e.strerror + ' [ ' + e.filename + ' ]')

	file.status = 'C'
	file.save()

	SFreeSpace = CalculateFreeSpace(file.service)
	file.service.freespace = SFreeSpace
	file.service.save()

        return True
    else:
	return False


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# DeleteFile(): Borra un archivo
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def DeleteFile(ufid):
    try:
	file = File.objects.get(ufid=ufid)
    except:
	raise StorageError('DeleteFile(): Unable to delete File [ufid=%s] not found' % ufid)

    if file.status == 'C' or file.status == 'O' or file.status == 'E':
	service = file.service

	if FileExist(file.service.localpath, file.pfilename):
	    try:
		os.unlink(file.service.localpath + file.pfilename)
	    except:
		pass
	file.delete()

	SFreeSpace = CalculateFreeSpace(service)
	service.freespace = SFreeSpace
	service.save()
    
    return True


def RegisterFile(Service=None, FileName=None, ProvisionedSpace="10G"):

    if Service  is None:
	raise StorageError('RegisterFile(): Service can not be None')

    if FileName is None:
	raise StorageError('RegisterFile(): FileName can not be None')

    vfilespace = StringSizeToBytes(ProvisionedSpace)
    
    if Service.freespace - vfilespace > 0:
	NewFile = File()
	NewFile.vfilename 	= FileName
        NewFile.ufid		= GetUniqueFileID(FileName)
	NewFile.pfilesize	= 0
        NewFile.vfilesize	= vfilespace
	NewFile.service		= Service
	NewFile.pfilename	= GetPhysicalFileName(Service.localpath, FileName)
	NewFile.status		= 'O'
	NewFile.save()
	
	SFreeSpace = CalculateFreeSpace(Service)
	Service.freespace = SFreeSpace
	Service.save()

	return NewFile
    else:
	raise StorageError('RegisterFile(): No have left space')


def ShareFile(ufid):
    try:
	file = File.objects.get(ufid=ufid)
    except:
	raise StorageError('ShareFile(): Unable to share File [ufid=%s] not found' % ufid)

    return file.service.smbpath + file.pfilename



def CalculateFreeSpace(service = None):

    if service is None:
	raise StorageError('CalculateFreeSpace(): service argument can not be None')

    FileList = File.objects.filter(service=service)

    UsedSpace = 0
    for file in FileList:
	if   file.status == 'O':
	    UsedSpace = UsedSpace + file.vfilesize
	elif file.status == 'C':
	    UsedSpace = UsedSpace + file.pfilesize

    return service.servicesize - UsedSpace


def SplitUriSchema(Uri=None):

    if Uri is None:
	raise StorageError('SplitUriSchema(): Uri can not be None')

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
	raise StorageError('SplitUriSchema(): Uri Sintax Wrong [%s] expect: %s' % (Uri,ftp_uri_re))

