
LDFLAGS=`pkg-config --libs gecode gecode-minimodel gecode-search` -lpython2.4 -lboost_python-mt
CXXFLAGS=`pkg-config --cflags gecode gecode-minimodel gecode-search` -I/usr/include/python2.4 -fPIC -g -O0

all: gcsp.so

sample: sample.o projman_gecode.o timer.o
	g++ -o sample `pkg-config --libs --cflags gecode gecode-minimodel gecode-search` -g sample.o timer.o projman_gecode.o


gcsp.so: projman_gecode.o timer.o gcspmodule.o projman_problem.o
	g++  $(LDFLAGS) --shared -o gcsp.so -g gcspmodule.o timer.o projman_gecode.o projman_problem.o

clean:
	rm *.o *.so

projman_gecode.o gcspmodule.o: projman_gecode.hh

