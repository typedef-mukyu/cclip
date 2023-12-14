#!/usr/bin/python3
import sys
import os
import signal
import time
from msgstrings import msgStrings

# Launches the program at fileName, and returns the PID of the new process.
def launchProcess(fileName: str) -> int:
    newProcessPid = os.fork()
    if newProcessPid == -1:
        raise OSError(msgStrings["ForkNG"])
    elif newProcessPid == 0:
        os.execvp(fileName, (fileName,))
    else:
        return newProcessPid

# If fileName exists, prompt to delete it. If user answers negatively, program exits.
# Otherwise, fileName is deleted if necessary and created.
def promptAndResetFile(fileName: str) -> int:
    if os.path.exists(fileName):
        r = input(msgStrings["CfgResetPrompt"])
        if len(r) > 0 and r[0].upper() == "Y":
            os.remove(fileName)
        else:
            exit()
    open(fileName, "x").close() # create a new cfg file

# This continually runs the configuration service, since that terminates on success.
def cfgSvcWatcher() -> int:
    cfgSvcWatcherPid = os.fork()
    if cfgSvcWatcherPid == -1:
        raise OSError(msgStrings["ForkNG"])
    elif cfgSvcWatcherPid == 0:
        while 1:
            cfgSvcPid = launchProcess("config.py")
            os.waitpid(cfgSvcPid, 0)
    else: 
        return cfgSvcWatcherPid

def cleanUpProcess(targetPid: int) -> None:
    os.kill(targetPid, signal.SIGTERM)
    os.waitpid(targetPid, 0)

def setConfigItem(setting: str, value: str) -> None:
    cfgFifo = os.open(".cfg_fifo", os.O_WRONLY, 0o600)
    os.write(cfgFifo, str.encode("config set " + setting + " " + value))
    os.close(cfgFifo)

def getUrlAndKey() -> None:
    print(msgStrings["CfgURLPrompt"])
    response = input("> ") # strip trailing slash from URL if present in line below    
    setConfigItem("api_url", (response if response[-1] != "/" else response[:-1]))
    print(msgStrings["CfgKeyPrompt"])
    response = input("> ")
    setConfigItem("api_key", response)

def configWizard() -> None:
    promptAndResetFile("canvas.cfg")
    cfgSvcWatcherPid = cfgSvcWatcher()  
    getUrlAndKey()
    print(msgStrings["CfgComplete"])
    cleanUpProcess(cfgSvcWatcherPid)
    return

# Starts all microservices, and returns a dict with each service's PID.
def startProg() -> dict:
    pidList = dict()
    pidList["msgbroker"] = launchProcess("msgbroker") # message broker service
    pidList["cfgSvcWatcher"] = cfgSvcWatcher() # configuration service
    print(msgStrings["SvcStarting"])
    time.sleep(3) # wait for services to start
    pidList["ui"] = launchProcess("ui.py") # start UI service
    return pidList 

def waitAndCleanup(pidList: dict):
    os.waitpid(pidList["ui"], 0) # wait for UI to terminate
    pidList.pop("ui")
    for pid in pidList.values():
        cleanUpProcess(pid)
    os.system("killall -q config.py")

def main():
    # -c requests a configuration reset
    if not os.path.exists("canvas.cfg") or (len(sys.argv) > 1 and sys.argv[1] == "-c"):
        configWizard()
    pidList = startProg()
    waitAndCleanup(pidList)

if __name__ == "__main__":        
    main()


    
