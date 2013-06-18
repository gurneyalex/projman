// Copyright (c) 2000-2013 LOGILAB S.A. (Paris, FRANCE).
// http://www.logilab.fr/ -- mailto:contact@logilab.fr

// This program is free software; you can redistribute it and/or modify it under
// the terms of the GNU General Public License as published by the Free Software
// Foundation; either version 2 of the License, or (at your option) any later
// version.

// This program is distributed in the hope that it will be useful, but WITHOUT
// ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
// FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

// You should have received a copy of the GNU General Public License along with
// this program; if not, write to the Free Software Foundation, Inc.,
// 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.


/* gecode/csp module for projman */

#include <Python.h>
#include <boost/python.hpp>

#include "projman_problem.hh"
#include "projman_gecode.hh"
//#include "timer.hh"

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
#if GE_VERSION < PM_VERSION(3,1,0)
    /* gecode 3.0.0 and below */
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
#else
    /* from gecode 3.1.0 */
    bool stop(const Search::Statistics& s, const Search::Options &o) {
	int sigs = PyErr_CheckSignals();
	bool fs_stop = false;
	bool ts_stop = false;
	if (fs) {
	    fs_stop = fs->stop(s,o);
	}
	if (ts) {
	    ts_stop = ts->stop(s,o);
	}
	return sigs || fs_stop || ts_stop;
    }
#endif
    /// Create appropriate stop-object
    static Search::Stop* create(int fails, int time) {
	return new FailTimeStop(fails, time);
    }
};

void run_solve( ProjmanProblem& pb ) {
    Search::Stop* stop = FailTimeStop::create(pb.fails, pb.time);

    //Py_BEGIN_ALLOW_THREADS; // probablement pas genial de faire PyErr_CheckSignals la dedans...
    ProjmanSolver::run<BAB>( pb, stop );
    //Py_END_ALLOW_THREADS;
    delete stop;
}

BOOST_PYTHON_MODULE(gcsp)
{
    enum_<constraint_type_t>("constraint_types")
	.value("BEGIN_AFTER_BEGIN", BEGIN_AFTER_BEGIN)
	.value("BEGIN_AFTER_END", BEGIN_AFTER_END)
	.value("END_AFTER_END", END_AFTER_END)
	.value("END_AFTER_BEGIN", END_AFTER_BEGIN);

    enum_<load_type_t>("load_types")
	.value("TASK_SHARED", TASK_SHARED)
	.value("TASK_ONEOF", TASK_ONEOF)
	.value("TASK_SAMEFORALL", TASK_SAMEFORALL)
	.value("TASK_SPREAD", TASK_SPREAD)
	.value("TASK_MILESTONE", TASK_MILESTONE);

    class_<ProjmanSolution>("ProjmanSolution", no_init )
	.def("get_ntasks", &ProjmanSolution::get_ntasks )
	.def("get_duration", &ProjmanSolution::get_duration )
	.def("get_nmilestones", &ProjmanSolution::get_nmilestones )
	.def("get_milestone", &ProjmanSolution::get_milestone )
	.def("isworking", &ProjmanSolution::isworking )
	;
    class_<ProjmanProblem>("ProjmanProblem", init<uint_t>() )
	.def("set_time", &ProjmanProblem::set_time )
	.def("set_convexity", &ProjmanProblem::set_convexity )
	.def("get_number_of_solutions", &ProjmanProblem::get_number_of_solutions )
    .def("set_max_nb_solutions", &ProjmanProblem::set_max_nb_solutions )
	.def("get_solution", &ProjmanProblem::get_solution )
	.def("set_verbosity", &ProjmanProblem::set_verbosity )
	.def("set_first_day", &ProjmanProblem::set_first_day )
// new interface
	.def("add_task_constraint", &ProjmanProblem::add_task_constraint )
	.def("add_worker", &ProjmanProblem::add_worker )
	.def("add_task", &ProjmanProblem::add_task )
	.def("set_task_range", &ProjmanProblem::set_task_range )
	.def("add_not_working_day", &ProjmanProblem::add_not_working_day )
	.def("add_resource_to_task", &ProjmanProblem::add_resource_to_task )
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
