
LDFLAGS=`pkg-config --libs gecode gecode-minimodel gecode-search`
CXXFLAGS=`pkg-config --cflags gecode gecode-minimodel gecode-search` -I/usr/include/python2.4 -fPIC -g -O0

all: sample gcsp.so

sample: sample.o projman_gecode.o timer.o
	g++ -o sample `pkg-config --libs --cflags gecode gecode-minimodel gecode-search` -g sample.o timer.o projman_gecode.o


gcsp.so: projman_gecode.o timer.o gcspmodule.o
	g++  -lpython2.4 -lboost_python --shared -o gcsp.so `pkg-config --libs --cflags gecode gecode-minimodel gecode-search` -g gcspmodule.o timer.o projman_gecode.o

clean:
	rm *.o *.so

projman_gecode.o gcspmodule.o: projman_gecode.hh

