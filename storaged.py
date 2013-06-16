#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Stand alone script
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from django.core.management import setup_environ
from tacho import settings
setup_environ(settings)

from lib.daemon import Daemon

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Modelo de la aplicacion
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from storage.models import Service
from storage.models import File
from storage.models import Queue

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Funciones StorageUtils
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from storage.storageutils import GetFile
from storage.storageutils import PutFile
from storage.storageutils import StorageError
from storage.storageutils import TotalSchedulableQueue_Put
from storage.storageutils import TotalSchedulableQueue_Get
from storage.storageutils import DequeueBestCandidate_Get
from storage.storageutils import DequeueBestCandidate_Put

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# OS System calls
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from os   import wait
from os   import fork
from os   import getpid
from sys  import exit
from sys  import argv
from time import sleep
import logging

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Signals
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from signal import signal
from signal import SIGCHLD


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# WorkerDie(): Manejador de la signal SIGCHLD, comprueba que el hijo no haya muerto 
#              de manera inesperada y corrige el resultado de la transferencia
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def WorkerDie(signaln, frame):
    pid, status = wait()

    try:
	# Busca cual es el hijo que termino
	Q = Queue.objects.get(worker_pid=pid)
	if Q.status == 'A':
    	    # Fallo inesperadamente
    	    logging.error('WorkerDie(): Worker [Pid=%d] died with status [%d]' % (pid,status))
    	    logging.error('WorkerDie(): Queue [%s] in error state' % Q)
	    Q.status = 'E'
    	    Q.error  = 'Worker died Unexpectedly'
    	    Q.save()
	else:
    	    logging.info('WorkerDie(): Worker [Pid=%d] end, Transfer result = %s' % (pid,Q.status))
    except:
	# No lo encontro, es un hijo no reconocido
	logging.error('WorkerDie(): Unregistred worker die [Pid=%d]' % pid)


def ForkWorker(Queue=None):

    if Queue is None:
	logging.error('ForkWorker(): Queue can not be None')
	return False

    logging.info('ForkWorker(): Starting Worker for Queue[%s], QUID: %s' % (Queue, Queue.uqid))

    Queue.status = 'A'
    Queue.save()

    try:
	Pid = fork()
    except OSError as e:
	logging.error('ForkWorker(): Can not call fork() -> [%s]' % e.strerror)
	return False

    if Pid == 0:

	WorkerPid = getpid()
	Queue.worker_pid = WorkerPid
	Queue.save()

	if   Queue.action == 'G':
	    try:
		logging.info('WORKER[%d]: Start processing [%s]' % (WorkerPid,Queue))
		GetFile(Queue)
		logging.info('WORKER[%d]: End processing [%s] - OK' % (WorkerPid,Queue))
		Queue.status = 'D'
		Queue.save()

	    except StorageError as e:
		logging.error('WORKER[%d]: End processing [%s] - ERROR[%s]' % (WorkerPid,Queue,e.value))
		Queue.status = 'E'
		Queue.error  = e.value
		Queue.save()

	elif Queue.action == 'P':
	    try:
		logging.info('WORKER[%d]: Start processing [%s]' % (WorkerPid,Queue))
		PutFile(Queue)
		logging.info('WORKER[%d]: End processing [%s] - OK' % (WorkerPid,Queue))
		Queue.status = 'D'
		Queue.save()

	    except StorageError as e:
		logging.error('WORKER[%d]: End processing [%s] - ERROR[%s]' % (WorkerPid,Queue,e.value))
		Queue.status = 'E'
		Queue.error  = e.value
		Queue.save()
	exit(0)
    
    logging.info('ForkWorker(): Worker Pid -> [%d]' % Pid)
    return True


def StoragedMain():

    # Registra el manejador de la senial SIGCHLD
    signal(SIGCHLD, WorkerDie)


    # Configura el archivo de log
    logging.basicConfig(format   = '%(asctime)s - storaged.py -[%(levelname)s]: %(message)s', 
			filename = settings.STORAGED_LOG,
			level    = logging.INFO)

    
    logging.info('StoragedMain(): Staring Storage Daemon operation')

    End = False
    while not End:

	# Trae todos los servicios Activos
	ServiceList = Service.objects.filter(status='E')
	for service in ServiceList:
	    
	    logging.info('StorageMain(): Start Checking Service [%s]' % service.servicename)	

	    Qlen_Get = TotalSchedulableQueue_Get(service)
	    logging.info('StorageMain(): Get Schedulable: %d', Qlen_Get)
	    i    = 0
	    flag = False
	    while i < Qlen_Get and not flag:
		Q = DequeueBestCandidate_Get(service)
		if Q:
		    result = ForkWorker(Q)
		    if not result:
			End = True
			continue
		else:
		    logging.info('StorageMain(): No more candidates')
		    flag = True

	    Qlen_Put = TotalSchedulableQueue_Put(service)
	    logging.info('StorageMain(): Put Schedulable: %d', Qlen_Put)
	    i    = 0
	    flag = False
	    while i < Qlen_Put and not flag:
		Q = DequeueBestCandidate_Put(service)
		if Q:
		    result = ForkWorker(Q)
		    if not result:
			End = True
			continue
		else:
		    logging.info('StorageMain(): No mode candidates')
		    flag = True
	
	logging.info('StorageMain(): No more work -> Sleep')
	sleep(10)


class DaemonMain(Daemon):
    def run(self):
        try:
            StoragedMain()
        except KeyboardInterrupt:
            exit()      

if __name__ == "__main__":
        daemon = DaemonMain(settings.STORAGED_PID, stdout=settings.STORAGED_LOG, stderr=settings.STORAGED_LOG)
        if len(argv) == 2:
                if 'start'     == argv[1]:
                        daemon.start()
                elif 'stop'    == argv[1]:
                        daemon.stop()
                elif 'restart' == argv[1]:
                        daemon.restart()
                elif 'run'     == argv[1]:
                        daemon.run()
                elif 'status'  == argv[1]:
                        daemon.status()
                else:
                        print "Unknown command"
                        exit(2)
                exit(0)
        else:
                print "usage: %s start|stop|restart|run" % sys.argv[0]
                exit(2)

