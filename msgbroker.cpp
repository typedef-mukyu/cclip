#include <iostream>
#include <cstring>
#include <cstdio>
#include <unistd.h>
#include <cstdlib>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <vector>
#define CONFIG_FIFO fifos[0]
using namespace std;
struct fifopair{
    char* filename;
    int fd; // C-style file descriptor for each FIFO
};

fifopair fifos[4] = {
    {".cfg_fifo"}, // connects to config.py
    {".getter_fifo"}, // get_items.py
    {".submit_fifo"}, // submit.py
    {".ui_fifo"} // ui.py
};

// Closes and reopens a FIFO in the mode requested with oflags.
void closeAndReopen(fifopair& fifo, int oflags){
    close(fifo.fd);
    fifo.fd = open(fifo.filename, oflags);
}

void sendMsgToFifo(const char* msg, fifopair& fifo = CONFIG_FIFO){
    closeAndReopen(fifo, O_WRONLY); // reopen config fifo for writing (they are read-only initially)
    write(fifo.fd, msg, strlen(msg));
    // re-open fifo for reading (expected state at the start of the function call)
    closeAndReopen(fifo, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
}

// Receives up to length bytes from inFifo, and forwards it to outFifo.
void recvFifoAndFwd(fifopair& outFifo, fifopair& inFifo = CONFIG_FIFO, size_t length = 1024){
    char msg[length] = {0};
    int c = read(inFifo.fd, msg, length - 1); // config service fifo
    if(c <= 0) return;
    closeAndReopen(outFifo, O_WRONLY); // re-open requesting fifo to write back 
    write(outFifo.fd, msg, strlen(msg));
    closeAndReopen(outFifo, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
}

// Launches an on-demand microservice named in args[0] and returns its process ID.
// The get_items service gets its output redirected to output.tsv.
pid_t launchProcess(char** args){
    pid_t svcpid = fork();
    if(svcpid == 0){ // child process
        if(!strcmp(args[0], "get_items.py")){
            int csvfd = open("output.tsv", O_WRONLY | O_TRUNC | O_CREAT, 0600);
            dup2(csvfd, 1); // redirect stdout from get_items service to the tsv file
        }
        execvp(args[0], args);
        exit(2);
    }
    return svcpid;
}

void setUpFifos(){
    for(int i = 0; i < (sizeof(fifos) / sizeof(fifopair)); i++){
        fifos[i].fd = open(fifos[i].filename, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    }
}

// Splits a C-string into a vector of C-strings, splitting at any character in delim.
vector<char*>* splitString(char* istr, const char* delim){
    char* strptr = istr;
    vector<char*>* stringSegments = new vector<char*>;
    strptr = strtok(istr, delim);
    do{
        stringSegments->push_back(strptr);
    }while(strptr = strtok(0, delim));
    return stringSegments;
}

char* copyCStr(const char* input){
    char* output = (char*) malloc((strlen(input) + 1) * sizeof(char));
    strcpy(output, input);
    return output;
}

void setArgValue(char** execArgs, int pos, char* arg, char* value = 0){
    execArgs[pos] = arg;
    if(value) execArgs[pos + 1] = value;
}

void setGetterArgs(vector<char*>* stringSegments, char** execArgs){
    int initialArgs = (!strcmp(stringSegments->at(1), "courses"))? 2 : 3;
    execArgs[1] = (initialArgs == 3)? "-c" : "-C"; // capital C lists courses, lowercase specifies course ID
    if(initialArgs == 3){ // "get", "assignments", and a course ID
        execArgs[2] = stringSegments->at(2); // course ID
        execArgs[3] = "-A";
    }
    if(stringSegments->size() >= initialArgs + 1){ // limit argument for getter program
        setArgValue(execArgs, initialArgs + 2, "-l", stringSegments->at(initialArgs));
    }
    if(stringSegments->size() >= initialArgs + 2){ // offset argument for getter program
        setArgValue(execArgs, initialArgs + 4, "-o", stringSegments->at(initialArgs + 1));
    }
    return;
}

void setSubmitArgs(vector<char*>* stringSegments, char** execArgs){
    setArgValue(execArgs, 1, "-c", stringSegments->at(1)); // course ID
    setArgValue(execArgs, 3, "-a", stringSegments->at(2)); // assignment ID
    setArgValue(execArgs, 5, stringSegments->at(3)); // filename to submit
    
}

void launchSubmitSvc(vector<char*>* stringSegments){
    char* execArgs[9] = {"submit.py", 0};
    setSubmitArgs(stringSegments, execArgs);
    launchProcess(execArgs);
}

void launchGetter(vector<char*>* stringSegments){
    char* execArgs[9] = {"get_items.py", 0};
    if(!strcmp(stringSegments->at(1), "courses") || 
        !strcmp(stringSegments->at(1), "assignments") && stringSegments->size() >= 3){
        setGetterArgs(stringSegments, execArgs);
        launchProcess(execArgs);
    }
}

void routeRequest(fifopair& fifo, vector<char*>* stringSegments, char* origMsg){{
    if(!strcmp(stringSegments->at(0), "config") && strcmp(fifo.filename, CONFIG_FIFO.filename)){
        // forward the config message to the config fifo/microservice
        sendMsgToFifo(origMsg);
        if(!strcmp(stringSegments->at(1), "get")){ // set does not produce a response
            sleep(1);
            recvFifoAndFwd(fifo);
        }
    }
    else if(!strcmp(stringSegments->at(0), "submit") && stringSegments->size() == 4){
        launchSubmitSvc(stringSegments);
    }
    else if(!strcmp(stringSegments->at(0), "get")){
        launchGetter(stringSegments);
    }
}}

void answer_fifo(fifopair& fifo){
    char* msg = (char*) calloc(1024, sizeof(char));
    int c = read(fifo.fd, msg, 1023);
    if(c <= 0) return;
    char* origMsg = copyCStr(msg); // save the original string for forwarding
                                   // since strtok() modifies it
    vector<char*>* stringSegments = splitString(msg, " \n\t");
    if(stringSegments->size() == 0) return;
    routeRequest(fifo, stringSegments, origMsg);
    return;
}

int main(){
    int svcstat = 0;
    setUpFifos(); // opens each FIFO read-only nonblocking, with close-on-exec enabled
    while(1){
        for(int i = 0; i < (sizeof(fifos) / sizeof(fifopair)); i++){
            answer_fifo(fifos[i]);
        }
        waitpid(-1, &svcstat, WNOHANG); // clean up any recently-terminated child processes
        sleep(1);
    }
    return 0;
}
