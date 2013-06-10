import xmlrpclib
import socket

class StorageClientError(Exception):
    def __init__(self, value, critical=False):
        self.value   = value
	self.critical= critical
    def __str__(self):
        return repr(self.value)


def Storage_RegisterFile(StorageHost, ServiceName, FileName, ProvisionedSpace):

    try:
	Storage = xmlrpclib.ServerProxy('http://'+ StorageHost + ':' + '3000', allow_none=True)
	Reply = Storage.RegisterFile(ServiceName,FileName,ProvisionedSpace)
	if Reply['result']:
	    return Reply['ufid']
	else:
	    raise StorageClientError(Reply['error'])

    except xmlrpclib.ProtocolError as err:
	raise StorageClientError(err.errmsg, True)
    except xmlrpclib.Fault as err:
	raise StorageClientError(err.FaultString)
    except socket.error as e:
	raise StorageClientError('Catch socket.error: ' + str(e),True)

try:
    print Storage_RegisterFile('localhost', 'Jose', 'Pirulo', '10b')
except StorageClientError as e:
    print e.value
    print "Critical: " + str(e.critical)
