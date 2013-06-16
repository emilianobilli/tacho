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
    maxput		= models.IntegerField(default=0)
    maxget		= models.IntegerField(default=0)
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
    ufid	= models.CharField(max_length=36, unique=True)
    vfilename	= models.CharField(max_length=512)
    pfilename	= models.CharField(max_length=256)
    vfilesize	= models.BigIntegerField(default=0)
    pfilesize	= models.BigIntegerField(default=0)
    service	= models.ForeignKey('Service')
    status	= models.CharField(max_length=1, choices=FILE_STATUS, default='O')


    def __unicode__(self):
	return self.pfilename


class Queue(models.Model):
    QUEUE_ACTION = (
	( 'G', 'Get' ),
	( 'P', 'Put' ),
    )
    QUEUE_STATUS = (
	( 'Q', 'Queued' ),
	( 'A', 'Active' ),
	( 'D', 'Done' ),
	( 'E', 'Error'),
    )
    uqid	= models.CharField(max_length=36, unique=True)
    uri		= models.CharField(max_length=512)
    file	= models.ForeignKey('File', null=True, blank=True)
    action	= models.CharField(max_length=1, choices=QUEUE_ACTION)
    priority	= models.IntegerField(default=10)
    service	= models.ForeignKey('Service')
    worker_pid	= models.IntegerField(default=-1)
    status	= models.CharField(max_length=1, choices=QUEUE_STATUS)
    progress	= models.IntegerField(default=0)
    error	= models.CharField(max_length=512, null=True, blank=True)
    speed_mbps	= models.DecimalField(blank=True,null=True, max_digits=5, decimal_places=3)

    def __unicode__(self):
	return self.action + ': -> ' + self.uri





