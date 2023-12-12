#!/usr/bin/python3
import sys
import os
import signal
import time
def configWizard():
    if not os.path.exists("canvas.cfg") or (len(sys.argv) > 1 and sys.argv[1] == "-c"):
        if os.path.exists("canvas.cfg"):
            r = input("Are you sure you want to reset the configuration? (Y / N) > ")
            if len(r) > 0 and r[0].upper() == "Y":
                os.remove("canvas.cfg")
            else:
                exit()
        open("canvascfg", "x").close() # create a new cfg file
        
        cfgSvcPid = os.fork()
        if cfgSvcPid == -1:
            raise OSError("Cannot fork the process")
        elif cfgSvcPid == 0:
            os.execvp("config.py", ("config.py",))

        cfgFifo = os.open(".cfgfifo", os.O_WRONLY, 0o600)
        print("Enter the URL to your Canvas instance, for example https://canvas.instructure.com")
        r = input("> ")
        os.write(cfgFifo, str.encode("config set api_url " + (r if r[-1] != "/" else r[:-1])))
        
        print("Now, on the Canvas webpage, go to Account > Settings > New Access Token (under Approved Integrations),")
        r = input("and paste it here > ")
        os.write(cfgFifo, str.encode("config set api_key " + r))
        os.close(cfgFifo)
        print("Configuration complete. Launching the program...")
        os.kill(cfgSvcPid, signal.SIGTERM)
        return
def startProg():
    msgbroker_pid = os.fork()
    if msgbroker_pid == -1:
        raise OSError("Could not fork the process")
    elif msgbroker_pid == 0:
        os.execvp("msgbroker", ("msgbroker",))
    cfgSvcWatcherPid = os.fork()
    if cfgSvcWatcherPid == -1:
        raise OSError("Could not fork the process")
    elif cfgSvcWatcherPid == 0:
        while 1:
            os.system("config.py")
    print("Services are starting up. Please wait...")

    time.sleep(3)
    ui_pid = os.fork()
    if ui_pid == -1:
        raise OSError("Could not fork the process")
    elif ui_pid == 0:
        os.execvp("ui.py", ("ui.py",))
    os.waitpid(ui_pid, 0)
    os.kill(msgbroker_pid, signal.SIGTERM)
    os.kill(cfgSvcWatcherPid, signal.SIGTERM)
    os.waitpid(msgbroker_pid, 0)
    os.waitpid(cfgSvcWatcherPid, 0)
    return
configWizard()
startProg()

    
