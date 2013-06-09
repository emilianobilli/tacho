from models  import File, Service
from time    import time
from hashlib import md5
from re	     import match

import os

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Class FileError(): Clase para raisear
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class FileError(Exception):
    def __init__(self, value):
	self.value = value
    def __str__(self):
	return repr(self.value)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Comprueba la existencia de un archivo
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ 
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
	raise FileError('GetUniqueFileID(): FileName can not be None')

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

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# CloseFile(): Cierra un archivo
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def CloseFile(ufid):
    try:
	file = File.objects.get(ufid=ufid)
    except:
	raise FileError('CloseFile(): File [ufid=%s] not found' % ufid)

    if file.status == 'O':
	file.vfilesize = 0
	file.pfilesize = os.stat(file.pfilename).st_size
	file.status = 'C'
	file.save()
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
	raise FileError('DeleteFile(): Unable to delete File [ufid=%s] not found' % ufid)

    if file.status == 'C' or file.status == 'O' or file.status == 'E':
	if FileExist(file.service.localpath, file.pfilename):
	    os.unlink(file.service.localpath + file.pfilename)
	file.delete()
    
    return True


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
	NewFile.pfilesize	= 0
        NewFile.vfilesize	= vfilespace
	NewFile.service		= Service
	NewFile.pfilename	= GetPhysicalFileName(Service.localpath, FileName)
	NewFile.status		= 'O'
	NewFile.save()

	return NewFile
    else:
	raise FileError('RegisterFile(): No have left space')


def ShareFile(ufid):
    try:
	file = File.objects.get(ufid=ufid)
    except:
	raise FileError('ShareFile(): Unable to share File [ufid=%s] not found' % ufid)

    return file.service.smbpath + file.pfilename