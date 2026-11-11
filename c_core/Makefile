
CC = gcc
CFLAGS = -Wall -Wextra -O2
TARGET = food_court_ds_cli
LIB_TARGET = libfoodcourt.so
DLL_TARGET = food_court_ds.dll

SRCS = food_court_ds.c main.c
OBJS = $(SRCS:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJS)

%.o: %.c food_court_ds.h
	$(CC) $(CFLAGS) -c $< -o $@

shared_linux:
	$(CC) $(CFLAGS) -fPIC -shared -o $(LIB_TARGET) food_court_ds.c

shared_windows:
	$(CC) $(CFLAGS) -shared -o $(DLL_TARGET) food_court_ds.c

clean:
	rm -f $(OBJS) $(TARGET) $(LIB_TARGET) $(DLL_TARGET) *.exe

test: $(TARGET)
	./$(TARGET) test

.PHONY: all clean test shared_linux shared_windows
