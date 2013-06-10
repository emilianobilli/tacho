from django.db import models

# Create your models here.

class Storage(models.Model):
    name	= models.CharField(max_length=50)
    hostname	= models.CharField(max_length=100)
    port	= models.IntegerField(default=3000)

    def __unicode__(self):
	return self.name

class Service(models.Model):
    SERVICE_ROL = ( 
	( 'I', 'Import' ),
	( 'E', 'Export' ),
	( 'M', 'Mixed'  ),
    )
    SERVICE_STATUS = (
	( 'E', 'Enabled' ),
	( 'D', 'Disabled'),
    )
    servicename = models.CharField(max_length=100)
    storage	= models.ForeignKey('Storage')
    rol		= models.CharField(max_length=1, choices=SERVICE_ROL)
    status	= models.CharField(max_length=1, choices=SERVICE_STATUS)

    def __unicode__(self):
	return self.servicename

