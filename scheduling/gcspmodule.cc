
/* gecode/csp module for projman */

#include <boost/python.hpp>

#include "projman_gecode.hh"

using namespace boost::python;

BOOST_PYTHON_MODULE(gcsp)
{
    class_<ProjmanProblem>("ProjmanProblem", init<int,int,int>() )
        .def("alloc", &ProjmanProblem::alloc)
	.def("begin_after_end", &ProjmanProblem::add_begin_after_end )
	.def("end_after_end", &ProjmanProblem::add_end_after_end )
	.def("begin_after_begin", &ProjmanProblem::add_begin_after_begin )
	.def("end_after_begin", &ProjmanProblem::add_end_after_begin )
	.def("set_duration", &ProjmanProblem::set_duration )
	.def("add_not_working_day", &ProjmanProblem::add_not_working_day )
    ;

    def("solve", &ProjmanSolver::run<BAB> );
}

#if PY_VERSION_EX < 0x02050000
#include <Python.h>

extern "C" {
int PyErr_WarnEx(PyObject *category, char *msg,
                             int stack_level)
{
    return PyErr_Warn(category, msg);
}
}
#endif
