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
        cfgFile = os.open("canvas.cfg", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        print("Enter the URL to your Canvas instance, for example https://canvas.instructure.com")
        r = input("> ")
        os.write(cfgFile, str.encode("api_url " + (r if r[-1] != "/" else r[:-1]) + "\n"))
        
        print("Now, on the Canvas webpage, go to Account > Settings > New Access Token (under Approved Integrations),")
        r = input("and paste it here > ")
        os.write(cfgFile, str.encode("api_key " + r))
        os.close(cfgFile)
        print("Configuration complete. Launching the program...")
        
        return
def startProg():
    msgbroker_pid = os.fork()
    if msgbroker_pid == -1:
        raise OSError("Could not fork the process")
    elif msgbroker_pid == 0:
        os.execvp("msgbroker", ("msgbroker",))
    print("Message broker is starting up. Please wait...")
    time.sleep(3)
    ui_pid = os.fork()
    if ui_pid == -1:
        raise OSError("Could not fork the process")
    elif ui_pid == 0:
        os.execvp("ui.py", ("ui.py",))
    os.waitpid(ui_pid, 0)
    os.kill(msgbroker_pid, signal.SIGTERM)
    return
configWizard()
startProg()

    
