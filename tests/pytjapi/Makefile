TARGET  = libtjapi
CC 	= gcc

all : $(TARGET) 

$(TARGET) : tjapi.c
	$(CC) -Wall -c -fPIC tjapi.c -o tjapi.o
	$(CC) -shared -fPIC -Wl,-soname,$(TARGET).so -o $(TARGET).so tjapi.o -lc
clean:
	rm -rf tjapi.o
	rm -rf $(TARGET).so
