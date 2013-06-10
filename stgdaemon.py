#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# RPC XML
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Stand alone script
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from django.core.management import setup_environ
from tacho import settings
setup_environ(settings)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Modelo de la aplicacion
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from storage.models import Service
from storage.models import File

from storage.storageutils import DeleteFile
from storage.storageutils import CloseFile
from storage.storageutils import RegisterFile

import logging
from lib.daemon import Daemon


def Public_RegisterFile(ServiceName=None,FileName=None, ProvisionedSpace="1G"):

    if ServiceName is not None:
	try:
	    Svc = Service.objects.get(servicename=ServiceName)
	except:
	    return dict([('result', False),
			 ('ufid', ''),
			 ('error', 'Unable to find service [%s]' % ServiceName)])

	try:
	    file = RegisterFile(Svc,FileName,ProvisionedSpace)
	    return dict([('result', True),
			 ('ufid', file.ufid),
			 ('error', '')])

	except StorageError as e:
	    return dict([('result', False),
			 ('ufid', ''),
		         ('error', e.value)])

    else:
	return dict([('result', False),
		     ('ufid', ''),
		     ('error', 'ServiceName can not be None')])



def Public_CloseFile(ufid=None):
    try:
	result = CloseFile(ufid)
	return dict([('result', result),
		     ('error', '')])
    except StorageError as e:
	return dict([('result', False),
		     ('error', e.value)])


def Public_DeleteFile(ufid=None):
    try:
	result = DeleteFile(ufid)
	return dict([('result', result),
		     ('error', '')])
    except StorageError as e:
	return dict([('result', False),
		     ('error', e.value)])


def Public_ShareFile(ufid=None):
    try:
	result = ShareFile(ufid)
	return dict([('result', True),
		     ('uncpath', result),
		     ('error', '')])
    except StorageError as e:
	return dict([('result', False),
		     ('uncpath', ''),
		     ('error', e.value)])



def Main():
    
    logging.basicConfig(format  ='%(asctime)s - stgdaemon.py -[%(levelname)s]: %(message)s', 
			filename=settings.STGDAEMON_LOG,
			level=logging.INFO)

    server = SimpleXMLRPCServer((settings.STGDAEMON_HOST, int(settings.STGDAEMON_PORT)), allow_none=True)
    server.register_introspection_functions()
    server.register_function(Public_RegisterFile, 'RegisterFile')
    server.register_function(Public_CloseFile,    'CloseFile'   )
    server.register_function(Public_DeleteFile,   'DeleteFile'  )
    server.register_function(Public_ShareFile,    'ShareFile'   )

    server.serve_forever()

Main()

