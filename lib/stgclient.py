import xmlrpclib
import socket

class StorageClientError(Exception):
    def __init__(self, value, critical=False):
        self.value   = value
	self.critical= critical
    def __str__(self):
        return repr(self.value)


def Storage_RegisterFile(StorageHost, ServiceName, FileName, ProvisionedSpace, Port=3000):

    try:
	Storage = xmlrpclib.ServerProxy('http://'+ StorageHost + ':' + str(Port), allow_none=True)
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


def Storage_CloseFile(StorageHost, ufid, Port=3000):
    try:
	Storage = xmlrpclib.ServerProxy('http://' + StorageHost + ':' + str(Port), allow_none=True)
	Reply = Storage.CloseFile(ufid)
	if Reply['result']:
	    return Reply['result']
	else:
	    raise StorageClientError(Reply['error'])

    except xmlrpclib.ProtocolError as err:
	raise StorageClientError(err.errmsg, True)
    except xmlrpclib.Fault as err:
	raise StorageClientError(err.FaultString)
    except socket.error as e:
	raise StorageClientError('Catch socket.error: ' + str(e),True)

