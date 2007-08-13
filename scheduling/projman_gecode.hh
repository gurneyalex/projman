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

class ProjmanProblem;

class ProjmanSolver : public Space {
protected:
    /// Variables
    SetVarArray res_tasks;      // days a resource is scheduled for a given task
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
    void register_order( const ProjmanProblem& pb, SetVarArray& real_tasks);
};


#endif
