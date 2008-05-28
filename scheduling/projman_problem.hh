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

struct res_task_t {
    res_task_t( uint_t _task_id, uint_t _res_id):task_id(_task_id),
							      res_id(_res_id){}
    uint_t task_id;
    uint_t res_id;
};
struct task_constraint_t {
    task_constraint_t( constraint_type_t t, int ti, int tj):
	type(t), task0(ti), task1(tj) {}
    constraint_type_t  type;
    uint_t   task0;
    uint_t   task1;
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
    task_t( std::string tid, load_type_t lt, int _load, uint_t _range_low, uint_t _range_high, bool _can_interrupt );
    std::string tid;
    load_type_t load_type;
    int         load; // workload, whatever it means depending on load_type
    // date constraints on the task
    int         range_low;
    int         cmp_type_low; // whether <= or == >
    int         range_high;
    int         cmp_type_high;
    bool        convex;
    bool        can_interrupt; // Whether this task can interrupt other 'convex' tasks
    
    std::vector<uint_t> resources; // resources allocated to this task
    std::vector<uint_t> res_tasks_id; // res_tasks id associated with the resource
    uint_t milestone; // id of the milestone *if* this task is a milestone otherwise undefined
};

struct resource_t {
    resource_t( std::string res_id );
    std::string rid;
    std::vector<uint_t> not_working; // not working days for this resource
    
    // bookeeping : tasks this resource is working on
    std::vector<uint_t> tasks;
    std::vector<uint_t> res_tasks_id; // res_tasks id associated with the task
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
    int verbosity;
    
    // problem definition
    uint_t max_duration;
    uint_t first_day; // the first worked day (usually 0)
    bool convexity;

    // solutions
    std::vector<ProjmanSolution> projman_solutions;

    // accessors
    ProjmanProblem(uint_t _maxdur);
    IntSet get_not_working( uint_t res ) const;
    int get_number_of_solutions() const;
    ProjmanSolution get_solution( int k ) const;
    void set_convexity( bool v );
    void set_verbosity( int level );
    void set_first_day( uint_t d );
    void set_time( int _time );
    void set_max_nb_solutions( int nb );
    
    // new interface:
    std::vector< task_t > tasks;
    std::vector< resource_t > resources;
    std::vector<task_constraint_t> task_constraints;
    std::vector< res_task_t > res_tasks; //bookeeping only
    std::vector< uint_t > milestones; // mapping milestone to task_id

    uint_t add_task( std::string task_name, load_type_t load_type, int load, bool can_interrupt );
    void set_task_range( uint_t task_id, uint_t range_low, uint_t range_high,
			 int cmp_type_low, int cmp_type_high );
    uint_t add_worker( std::string worker_name );
    void add_not_working_day( uint_t worker, uint_t day );
    int add_resource_to_task( uint_t task_id, uint_t res_id );
    void add_task_constraint( constraint_type_t t, uint_t ti, uint_t tj );

};


#endif
