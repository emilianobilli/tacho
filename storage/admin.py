from django.contrib import admin
from models import *


class FileAdmin(admin.ModelAdmin):
    list_display = ( 'ufid', 'vfilename', 'pfilesize', 'status' )

class ServiceAdmin(admin.ModelAdmin):
    list_display = ( 'servicename', 'servicesize', 'freespace', 'status' )

class QueueAdmin(admin.ModelAdmin):
    list_display = ( 'id', 'action', 'uri', 'status', 'progress', 'speed_mbps' )

admin.site.register(Queue,QueueAdmin)
admin.site.register(Service,ServiceAdmin)
admin.site.register(File,FileAdmin)