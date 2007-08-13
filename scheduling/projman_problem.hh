/*
   projman_problem.hh

   describes what projman thinks a task scheduling problem is...
*/
#ifndef _PROJMAN_PROBLEM_
#define _PROJMAN_PROBLEM_

#include <vector>
#include <stdexcept>

//#include "gecode/set.hh"
//#include "gecode/kernel.hh"
#include "gecode/int.hh"
#include "gecode/search.hh"

using namespace Gecode;

typedef unsigned int uint_t;
typedef std::pair<int,int> int_pair_t;
typedef std::vector<int>::const_iterator int_iter;
typedef std::vector<int_pair_t>::const_iterator alloc_iter;

enum constraint_type_t {
    BEGIN_AFTER_BEGIN,
    BEGIN_AFTER_END,
    END_AFTER_END,
    END_AFTER_BEGIN
};
struct task_constraint_t {
    task_constraint_t( constraint_type_t t, int ti, int tj):
	type(t), task0(ti), task1(tj) {}
    constraint_type_t  type;
    int   task0;
    int   task1;
};
typedef std::vector<task_constraint_t>::const_iterator const_constraint_iter;

enum load_type_t {
    TASK_SHARED,
    TASK_ONEOF,
    TASK_SAMEFORALL,
    TASK_SPREAD,
    TASK_MILESTONE
};
struct task_t {
    task_t( std::string tid, load_type_t lt, int _load, uint_t _range_low, uint_t _range_high );
    std::string tid;
    load_type_t load_type;
    int         load; // workload, whatever it means depending on load_type
    // date constraints on the task
    int         range_low;
    int         cmp_type_low; // whether <= or == >
    int         range_high;
    int         cmp_type_high;
    bool        convex;
    
    std::vector<uint_t> resources; // resources allocated to this task
};

struct resource_t {
    resource_t( std::string res_id );
    std::string rid;
    std::vector<int> not_working; // not working days for this resource
    
    // bookeeping : tasks this resource is working on
    std::vector<uint_t> tasks;
};

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
    int get_milestone(uint_t k) const {
	if (k>=milestones.size()) {
	    throw std::out_of_range("Milestone number out of range");
	}
	return milestones[k];
    }
    bool isworking( uint_t task, uint_t day ) const {
	if (task>task_days.size()) {
	    throw std::out_of_range("Task number out of range");
	}
	if (day>task_days[task].size()) {
	    throw std::out_of_range("Day number out of range");
	}
	return task_days[task][day];
    }
    std::vector< std::vector<bool> > task_days;
    std::vector<int> milestones;
};

class ProjmanProblem {
public:
    // Gecode Solver options
    IntConLevel  icl;        ///< integer consistency level
    unsigned int c_d;        ///< recomputation copy distance
    unsigned int a_d;        ///< recomputation adaption distance
    unsigned int solutions;  ///< how many solutions (0 == all)
    int          fails;      ///< number of fails before stopping search
    int          time;       ///< allowed time before stopping search
    
    // problem definition
    uint_t ntasks;  // real tasks
    uint_t nallocations;
    uint_t max_resources;
    uint_t max_duration;
    uint_t n_milestones;
    int verbosity;
    int first_day; // the first worked day (usually 0)
    bool convexity;

    std::vector<int> durations;  // duration of 0 means it's a milestone
    std::vector<std::string> real_task_names;
    std::vector<int> milestones;  // task_id -> milestone_id mapping or -1 if n/a
    std::vector<int> task_low;   // starting date
    std::vector<int> task_high;  // ending date
    std::vector<int_pair_t> allocations;  // task / res pairs
    
    std::vector<task_constraint_t> task_constraints;
    std::vector< std::vector<int> > not_working; // not working days per resources

    // solutions
    std::vector<ProjmanSolution> projman_solutions;

    // accessors
    ProjmanProblem(int _ntasks, int _nres, int _maxdur);
    IntSet get_not_working( int res ) const;
    int get_number_of_solutions() const;
    ProjmanSolution get_solution( int k ) const;
    void set_convexity( bool v );
    void set_verbosity( int level );
    void check_task( int t );
    void set_first_day( int d );
    void set_name( int t, std::string name );
    void set_low( int real_task_id, int low );
    void set_high( int real_task_id, int high );
    void set_time( int _time );
    void add_not_working_days( int res, int days[], int ndays );
    void add_not_working_day( int res, int day );
    void set_duration( int real_task_id, int dur );
    int alloc( int task, int res );
    void add_task_constraint( constraint_type_t t, int ti, int tj );

    // new interface:
    std::vector< task_t > tasks;
    std::vector< resource_t > resources;

    uint_t add_task( std::string task_id, load_type_t load_type, int load );
    void set_task_range( uint_t task_id, uint_t range_low, uint_t range_high,
			 int cmp_type_low, int cmp_type_high );
    uint_t add_worker( std::string worker_id );
    void append_not_working_day( uint_t worker, uint_t day );
    int add_resource_to_task( uint_t task_id, uint_t res_id );
};


#endif
