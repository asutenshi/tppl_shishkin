average: main.o
	ld -o average main.o

main.o: main.asm
	nasm -f elf64 -o main.o main.asm

run: average
	./average data.txt

clean:
	rm -f average main.o

.PHONY: run clean
