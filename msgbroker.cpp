#include <iostream>
#include <fstream>
#include <string>
#include <cstring>
#include <cstdio>
#include <unistd.h>
#include <cstdlib>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <vector>
#include <unordered_map>
using namespace std;
struct fifopair{
    char* filename;
    int fd;
};
fifopair fifos[4] = {
    {".cfg_fifo"},
    {".getter_fifo"},
    {".submit_fifo"},
    {".ui_fifo"}
};
char* copyCStr(const char* input){
    char* output = (char*) malloc(1024);
    strcpy(output, input);
    return output;
}
vector<char*>* split_string(char* istr){
    char* strptr = istr;
    vector<char*>* string_segments = new vector<char*>;
    strptr = strtok(istr, " \n\t");
    do{
        string_segments->push_back(strptr);
    }while(strptr = strtok(0, " \n\t"));
    return string_segments;
}
void answer_fifo(int& fd, char* filename, unordered_map<string, string>* config_table){

    char* buffer = (char*) malloc(1024);
    memset(buffer, 0, 1024);
    
    int c = read(fd, buffer, 1023);

    
    if(c <= 0) return;
    char* origStr = copyCStr(buffer); // save the original string for forwarding
                                      // since strtok() modifies it
    vector<char*>* string_segments = split_string(buffer);

    if(string_segments->size() == 0) return;

    if(!strcmp(string_segments->at(0), "config") && string_segments->size() >= 2){
        
        if(!strcmp(filename, fifos[0].filename)){
            // don't create a loop between here and the config microservice
            free(origStr);
            free(buffer);
            return;
        }
        // forward the config message to the config fifo/microservice
        close(fifos[0].fd);
        // reopen the config fifo for writing (they are open read-only by default)
        fifos[0].fd = open(fifos[0].filename, O_WRONLY); 
        cout << "[msgbroker] Sending " << origStr << " to .cfg_fifo" << endl;
        write(fifos[0].fd, origStr, strlen(origStr));
        close(fifos[0].fd);

        // re-open fifo for reading (expected state at the start of the function call)
        fifos[0].fd = open(fifos[0].filename, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
        
        if(!strcmp(string_segments->at(1), "get")){ // set does not produce a response
            sleep(1); // wait for configsvc to respond
            memset(buffer, 0, 1024); // clear the buffer
            int c = read(fifos[0].fd, buffer, 1023); // config service fifo
            if(c <= 0) return;

            
            // re-open requesting fifo for a response 
            close(fd);
            fd = open(filename, O_WRONLY);
            // For the video demo. The content of the response may be confidential (API key, etc),
            // so that will not be printed out.
            cout << "[msgbroker] Forwarding response from .cfg_fifo to " << filename << endl;
            write(fd, buffer, strlen(buffer));
            close(fd);
            fd = open(filename, O_RDONLY | O_NONBLOCK | O_CLOEXEC);

        }
    }
    else if(!strcmp(string_segments->at(0), "submit") && string_segments->size() == 4){
        pid_t svcpid = fork();

        if(svcpid == 0){
            //int nullFD = open("/dev/null", O_WRONLY);
            //dup2(nullFD, 1);
            char* execargs[] = {"submit.py", "-c", string_segments->at(1), "-a", string_segments->at(2), string_segments->at(3), 0};
            execvp("submit.py", execargs);
            free(buffer);
            delete string_segments;
            exit(2);
        }
    }
    else if(!strcmp(string_segments->at(0), "get")){
        if(!strcmp(string_segments->at(1), "courses")){
            char* execargs[] = {"get_items.py", "-C", 0, 0, 0, 0, 0};
            switch(string_segments->size()){
                case 2:
                    break;
                case 3:
                    execargs[2] = "-l";
                    execargs[3] = string_segments->at(2);
                    break;
                default:
                    execargs[2] = "-l";
                    execargs[3] = string_segments->at(2);
                    execargs[4] = "-o";
                    execargs[5] = string_segments->at(3);
                    break;
            }
            pid_t svcpid = fork();
            if(svcpid == 0){
                int csvfd = open("output.tsv", O_WRONLY | O_TRUNC | O_CREAT, 0600);
                dup2(csvfd, 1);
                
                
                execvp("get_items.py", execargs);
                free(buffer);
                delete string_segments;
                exit(2);
            }


        }
        else if(!strcmp(string_segments->at(1), "assignments") && string_segments->size() >= 3){
            char* execargs[] = {"get_items.py", "-c", string_segments->at(2), "-A", 0, 0, 0, 0, 0};
            switch(string_segments->size()){
                case 3:
                    break;
                case 4:
                    execargs[4] = "-l";
                    execargs[5] = string_segments->at(3);
                    break;
                default:
                    execargs[4] = "-l";
                    execargs[5] = string_segments->at(3);
                    execargs[6] = "-o";
                    execargs[7] = string_segments->at(4);
                    break;
            }
            pid_t svcpid = fork();
            if(svcpid == 0){
                int csvfd = open("output.tsv", O_WRONLY | O_TRUNC | O_CREAT, 0600);
                dup2(csvfd, 1);
                
                execvp("get_items.py", execargs);
                free(buffer);
                delete string_segments;
                exit(2);
            }


        }

        

        
    }

    free(buffer);
    delete string_segments;
    return;
}
unordered_map<string, string>* load_config(){
    unordered_map<string, string>* config_table = new unordered_map<string, string>;
    ifstream configFile;
    configFile.open("canvas.cfg", ios::in);
    string key_str, value_str;
    while(!configFile.eof()){
        configFile >> key_str;
        configFile >> value_str;
        //cout << "Added to config: " << key_str <<" - " << value_str << endl;
        config_table->insert({key_str, value_str});
    }
    return config_table;
}
int main(){
    unordered_map<string, string>* config_table = load_config();

    // char* submitfifo_fn = ".submit_fifo";
    // char* getterfifo_fn = ".getter_fifo";
    // char* ui_fn = ".ui_fifo"; 
    // char* config_fn = ".config_fifo";
    char* input_buf = (char*) malloc(1024);
    int svcstat = 0;
    
    for(int i = 0; i < (sizeof(fifos) / sizeof(fifopair)); i++){
        fifos[i].fd = open(fifos[i].filename, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    }

    while(1){
        for(int i = 0; i < (sizeof(fifos) / sizeof(fifopair)); i++){
            answer_fifo(fifos[i].fd, fifos[i].filename, config_table);
        }
        waitpid(-1, &svcstat, WNOHANG);
        sleep(1);
    }
    return 0;
}
