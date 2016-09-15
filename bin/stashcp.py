import optparse
import sys
import subprocess
import datetime
import time
import re
import os
import json
import multiprocessing
import urllib2

parser = optparse.OptionParser()
parser.add_option('--debug', dest='debug', action='store_true', help='debug')
parser.add_option('-r', dest='recursive', action='store_true', help='recursively copy')
parser.add_option('--closest', action='store_true')
args,opts=parser.parse_args()

def find_closest():
    closest=subprocess.Popen(['./get_best_stashcache.py', '0'], stdout=subprocess.PIPE)
    cache=closest.communicate()[0].split()[0]
    return cache

if not args.closest:
    try:
        source=opts[0]
        destination=opts[1]
    except:
        parser.error('Source and Destination must be last two arguments')
else:
    print find_closest()
    sys.exit()

if not args.debug:
    xrdargs=0
else:
    xrdargs=1

TIMEOUT = 300
DIFF = TIMEOUT * 10


def doStashCpSingle(sourceFile=source, destination=destination):
    xrdfs = subprocess.Popen(["xrdfs", "root://stash.osgconnect.net", "stat", sourceFile], stdout=subprocess.PIPE).communicate()[0]
    fileSize=re.findall(r"Size:   \d+",xrdfs)[0].split(":   ")[1]
    fileSize=int(fileSize)
    cache=find_closest()
    command = "python ./timeout.py -t "+str(TIMEOUT)+ " -f "+sourceFile + " -d "+str(DIFF)+" -s "+str(fileSize)+" -x "+str(xrdargs)+" -c "+cache+" -z "+destination
    date=datetime.datetime.now()
    start1=int(time.mktime(date.timetuple()))*1000
    copy=subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
    xrd_exit=copy.communicate()[0].split()[-1]
    date=datetime.datetime.now()
    end1=int(time.mktime(date.timetuple()))*1000
    filename=destination+'/'+sourceFile.split('/')[-1]
    dlSz=os.stat(filename).st_size
    destSpace=1000
    try:
        sitename=os.environ['OSG_SITE_NAME']
    except:
        sitename="siteNotFound"
    xrdcp_version="4.2.1"
    start2=0
    start3=0
    end2=0
    xrdexit2=-1
    xrdexit3=-1
    if xrd_exit=='0': #worked first try
        dltime=end1-start1
        status = 'Success'
        tries=1
        payload="{ \"timestamp\" : %d, \"host\" : '%s', \"filename\" : '%s', \"filesize\" : %d, \"download_size\" : %d, \"download_time\" : %d,  \"sitename\" : '%s', \"destination_space\" : %d, \"status\" : '%s', \"xrdexit1\" : %s, \"xrdexit2\" : %d, \"xrdexit3\" : %d, \"tries\" : %d, \"xrdcp_version\" : '%s', \"start1\" : %d, \"end1\" : %d, \"start2\" : %d, \"end2\" : %d, \"start3\" : %d, \"cache\" : '%s'}" % (end1, cache, sourceFile, fileSize, dlSz, dltime, sitename, destSpace, status, xrd_exit, xrdexit2, xrdexit3, tries, xrdcp_version, start1, end1, start2, end2, start3, cache)
        payload=payload.replace("'", '"')
        payload=payload.replace('{', "'{")
        payload=payload.replace('}', "}'")
        try:
            p = multiprocessing.Process(target=es_send, name="es_send", args=(payload,))
            p.start()
            time.sleep(5)
            p.terminate()
            p.join()
        except:
            print "Error posting to ES"
    else: #copy again using same cache
        print "1st try failed on %s, trying again" % cache
        date=datetime.datetime.now()
        start2=int(time.mktime(date.timetuple()))*1000
        copy=subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
        xrd_exit=copy.communicate()[0].split()[-1]
        date=datetime.datetime.now()
        end2=int(time.mktime(date.timetuple()))*1000
        dlSz=os.stat(filename).st_size
        if xrd_exit=='0': #worked second try
            status = 'Success'
            tries=2
            dltime=end2-start2
            payload="{ \"timestamp\" : %d, \"host\" : '%s', \"filename\" : '%s', \"filesize\" : %d, \"download_size\" : %d, \"download_time\" : %d,  \"sitename\" : '%s', \"destination_space\" : %d, \"status\" : '%s', \"xrdexit1\" : %s, \"xrdexit2\" : %d, \"xrdexit3\" : %d, \"tries\" : %d, \"xrdcp_version\" : '%s', \"start1\" : %d, \"end1\" : %d, \"start2\" : %d, \"end2\" : %d, \"start3\" : %d, \"cache\" : '%s'}" % (end2, cache, sourceFile, fileSize, dlSz, dltime, sitename, destSpace, status, xrd_exit, xrdexit2, xrdexit3, tries, xrdcp_version, start1, end1, start2, end2, start3, cache)
            payload=payload.replace("'", '"')
            payload=payload.replace('"{', "'{")
            payload=payload.replace('}"', "}'")
            try:
                p = multiprocessing.Process(target=es_send, name="es_send", args=(payload,))
                p.start()
                time.sleep(5)
                p.terminate()
                p.join()
            except:
                print "Error posting to ES"    
        else: #pull from origin
            print "2nd try failed on %s, pulling from origin" % cache
            cache="root://stash.osgconnect.net"
            command = "python ./timeout.py -t "+str(TIMEOUT)+ " -f "+sourceFile + " -d "+str(DIFF)+" -s "+str(fileSize)+" -x "+str(xrdargs)+" -c "+cache+" -z "+destination
            date=datetime.datetime.now()
            start3=int(time.mktime(date.timetuple()))*1000
            copy=subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
            xrd_exit=copy.communicate()[0].split()[-1]
            date=datetime.datetime.now()
            end3=int(time.mktime(date.timetuple()))*1000
            dlSz=os.stat(filename).st_size
            dltime=end3-start3
            if xrd_exit=='0':
                print "Trunk Success"
                status = 'Trunk Sucess'
                tries=3
            else:
                print "stashcp failed"
                status = 'Timeout'
                tries = 3
            payload="{ \"timestamp\" : %d, \"host\" : '%s', \"filename\" : '%s', \"filesize\" : %d, \"download_size\" : %d, \"download_time\" : %d,  \"sitename\" : '%s', \"destination_space\" : %d, \"status\" : '%s', \"xrdexit1\" : %s, \"xrdexit2\" : %d, \"xrdexit3\" : %d, \"tries\" : %d, \"xrdcp_version\" : '%s', \"start1\" : %d, \"end1\" : %d, \"start2\" : %d, \"end2\" : %d, \"start3\" : %d, \"cache\" : '%s'}" % (end3, cache, sourceFile, fileSize, dlSz, dltime, sitename, destSpace, status, xrd_exit, xrdexit2, xrdexit3, tries, xrdcp_version, start1, end1, start2, end2, start3, cache)
            payload=payload.replace("'", '"')
            payload=payload.replace('"{', "'{")
            payload=payload.replace('}"', "}'")
            try:
                p = multiprocessing.Process(target=es_send, name="es_send", args=(payload,))
                p.start()
                time.sleep(5)
                p.terminate()
                p.join()
            except:
                print "Error posting to ES"

def dostashcpdirectory(sourceDir=source, destination=destination):
    sourceItems = subprocess.Popen(["xrdfs", "root://stash.osgconnect.net", "ls", sourceDir], stdout=subprocess.PIPE).communicate()[0].split()
    for file in sourceItems:
        command2 = 'xrdfs root://stash.osgconnect.net stat '+ file + ' | grep "IsDir" | wc -l'
        isdir=subprocess.Popen([command2],stdout=subprocess.PIPE,shell=True).communicate()[0].split()[0]
        if isdir!='0':
            print 'Caching directory'
            dostashcpdirectory(sourceDir=file)
        else:
            print 'Caching file'
            doStashCpSingle(sourceFile=file)


def es_send(payload):
    url = "http://uct2-collectd.mwt2.org:9951"
    payload = payload
    try:
        req = urllib2.Request(url, payload, {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
    except:
        print "Error posting to ES"


if not args.recursive:
    doStashCpSingle()
else:
    dostashcpdirectory()
