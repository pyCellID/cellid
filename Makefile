# Makefile de cellid
#
#   make          compila el programa ./cell
#   make test     compila y corre los tests
#   make clean    borra lo compilado
#
CC      ?= gcc
CFLAGS  ?= -O2 -Wall -Wno-unused-variable -Wno-unused-but-set-variable
LDLIBS   = -ltiff -lz -lm

SRC  = $(wildcard src/*.c)
OBJ  = $(SRC:.c=.o)

cell: $(OBJ)
	$(CC) $(CFLAGS) -o $@ $(OBJ) $(LDLIBS)

src/%.o: src/%.c
	$(CC) $(CFLAGS) -c -o $@ $<

test: cell
	./tests/test_smoke.sh

# Ejercicios de C (no forman parte de los tests del CI)
ejercicio1:
	$(CC) -Wall -Wextra -g -o ejercicios/01_vecinos/test_vecinos \
	    ejercicios/01_vecinos/test_vecinos.c ejercicios/01_vecinos/vecinos.c \
	    ejercicios/01_vecinos/original.c
	./ejercicios/01_vecinos/test_vecinos

clean:
	rm -f cell src/*.o ejercicios/*/test_vecinos
	rm -rf tests/salida

.PHONY: test clean ejercicio1
