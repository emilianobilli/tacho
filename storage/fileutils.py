from models  import File, Service
from time    import time
from hashlib import md5
from re	     import match

import os

class FileError(Exception):
    def __init__(self, value):
	self.value = value
    def __str__(self):
	return repr(self.value)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Comprueba la existencia de un archivo
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++    
def FileExist(path, file):
    if not path.endswith('/'):
	path = path + '/'
    if os.path.isfile(path+file):
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


def GetUniqueFileID(FileName=None):
    
    if FileName is None:
	raise FileError('GetUniqueFileID(): FileName can not be None')

    timestamp = str(time())
    hasher = md5()    
    hasher.update(FileName)
    hasher.update(timestamp)
    return hasher.hexdigest()


def StringSizeToBytes(StringSize):

    result = match('([0-9]+)(B|K|M|G|T|b|k|g|t)', StringSize)
    if result:
        size = int(result.group(1))
        unit = result.group(2).upper()
    else:
        raise FileError('StringSizeToBytes(): StringSize is not a valid value [%s]' % str(StringSize))

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


def CloseFile(ufid):
    try:
	file = File.objects.get(ufid=ufid)
    except:
	raise FileError('CloseFile(): File [ufid=%s] not found' % ufid)

    if file.status == 'O':
	#
	# fisical space agregar
	#
	file.status = 'C'
	file.save()
        return True
    else:
	return False


def DeleteFile(ufid):
    try:
	file = File.objects.get(ufid=ufid)
    except:
	raise FileError('DeleteFile(): Unable to delete File [ufid=%s] not found' % ufid)

    if file.status == 'C':
	if FileExist(file.service.localpath, file.pfilename):
	    os.unlink(file.service.localpath + file.pfilename)
	    return True

    elif file.status == 'O':
	file.delete()
	return True

    return False


def RegisterFile(Service=None, FileName=None, ProvisionedSpace="10G"):

    if Service  is None:
	raise FileError('RegisterFile(): Service can not be None')

    if FileName is None:
	raise FileError('RegisterFile(): FileName can not be None')

    vfilespace = StringSizeToBytes(ProvisionedSpace)
    
    if Service.freespace - vfilespace > 0:
	NewFile = File()
	NewFile.vfilename 	= FileName
        NewFile.ufid		= GetUniqueFileID(FileName)
        NewFile.vfilesize	= vfilespace
	NewFile.service		= Service
	NewFile.pfilename	= GetPhysicalFileName(Service.localpath, FileName)
	NewFile.status		= 'O'
	NewFile.save()

	return NewFile
    else:
	raise FileError('RegisterFile(): No have left space')

