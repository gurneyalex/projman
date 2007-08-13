
#include "projman_problem.hh"



ProjmanProblem::ProjmanProblem(int _ntasks, int _nres, int _maxdur):
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
    convexity(false),
    first_day(0)
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

int ProjmanProblem::alloc( int task, int res ) {
    int k = allocations.size();
    allocations.push_back( int_pair_t( task, res ) );
    return k;
}

void ProjmanProblem::add_task_constraint( constraint_type_t type, int ti, int tj )
{
    check_task(ti);
    check_task(tj);
    task_constraints.push_back( task_constraint_t( type, ti, tj ) );
}

void ProjmanProblem::set_time( int _time )
{
    time=_time;
}

void ProjmanProblem::add_not_working_days( int res, int days[], int ndays )
{
    not_working[res].insert( not_working[res].end(), &days[0], &days[ndays] );
}

void ProjmanProblem::add_not_working_day( int res, int day )
{
    not_working[res].push_back( day );
}

void ProjmanProblem::set_duration( int real_task_id, int dur )
{
    check_task(real_task_id);
    durations[real_task_id] = dur;
    if (dur==0) {
	milestones[real_task_id] = n_milestones;
	n_milestones++;
    }
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

void ProjmanProblem::check_task( int t )
{
    if (t<0 || t>=ntasks) {
	throw std::out_of_range("task number out of range");
    }
}
void ProjmanProblem::set_first_day( int d )
{
    if (d<0 || d>=max_duration) {
	throw std::out_of_range("Day number out of range");
    }
    first_day = d;
}
void ProjmanProblem::set_name( int t, std::string name )
{
    check_task( t );
    real_task_names[t] = name;
}

void ProjmanProblem::set_low( int real_task_id, int low )
{
    check_task(real_task_id);
    task_low[real_task_id] = low;
}
void ProjmanProblem::set_high( int real_task_id, int high )
{
    check_task(real_task_id);
    task_high[real_task_id] = high;
}



task_t::task_t( std::string task_id, load_type_t lt, int _load,
		uint_t _range_low, uint_t _range_high ):
    tid(task_id), load_type(lt), load(_load),
    range_low(_range_low), cmp_type_low(0),
    range_high(_range_high), cmp_type_high(0),
    convex(true)
{
}


uint_t ProjmanProblem::add_task( std::string task_id, load_type_t load_type, int load )
{
    tasks.push_back( task_t( task_id, load_type, load, 0, max_duration ) );
    return tasks.size()-1;
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

uint_t ProjmanProblem::add_worker( std::string worker_id )
{
    resources.push_back( resource_t( worker_id ) );
    return resources.size()-1;
}

void ProjmanProblem::append_not_working_day( uint_t worker, uint_t day )
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
    tasks[task_id].resources.push_back( res_id );
    resources[res_id].tasks.push_back( task_id );
}
