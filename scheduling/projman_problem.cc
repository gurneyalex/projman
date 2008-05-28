
#include "projman_problem.hh"


ProjmanProblem::ProjmanProblem(uint_t _maxdur):
    icl(ICL_DEF),
    c_d(Search::Config::c_d),
    a_d(Search::Config::a_d),
    solutions(2000),
    fails(-1),
    time(100),
    verbosity(0),
    max_duration(_maxdur),
    first_day(0),
    convexity(false)
{
}

void ProjmanProblem::set_max_nb_solutions( int nb )
{
    solutions = nb;
}

void ProjmanProblem::set_time( int _time )
{
    time=_time;
}

int ProjmanProblem::get_number_of_solutions() const
{
    return projman_solutions.size();
}

ProjmanSolution ProjmanProblem::get_solution( int k ) const
{
    return projman_solutions[k];
}

void ProjmanProblem::set_convexity( bool v )
{
    convexity = v;
}

void ProjmanProblem::set_verbosity( int level )
{
    verbosity = level;
}

void ProjmanProblem::set_first_day( uint_t d )
{
    if (d>=max_duration) {
	throw std::out_of_range("Day number out of range");
    }
    first_day = d;
}

task_t::task_t( std::string task_id, load_type_t lt, int _load,
		uint_t _range_low, uint_t _range_high, bool _can_interrupt ):
    tid(task_id), load_type(lt), load(_load),
    range_low(_range_low), cmp_type_low(0),
    range_high(_range_high), cmp_type_high(0),
    convex(true), can_interrupt(_can_interrupt)
{
}


uint_t ProjmanProblem::add_task( std::string task_name, load_type_t load_type, int load, bool can_interrupt )
{
    uint_t task_id;
    tasks.push_back( task_t( task_name, load_type, load, 0, max_duration, can_interrupt ) );
    task_id = tasks.size()-1;
    if (load_type==TASK_MILESTONE) {
	milestones.push_back( task_id );
	tasks[task_id].milestone = milestones.size()-1;
    }
    return task_id;
}

void ProjmanProblem::set_task_range( uint_t task_id, uint_t range_low, uint_t range_high,
				     int cmp_type_low, int cmp_type_high )
{
    if (task_id>=tasks.size()) {
	throw std::out_of_range("Task number out of range");
    }
    task_t&  task = tasks[task_id];
    task.range_low = range_low;
    task.range_high = range_high;
    task.cmp_type_low = cmp_type_low;
    task.cmp_type_high = cmp_type_high;
}

resource_t::resource_t( std::string res_id ):rid(res_id)
{
}

uint_t ProjmanProblem::add_worker( std::string worker_name )
{
    resources.push_back( resource_t( worker_name ) );
    return resources.size()-1;
}

void ProjmanProblem::add_not_working_day( uint_t worker, uint_t day )
{
    if (worker>=resources.size()) {
	throw std::out_of_range("Resource number out of range");
    }
    resource_t& res = resources[worker];
    res.not_working.push_back( day );
}

int ProjmanProblem::add_resource_to_task( uint_t task_id, uint_t res_id )
{
    if (res_id>=resources.size()) {
	throw std::out_of_range("Resource number out of range");
    }
    if (task_id>=tasks.size()) {
	throw std::out_of_range("Task number out of range");
    }
    if (tasks[task_id].load_type==TASK_MILESTONE) {
	throw std::runtime_error("Milestones don't have resources");
    }
    res_tasks.push_back( res_task_t( task_id, res_id) );
    uint_t pseudo_id = res_tasks.size()-1;
    // do some bookeeping:
    tasks[task_id].resources.push_back( res_id );
    tasks[task_id].res_tasks_id.push_back( pseudo_id );

    resources[res_id].tasks.push_back( task_id );
    resources[res_id].res_tasks_id.push_back( pseudo_id );

    return pseudo_id;
}

IntSet ProjmanProblem::get_not_working( uint_t res ) const
{
    if (res>=resources.size()) {
	throw std::out_of_range("Resource number out of range");
    }
    const std::vector<uint_t>& nw = resources[res].not_working;
    int values[nw.size()];
    copy( nw.begin(), nw.end(), &values[0] );
    return IntSet( values, nw.size() );
}

void ProjmanProblem::add_task_constraint( constraint_type_t type, uint_t ti, uint_t tj )
{
    if (ti>=tasks.size()||tj>=tasks.size()) {
	throw std::out_of_range("Task number out of range");
    }
    task_constraints.push_back( task_constraint_t( type, ti, tj ) );
}
