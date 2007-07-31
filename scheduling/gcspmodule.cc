
/* gecode/csp module for projman */

#include <Python.h>
#include <boost/python.hpp>

#include "projman_gecode.hh"
#include "timer.hh"

using namespace boost::python;

class FailTimeStop : public Search::Stop {
private:
    Search::TimeStop *ts;
    Search::FailStop *fs;
public:
    FailTimeStop(int fails, int time):ts(0L),fs(0L) {
	if (time>=0)
	    ts = new Search::TimeStop(time);
	if (fails>=0) {
	    fs = new Search::FailStop(fails);
	}
    }
    bool stop(const Search::Statistics& s) {
	int sigs = PyErr_CheckSignals();
	bool fs_stop = false;
	bool ts_stop = false;
	if (fs) {
	    fs_stop = fs->stop(s);
	}
	if (ts) {
	    ts_stop = ts->stop(s);
	}
	return sigs || fs_stop || ts_stop;
    }
    /// Create appropriate stop-object
    static Search::Stop* create(int fails, int time) {
	return new FailTimeStop(fails, time);
    }
};

void run_solve( ProjmanProblem& pb ) {
    Search::Stop* stop = FailTimeStop::create(pb.fails, pb.time);

    Py_BEGIN_ALLOW_THREADS; // probablement pas genial de faire PyErr_CheckSignals la dedans...
    ProjmanSolver::run<BAB>( pb, stop );
    Py_END_ALLOW_THREADS;
    delete stop;
}

BOOST_PYTHON_MODULE(gcsp)
{
    class_<ProjmanSolution>("ProjmanSolution", no_init )
	.def("get_ntasks", &ProjmanSolution::get_ntasks )
	.def("get_duration", &ProjmanSolution::get_duration )
	.def("get_nmilestones", &ProjmanSolution::get_nmilestones )
	.def("get_milestone", &ProjmanSolution::get_milestone )
	.def("isworking", &ProjmanSolution::isworking )
	;
    class_<ProjmanProblem>("ProjmanProblem", init<int,int,int>() )
        .def("alloc", &ProjmanProblem::alloc)
	.def("begin_after_end", &ProjmanProblem::add_begin_after_end )
	.def("end_after_end", &ProjmanProblem::add_end_after_end )
	.def("begin_after_begin", &ProjmanProblem::add_begin_after_begin )
	.def("end_after_begin", &ProjmanProblem::add_end_after_begin )
	.def("set_duration", &ProjmanProblem::set_duration )
	.def("add_not_working_day", &ProjmanProblem::add_not_working_day )
	.def("set_low", &ProjmanProblem::set_low )
	.def("set_high", &ProjmanProblem::set_high )
	.def("set_time", &ProjmanProblem::set_time )
	.def("set_convexity", &ProjmanProblem::set_convexity )
	.def("get_number_of_solutions", &ProjmanProblem::get_number_of_solutions )
	.def("get_solution", &ProjmanProblem::get_solution )
	.def("set_verbosity", &ProjmanProblem::set_verbosity )
	.def("set_name", &ProjmanProblem::set_name )
    ;


    def("solve", &run_solve );
}

#if PY_VERSION_HEX < 0x02050000

extern "C" {
int PyErr_WarnEx(PyObject *category, char *msg,
                             int stack_level)
{
    return PyErr_Warn(category, msg);
}
}
#endif
