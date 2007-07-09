/*
 *  Main authors:
 *     Guido Tack <tack@gecode.org>
 *
 *  Copyright:
 *     Guido Tack, 2006
 *
 *  Last modified:
 *     $Date: 2006-08-03 13:51:17 +0200 (Thu, 03 Aug 2006) $ by $Author: schulte $
 *     $Revision: 3506 $
 *
 *  This file is part of Gecode, the generic constraint
 *  development environment:
 *     http://www.gecode.org
 *
 *  See the file "LICENSE" for information on usage and
 *  redistribution of this file, and for a
 *     DISCLAIMER OF ALL WARRANTIES.
 *
 */

#include "gecode/set.hh"
#include <iostream>
#include <algorithm>
#include "projman_gecode.hh"

using namespace std;

/**
 * \brief %Example: Task scheduling example
 *
 * \ingroup Example
 *

5 Tasks A, B, C, D, E
B begins after A
C begins after A
D begins after A
E begins after B, C, D
two resources 1, 2
A -> 1,2
B -> 1
C -> 1
D -> 1,2
E -> 1,2

 */

const int nholydays = 4;
const int vacances[nholydays][2] = {  // (day, res)
    { 5, 0 },
    { 5, 1 },
    { 6, 0 },
    { 6, 1 }
};



ProjmanProblem* setup( int max_duration )
{
    const int ntasks = 6;
    const int max_resources = 2;
    const int durations[ntasks] = { 2, 4, 2, 2, 2, 3 };
    ProjmanProblem *pb = new ProjmanProblem( ntasks, max_resources, max_duration );
    for( int i=0;i<ntasks;++i ) {
	pb->set_duration( i,  durations[i] );
    }
    int t0 = pb->alloc( 0, 1 );  // real task 0 -> res 1  #0
    int t1 = pb->alloc( 1, 0 );  // real task 1 -> res 0  #1
    int t2 = pb->alloc( 1, 1 );  // real task 1 -> res 1  #2
    int t3 = pb->alloc( 2, 0 );  // real task 2 -> res 0  #3
    int t4 = pb->alloc( 3, 1 );  // real task 3 -> res 1  #4
    int t5 = pb->alloc( 4, 1 );  // real task 4 -> res 1  #5
    int t6 = pb->alloc( 5, 0 );  // real task 4 -> res 1  #5
    int t7 = pb->alloc( 5, 1 );  // real task 4 -> res 1  #5
    pb->add_begin_after_end( t0, t1 );
    pb->add_begin_after_end( t0, t2 );
    pb->add_begin_after_end( t0, t3 );
    pb->add_begin_after_end( t0, t4 );
    pb->add_begin_after_end( t1, t5 );
    pb->add_begin_after_end( t2, t5 );
    pb->add_begin_after_end( t3, t5 );
    pb->add_begin_after_end( t4, t5 );
    pb->add_begin_after_begin( t5, t6 );
    pb->add_begin_after_begin( t5, t7 );
    
    int not_working0[] = {5,6,12,13};
    int not_working1[] = {4,5,6,11,12,13};
    pb->add_not_working_days( 0, not_working0, 4 );
    pb->add_not_working_days( 1, not_working1, 6 );

    return pb;
}

class FailTimeStop : public Search::Stop {
private:
    Search::TimeStop *ts;
    Search::FailStop *fs;
    FailTimeStop(int fails, int time) {
	ts = new Search::TimeStop(time);
	fs = new Search::FailStop(fails);
    }
public:
    bool stop(const Search::Statistics& s) {
	return fs->stop(s) || ts->stop(s);
    }
    /// Create appropriate stop-object
    static Search::Stop* create(int fails, int time) {
	if (fails < 0 && time < 0) return NULL;
	if (fails < 0) return new Search::TimeStop( time);
	if (time  < 0) return new Search::FailStop(fails);
	return new FailTimeStop(fails, time);
    }
};

/** \brief Main-function
 *  \relates ProjmanSolver
 */
int
main(int argc, char** argv) {
    int duration = 20;
    if (argc>1) {
	duration = atoi(argv[1]);
    }
    cout << "Maximum duration:" << duration << endl;

    ProjmanProblem *pb = setup(duration);
    Search::Stop* stop = FailTimeStop::create(pb->fails, pb->time);
    ProjmanSolver::run<BAB>(*pb, stop);
    return 0;
}

// STATISTICS: example-any

