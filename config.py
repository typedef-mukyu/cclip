#!/usr/bin/python3

#This function creates a dictionary of values from the Canvas config file
def init_cfg_dict():
    f = open("canvas.cfg", "r")
    cfg_dict = {}
    for x in f:
        x = x.strip("\n")
        values = x.split(" ",1)
        if len(values) > 1:
            cfg_dict[values[0]] = values[1]
    f.close()
    return cfg_dict

cfg_dict = init_cfg_dict()
f = open(".cfg_fifo", "r")                      # Open the FIFO to get the user's command
x = f.read()
f.close()
values = x.split(" ", 3)
if values[0] == "config" and len(values) > 2:
    if values[1] == "get":                      # If the command is a get request find the requested value from the dictionary
        f = open(".cfg_fifo", "w")
        if values[2] in cfg_dict:               
            f.write(cfg_dict[values[2]])
        else:
            f.write("\0")                       # If there is no value found in the dictionary, a null value is returned
        f.close()
    if values[1] == "set":                      # If the command is a set request, set the new value to the matching dictionary key
        if len(values) == 3:
            cfg_dict.pop(values[2], None)       # Keys set without a new value are removed from the dictionary
        else:
            cfg_dict[values[2]] = values[3]
        f = open("canvas.cfg", "w")
        i = 0
        for key in cfg_dict:                    # Update the config file so it includes the new value
            i += 1
            print(key, cfg_dict[key], file=f, end=("\n" if i < len(cfg_dict) else ""))
        f.close()




