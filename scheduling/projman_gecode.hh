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

/* projman_gecode.hh

problem definition for projman solver

*/

#ifndef _PROJMAN_GECODE_
#define _PROJMAN_GECODE_

#include <vector>
#include <stdexcept>
#include <ctime>
#include <cmath>
#include "gecode/set.hh"
#include "gecode/kernel.hh"
#include "gecode/int.hh"
#include "gecode/search.hh"


// Alternate scheduling options
#define USE_LAST_DAYS  0


#define PM_VERSION(a,b,c) ((a<<16)+(b<<8)+(c))
// There is no way to test for gecode version here
// so the build system must pass GE_VERSION accordingly
// by default we build for 3.1.0 or above
#ifndef GE_VERSION
#define GE_VERSION PM_VERSION(3,1,0)
#endif
#if GE_VERSION < PM_VERSION(3,0,0)
#define SELF this
#define SET_VAR_SIZE_MAX SET_VAR_MAX_CARD
#define SET_VAR_MAX_MIN SET_VAR_MIN_UNKNOWN_ELEM
#define SET_VAL_MIN_INC SET_VAL_MIN
#else
#define SELF (*this)
#define convexHull convex
#endif

using namespace Gecode;

class ProjmanProblem;

class Timer {
private:
  clock_t t0;
public:
  void start(void);
  double stop(void);
};

forceinline void
Timer::start(void) {
  t0 = clock();
}
forceinline double
Timer::stop(void) {
  return (static_cast<double>(clock()-t0) / CLOCKS_PER_SEC) * 1000.0;
}

class ProjmanSolver : public Space {
protected:
    /// Variables
    SetVarArray res_tasks;      // days a resource is scheduled for a given task
    IntVar last_day;
#if USE_LAST_DAYS
    IntVar eta_cost;            // sum of the last days (idx) of all tasks used as a cost
    IntVarArray last_days;      // the last day of each task
#endif
    IntVarArray milestones;
public:
    /// The actual problem
    ProjmanSolver(const ProjmanProblem& pb);
    template <template<class> class Engine>
    static void run( ProjmanProblem& pb, Search::Stop* stop );
    /// Additionnal constrain for Branch And Bound
#if GE_VERSION < PM_VERSION(3,0,0)
    void constrain(Space* s);
#else
    void constrain(const Space& s);
#endif
    /// Constructor for cloning \a s
    ProjmanSolver(bool share, ProjmanSolver& s);
    /// Perform copying during cloning
    virtual Space* copy(bool share);
    virtual void print(ProjmanProblem& pb);
    virtual void debug(const ProjmanProblem& pb, std::string s, SetVarArray& _tasks);

protected:
    void show_status(const std::string&);
    void register_order( const ProjmanProblem& pb, SetVarArray& real_tasks);
    void register_convex_tasks(const ProjmanProblem& pb, SetVarArray& real_tasks);
};


#endif
