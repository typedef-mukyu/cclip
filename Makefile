CPPC=g++
CC_ARGS=-Wno-write-strings

all: msgbroker .getter_fifo .submit_fifo .ui_fifo
msgbroker: msgbroker.cpp
	$(CPPC) msgbroker.cpp -o msgbroker $(CC_ARGS)
.getter_fifo:
	mkfifo .getter_fifo
.submit_fifo:
	mkfifo .submit_fifo
.ui_fifo:
	mkfifo .ui_fifo	
