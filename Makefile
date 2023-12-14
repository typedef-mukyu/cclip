CPPC=g++
CC_ARGS=-Wno-write-strings -fpermissive -g

all: msgbroker .cfg_fifo .getter_fifo .submit_fifo .ui_fifo
msgbroker: msgbroker.cpp
	$(CPPC) msgbroker.cpp -o msgbroker $(CC_ARGS)
.cfg_fifo:
	mkfifo .cfg_fifo
.getter_fifo:
	mkfifo .getter_fifo
.submit_fifo:
	mkfifo .submit_fifo
.ui_fifo:
	mkfifo .ui_fifo	
