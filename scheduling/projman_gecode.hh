/* projman_gecode.hh

problem definition for projman solver

*/

#ifndef _PROJMAN_GECODE_
#define _PROJMAN_GECODE_

#include <vector>
#include <stdexcept>
#include "gecode/set.hh"
#include "gecode/kernel.hh"
#include "gecode/int.hh"
#include "gecode/search.hh"

using namespace Gecode;

typedef std::pair<int,int> int_pair_t;
typedef std::vector<int>::const_iterator int_iter;
typedef std::vector<int_pair_t>::const_iterator alloc_iter;

class ProjmanSolution {
public:
    ProjmanSolution( int ntasks, int max_duration, int nmilestones ) {
	for(int i=0;i<ntasks;++i) {
	    task_days.push_back( std::vector<bool>( max_duration ) );
	}
	for(int i=0;i<nmilestones;++i) {
	    milestones.push_back( 0 );
	}
    }
    int get_ntasks() const {
	return task_days.size();
    }
    int get_duration() const {
	return task_days.front().size();
    }
    int get_nmilestones() const {
	return milestones.size();
    }
    int get_milestone(int k) {
	return milestones[k];
    }
    bool isworking( int task, int day ) const {
	return task_days[task][day];
    }
    std::vector< std::vector<bool> > task_days;
    std::vector<int> milestones;
};

class ProjmanProblem {
public:
    int ntasks;  // real tasks
    int nallocations;
    int max_resources;
    int max_duration;
    int n_milestones;
    int verbosity;
    bool convexity;
    std::vector<ProjmanSolution> projman_solutions;
    int get_number_of_solutions() const {
	return projman_solutions.size();
    }
    ProjmanSolution get_solution( int k ) const {
	return projman_solutions[k];
    }

    void set_convexity( bool v ) { convexity = v; }
    void set_verbosity( int level ) { verbosity = level; }
    std::vector<int> durations;  // duration of 0 means it's a milestone
    std::vector<std::string> real_task_names;
    std::vector<int> milestones;  // task_id -> milestone_id mapping or -1 if n/a
    std::vector<int> task_low;   // starting date
    std::vector<int> task_high;  // ending date
    std::vector<int_pair_t> allocations;  // task / res pairs
    
    std::vector<int_pair_t> begin_after_end;
    std::vector<int_pair_t> end_after_end;
    std::vector<int_pair_t> begin_after_begin;
    std::vector<int_pair_t> end_after_begin;

    std::vector< std::vector<int> > not_working; // not working days per resources

    IntSet get_not_working( int res ) const;

    void check_task( int t ) {
	if (t<0 || t>=ntasks) {
	    throw std::out_of_range("task number out of range");
	}
    }
    void set_name( int t, std::string name ) {
	check_task( t );
	real_task_names[t] = name;
    }

    void set_low( int real_task_id, int low ) {
	check_task(real_task_id);
	task_low[real_task_id] = low;
    }
    void set_high( int real_task_id, int high ) {
	check_task(real_task_id);
	task_high[real_task_id] = high;
    }

    // options
    IntConLevel  icl;        ///< integer consistency level
    unsigned int c_d;        ///< recomputation copy distance
    unsigned int a_d;        ///< recomputation adaption distance
    unsigned int solutions;  ///< how many solutions (0 == all)
    int          fails;      ///< number of fails before stopping search
    int          time;       ///< allowed time before stopping search
    void set_time( int _time ) { time=_time; }

    void add_not_working_days( int res, int days[], int ndays ) {
	not_working[res].insert( not_working[res].end(), &days[0], &days[ndays] ); }
    void add_not_working_day( int res, int day ) { not_working[res].push_back( day ); }
    void set_duration( int real_task_id, int dur ) {
	check_task(real_task_id);
	durations[real_task_id] = dur;
	if (dur==0) {
	    milestones[real_task_id] = n_milestones;
	    n_milestones++;
	}
    }

    ProjmanProblem(int _ntasks, int _nres, int _maxdur):
	icl(ICL_DEF),
	c_d(Search::Config::c_d),
	a_d(Search::Config::a_d),
	time(100),
	fails(-1),
	solutions(2000),
	ntasks(_ntasks),
	max_resources(_nres),
	max_duration(_maxdur),
	n_milestones(0),
	verbosity(0),
	convexity(false)
    {
	for(int i=0;i<ntasks;++i) {
	    durations.push_back( 0 );
	    real_task_names.push_back( std::string() );
	    milestones.push_back( -1 );
	    task_low.push_back( 0 );
	    task_high.push_back( max_duration );
	}
	for(int i=0;i<_nres;++i) {
	    not_working.push_back( std::vector<int>(0) );
	}
    }

    int alloc( int task, int res ) {
	int k = allocations.size();
	allocations.push_back( int_pair_t( task, res ) );
	return k;
    }
    void add_begin_after_end( int ti, int tj ) {
	check_task(ti);
	check_task(tj);
	begin_after_end.push_back( int_pair_t( ti, tj ) );
    }
    void add_end_after_end( int ti, int tj ) {
	check_task(ti);
	check_task(tj);
	end_after_end.push_back( int_pair_t( ti, tj ) );
    }
    void add_begin_after_begin( int ti, int tj ) {
	check_task(ti);
	check_task(tj);
	begin_after_begin.push_back( int_pair_t( ti, tj ) );
    }
    void add_end_after_begin( int ti, int tj ) {
	check_task(ti);
	check_task(tj);
	end_after_begin.push_back( int_pair_t( ti, tj ) );
    }
};

enum {
    BEGIN_AFTER_BEGIN,
    BEGIN_AFTER_END,
    END_AFTER_END,
    END_AFTER_BEGIN
};

class ProjmanSolver : public Space {
protected:
    /// Variables
    SetVarArray tasks;      // days the pseudo-task is scheduled
    IntVar last_day;
    IntVarArray milestones;
public:
    /// The actual problem
    ProjmanSolver(const ProjmanProblem& pb);
    template <template<class> class Engine>
    static void run( ProjmanProblem& pb, Search::Stop* stop );
    /// Additionnal constrain for Branch And Bound
    void constrain(Space* s);
    /// Constructor for cloning \a s
    ProjmanSolver(bool share, ProjmanSolver& s);
    /// Perform copying during cloning
    virtual Space* copy(bool share);
    virtual void print(ProjmanProblem& pb);
    virtual void debug(const ProjmanProblem& pb, std::string s, SetVarArray& _tasks);

protected:
    void register_order( const ProjmanProblem& pb, SetVarArray& real_tasks,
			 int type, const std::vector< int_pair_t >& pairs );
};


#endif
