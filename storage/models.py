from django.db import models

# Create your models here.
class Service(models.Model):
    SERVICE_STATUS = (
	('E', 'Enabled'),
	('D', 'Disabled'),
    )
    servicename		= models.CharField(max_length=100)
    servicesize		= models.BigIntegerField(default=0)
    freespace		= models.BigIntegerField(default=0)
    localpath		= models.CharField(max_length=256)
    smbpath		= models.CharField(max_length=256)
    status		= models.CharField(max_length=1, choices=SERVICE_STATUS, default='E')
    maxout		= models.IntegerField(default=0)
    maxin		= models.IntegerField(default=0)
    maxsmbout		= models.IntegerField(default=0)
    maxsmbin		= models.IntegerField(default=0)

    def __unicode__(self):
	return self.servicename


class File(models.Model):
    FILE_STATUS = (
	('O', 'Open'),
	('C', 'Close'),
	('E', 'Expired'),
    )
    ufid	= models.CharField(max_length=32, unique=True)
    vfilename	= models.CharField(max_length=512)
    pfilename	= models.CharField(max_length=256)
    vfilesize	= models.BigIntegerField(default=0)
    pfilesize	= models.BigIntegerField(default=0)
    service	= models.ForeignKey('Service')
    status	= models.CharField(max_length=1, choices=FILE_STATUS, default='O')


    def __unicode__(self):
	return self.pfilename







