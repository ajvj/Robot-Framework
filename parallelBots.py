__author__ = 'ajvj'


from Queue import Queue
from threading import Thread
import subprocess
import thread
import time
import Queue
import threading
from robot.running import TestSuite
from robot.api import TestData
from robot import utils
from robot.conf import settings
import os, glob
import sys
import psutil

pybotList=[]
#number bots to execute the test
botList = ["Bot-1", "Bot-2", "Bot-3", "Bot-4", "Bot-5", "Bot-6", "Bot-7", "Bot-8", "Bot-9", "Bot-10"]
processInfo = {}
queueLock = threading.Lock()
workQueue = Queue.Queue(500)
threads = []

groupingStamp = str(int(time.time()))



def getTestCases(suite, userSwitch):
	try:
		#print 'Suite:', suite.source
		for test in suite.testcase_table:            
			pybotList.append('pybot --listener WatchDog:'+groupingStamp+' -d parallel -r none -l none -o '+test.name+'.xml -t '+test.name+' '+userSwitch+' '+suite.source)

		for child in suite.children:
			getTestCases(child, userSwitch)
	except:
		print "Unexpected error:", sys.exc_info()[0]

	return pybotList
	

class TestBot (threading.Thread):
    def __init__(self, botIdentity, botName, jobPool):
        threading.Thread.__init__(self)
        self.botIdentity = botIdentity
        self.botName = botName
        self.jobPool = jobPool
    def run(self):
        print "\nStarting " + self.botName
        process_data(self.botName, self.jobPool)
        print "\nExiting " + self.botName

def do_cmd_operation(cmd):
	p = subprocess.Popen(cmd, stdout = subprocess.PIPE, shell = True)
	print "\n process started : " +str(psutil.Process( p.pid).create_time())	
	(output, err) = p.communicate()
	p_status = p.wait()
	print "\nCommand output : \n", output
	#print "\nCommand exit status/return code : ", p_status

	
def process_data(botName, jobQueue):
    while not exitFlag:
        queueLock.acquire()
        if not workQueue.empty():
            job = jobQueue.get()
            queueLock.release()
            print "\n%s processing %s \n"% (botName, job)
            do_cmd_operation(job)
        else:
            queueLock.release()
        time.sleep(1)

def triggerBots():
    # Create bot to test
    botIdentity = 1
    for testBot in botList:
        thread = TestBot(botIdentity, testBot, workQueue)
        thread.start()
        threads.append(thread)
        botIdentity += 1

    # Wait for the queue to empty
    while not workQueue.empty():
        pass


# splitting parallel tests into blocks
# usage: python parallelBots.py test\suite.txt

testArguments = []
testParam = ''
try:
	for arg in sys.argv:
		testArguments.append(arg)

	srcSuite = testArguments[-1]

	for switch in testArguments[1:-1]:
		testParam = testParam + " " + switch

	suite=TestData(source=srcSuite)

	pybotList = getTestCases(suite, testParam)

	# Prepare the queue
	queueLock.acquire()
	for pybotCmd in pybotList:
		workQueue.put(pybotCmd)
	queueLock.release()

except:
	print "Unexpected error:", sys.exc_info()[0]


# Notifier bot to pick a job
exitFlag = 0

triggerBots()

# Notify bot to exit
exitFlag = 1

# Wait for all the job to complete
for t in threads:
    t.join(240)
    

print "Exiting Main Bot"



 
