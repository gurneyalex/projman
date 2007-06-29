/* projman_gecode.hh

problem definition for projman solver

*/

#ifndef _PROJMAN_GECODE_
#define _PROJMAN_GECODE_

#include <vector>
#include "gecode/set.hh"
#include "gecode/kernel.hh"
#include "gecode/int.hh"
#include "gecode/search.hh"

using namespace Gecode;

typedef std::pair<int,int> int_pair_t;
typedef std::vector<int>::const_iterator int_iter;
typedef std::vector<int_pair_t>::const_iterator alloc_iter;

class ProjmanProblem {
public:
    int ntasks;  // real tasks
    int nallocations;
    int max_resources;
    int max_duration;

    std::vector<int> durations;
    std::vector<int> task_low;   // starting date
    std::vector<int> task_high;  // ending date
    std::vector<int_pair_t> allocations;  // task / res pairs
    
    std::vector<int_pair_t> begin_after_end;
    std::vector<int_pair_t> end_after_end;
    std::vector<int_pair_t> begin_after_begin;
    std::vector<int_pair_t> end_after_begin;

    std::vector< std::vector<int> > not_working; // not working days per resources

    IntSet get_not_working( int res ) const;

    void set_low( int pseudo_task_id, int low ) { task_low[pseudo_task_id] = low; }
    void set_high( int pseudo_task_id, int high ) { task_high[pseudo_task_id] = high; }

    // options
    IntConLevel  icl;        ///< integer consistency level
    unsigned int c_d;        ///< recomputation copy distance
    unsigned int a_d;        ///< recomputation adaption distance
    unsigned int solutions;  ///< how many solutions (0 == all)
    int          fails;      ///< number of fails before stopping search
    int          time;       ///< allowed time before stopping search

    void add_not_working_days( int res, int days[], int ndays ) {
	not_working[res].insert( not_working[res].end(), &days[0], &days[ndays] ); }
    void add_not_working_day( int res, int day ) { not_working[res].push_back( day ); }
    void set_duration( int real_task, int dur ) { durations[real_task] = dur; }

    ProjmanProblem(int _ntasks, int _nres, int _maxdur):
	icl(ICL_DEF),
	c_d(Search::Config::c_d),
	a_d(Search::Config::a_d),
	time(-1),
	fails(-1),
	solutions(2000),
	ntasks(_ntasks),
	max_resources(_nres),
	max_duration(_maxdur)
    {
	for(int i=0;i<ntasks;++i) {
	    durations.push_back( 0 );
	}
	for(int i=0;i<_nres;++i) {
	    not_working.push_back( std::vector<int>(0) );
	}
    }

    int alloc( int task, int res ) {
	int k = allocations.size();
	allocations.push_back( int_pair_t( task, res ) );
	task_low.push_back( 0 );
	task_high.push_back( max_duration );
	return k;
    }
    void add_begin_after_end( int ti, int tj ) { begin_after_end.push_back( int_pair_t( ti, tj ) ); }
    void add_end_after_end( int ti, int tj ) { end_after_end.push_back( int_pair_t( ti, tj ) ); }
    void add_begin_after_begin( int ti, int tj ) { begin_after_begin.push_back( int_pair_t( ti, tj ) ); }
    void add_end_after_begin( int ti, int tj ) { end_after_begin.push_back( int_pair_t( ti, tj ) ); }
};



class ProjmanSolver : public Space {
protected:
    /// Variables
    SetVarArray tasks;      // days the (pseudo)task is scheduled
    IntVar last_day;
public:
    /// The actual problem
    ProjmanSolver(const ProjmanProblem& pb);
    template <template<class> class Engine>
    static void run( const ProjmanProblem& pb );
    /// Additionnal constrain for Branch And Bound
    void constrain(Space* s);
    /// Constructor for cloning \a s
    ProjmanSolver(bool share, ProjmanSolver& s);
    /// Perform copying during cloning
    virtual Space* copy(bool share);
    virtual void print(const ProjmanProblem& pb);
};


#endif
