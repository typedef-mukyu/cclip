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
    //cout << "Now answering " << filename << endl;
    char* buffer = (char*) malloc(1024);
    memset(buffer, 0, 1024);
    
    int c = read(fd, buffer, 1023);
    //cout << "Read " << c << " bytes from fd " << fd << endl;
    
    if(c <= 0) return;
    
    vector<char*>* string_segments = split_string(buffer);

    if(string_segments->size() == 0) return;
    //else cout << "Size: " << string_segments->size() << " " << "First: " << string_segments->at(0) << endl;
    if(!strcmp(string_segments->at(0), "config") && string_segments->size() == 3){
        if(!strcmp(string_segments->at(1), "get")){
            close(fd);
            fd = open(filename, O_WRONLY);
            try{
                string config_value = string_segments->at(2);
                const char* outPtr = config_table->at(config_value).c_str();
                //printf("Writing %s", outPtr);
                
                write(fd, outPtr, strlen(outPtr));
            }
            catch(...){
                write(fd, "\0", 1);
            }
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
            free(buffer);
            delete string_segments;
            execvp("submit.py", execargs);
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
                int csvfd = open("output.csv", O_WRONLY | O_TRUNC | O_CREAT, 0600);
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
                int csvfd = open("output.csv", O_WRONLY | O_TRUNC | O_CREAT, 0600);
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
    //FILE* submit_fifo;
    char* submitfifo_fn = ".submit_fifo";
    char* getterfifo_fn = ".getter_fifo";
    char* ui_fn = ".ui_fifo"; 
    char* input_buf = (char*) malloc(1024);
    int svcstat = 0;
    // mkfifo("submit_fifo", 0600);
    int submitFD = open(submitfifo_fn, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    int getterFD = open(getterfifo_fn, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    int uiFD = open(ui_fn, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    

    while(1){

        answer_fifo(submitFD, submitfifo_fn, config_table);



        answer_fifo(getterFD, getterfifo_fn, config_table);



        answer_fifo(uiFD, ui_fn, config_table);

        waitpid(-1, &svcstat, WNOHANG);
        sleep(1);
    }
    return 0;
}
