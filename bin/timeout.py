import optparse
import os
import time
import subprocess
import multiprocessing

parser = optparse.OptionParser()
parser.add_option('-t', dest='timeout', type=int)
parser.add_option('-f', dest='filename')
parser.add_option('-d', dest='diff', type=int)
parser.add_option('-s', dest='expSize', type=int)
parser.add_option('-x', dest='xrdebug')
parser.add_option('-c', dest='cache')
parser.add_option('-z', dest='destination')
results,opts = parser.parse_args()

def start_watchdog(xrdcp,timeout=results.timeout,filename=results.filename,diff=results.diff,expSize=results.expSize):
    prevSize=0
    newSize=0
    filename="./"+filename.split("/")[-1]
    while (newSize<expSize):
        time.sleep(timeout)
        if os.path.isfile(filename):
            newSize=os.stat(filename).st_size
            nextSize=prevSize+diff
            if nextSize<expSize:
                wantSize=nextSize
            else:
                wantSize=expSize
            if newSize < wantSize:
                xrdcp.kill()
                newSize=expSize
            else:
                prevSize=os.stat(filename).st_size
        else:
            xrdcp.kill()
            newSize=expSize
print results.xrdebug
filepath=results.cache+":1094//"+ results.filename
if results.xrdebug=="1":
    command="xrdcp -d 2 --nopbar -f " + filepath + " " + results.destination
else:
    command="xrdcp -s -f " + filepath + " " + results.destination

filename="./"+results.filename.split("/")[-1]
if os.path.isfile(filename):
    os.remove(filename)
xrdcp=subprocess.Popen([command ],shell=True,stdout=subprocess.PIPE)
time.sleep(1)
watchdog=multiprocessing.Process(target=start_watchdog,args=[xrdcp])
watchdog.start()

streamdata=xrdcp.communicate()[0]

xrd_exit=xrdcp.returncode

watchdog.terminate()
