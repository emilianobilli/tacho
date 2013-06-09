from models  import File, Service


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



