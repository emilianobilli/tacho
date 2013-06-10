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
from storage.storageutils import StorageError

import logging
import sys
from lib.daemon import Daemon


def Public_RegisterFile(ServiceName=None,FileName=None, ProvisionedSpace="1G"):

    if ServiceName is not None:
	try:
	    Svc = Service.objects.get(servicename=ServiceName)
	    if Svc.status == 'D':
		return dict([('result', False),
			    ('ufid', ''),
			    ('error', 'Public_RegisterFile(): Service [%s] is Disabled' % ServiceName)])
	except:
	    return dict([('result', False),
			 ('ufid', ''),
			 ('error', 'Public_RegisterFile(): Unable to find service [%s]' % ServiceName)])

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
		     ('error', 'Public_RegisterFile(): ServiceName can not be None')])



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


class main_daemon(Daemon):
    def run(self):
        try:
            Main()
        except KeyboardInterrupt:
            sys.exit()      

if __name__ == "__main__":
        daemon = main_daemon(settings.STGDAEMON_PID, stdout=settings.STGDAEMON_LOG, stderr=settings.STGDAEMON_LOG)
        if len(sys.argv) == 2:
                if 'start'     == sys.argv[1]:
                        daemon.start()
                elif 'stop'    == sys.argv[1]:
                        daemon.stop()
                elif 'restart' == sys.argv[1]:
                        daemon.restart()
                elif 'run'     == sys.argv[1]:
                        daemon.run()
                elif 'status'  == sys.argv[1]:
                        daemon.status()
                else:
                        print "Unknown command"
                        sys.exit(2)
                sys.exit(0)
        else:
                print "usage: %s start|stop|restart|run" % sys.argv[0]
                sys.exit(2)
