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

#include "projman_problem.hh"
#include "projman_gecode.hh"
//#include "timer.hh"
#include <iostream>
#include <algorithm>
#include <iomanip>

using namespace std;


ProjmanSolver::ProjmanSolver(const ProjmanProblem& pb)
    : res_tasks(SELF,pb.res_tasks.size(),IntSet::empty,0,pb.max_duration-1),
      last_day(SELF,0,pb.max_duration),
#if USE_LAST_DAYS
      eta_cost(SELF,0,pb.max_duration*pb.res_tasks.size()),
      last_days(SELF,pb.tasks.size(),0,pb.max_duration),
#endif
      milestones(SELF,pb.milestones.size(),0,pb.max_duration-1)
{
    /* here: real task means a task as defined by the project_task.xml
             pseudo task is used to designate the part of a real task done by
             a specific resource
    */
    uint_t i,j;
    /* real_tasks: the day-print of each real (user defined) tasks */
    SetVarArray real_tasks(SELF, pb.tasks.size(), IntSet::empty,0,pb.max_duration-1);
    /* hull:  */
    SetVarArray hull(SELF, pb.res_tasks.size(), IntSet::empty,0,pb.max_duration-1);
    /* task_plus_nw_cvx: the pseudo-task plus the non-working days between start and end of the task */
    SetVarArray task_plus_nw_cvx(SELF, pb.res_tasks.size(),
				 IntSet::empty,0,pb.max_duration-1);
    /* not_working_res: set of non-working days for each resource  */
    IntSet not_working_res[pb.resources.size()];

    for(i=0;i<pb.resources.size();++i)
	not_working_res[i] = pb.get_not_working( i );

//    cout << "BEGIN" << endl;
//    debug(pb,tasks);
//    cout << "------------------" << endl;
    if (pb.verbosity>0)
	cout << "Initializing ..."<< endl;

    for(i=0;i<pb.res_tasks.size();++i) {
	uint_t res_id = pb.res_tasks[i].res_id;
	SetVar task_plus_nw(SELF);

	convexHull(SELF, res_tasks[i], hull[i]);
	rel(SELF, res_tasks[i], SOT_UNION, not_working_res[res_id], SRT_EQ, task_plus_nw );
	rel(SELF, task_plus_nw, SOT_INTER, hull[i], SRT_EQ, task_plus_nw_cvx[i]);
	if (pb.convexity) {
	    // SELF imposes a (pseudo-task) is convex when including not-working days
	    convex(SELF, task_plus_nw_cvx[i]);
	}

	// imposes resource res_id not working days on task i
	dom(SELF, res_tasks[i], SRT_DISJ, not_working_res[res_id]);
    }

    if (pb.verbosity>3) {
	debug(pb, "Pseudo tasks", res_tasks);
	cout << "------------------" << endl;
    }

    // This part expresses for each real task k:
    // Duration(k) = sum size(pseudo-Task i) for i such as alloc(i).task = k
    for(uint_t task_id=0;task_id<pb.tasks.size();++task_id) {
	const task_t& task = pb.tasks[task_id];
	int load = task.load;
	if (pb.verbosity>3) {
	    cout << "Task " << setw(10) << task.tid << " load=" << load << " pseudo=(";
	}
	if (task.resources.size()==1) {
	    uint_t pseudo_id = task.res_tasks_id.front();
	    cardinality(SELF, res_tasks[pseudo_id], load, load);
	    if (pb.verbosity>3) {
		cout << pseudo_id << ") duration=" << load;
	    }
	    rel(SELF, res_tasks[pseudo_id], SRT_EQ, real_tasks[task_id] );
	    cardinality(SELF, real_tasks[task_id], load, load);
	} else if (task.resources.size()>1) {
	    IntVarArray res_tasks_duration(SELF,task.resources.size(), 0, load);
	    IntVar real_task_duration(SELF,0, pb.max_duration);
	    SetVarArgs the_tasks(task.resources.size());
	    SetVarArgs the_tasks_nw(task.resources.size());
	    for(j=0;j<task.resources.size();++j) {
 		uint_t pseudo_id = task.res_tasks_id[j];
		cardinality(SELF, res_tasks[pseudo_id], 0, load);
		cardinality(SELF, res_tasks[pseudo_id], res_tasks_duration[j]);
		if (pb.verbosity>3) {
		    cout << pseudo_id << ",";
		}
		the_tasks[j] = res_tasks[pseudo_id];
		the_tasks_nw[j] = task_plus_nw_cvx[pseudo_id];
	    }
	    if (task.load_type==TASK_SHARED) {
		// compute the allowable range for duration of the real task
		int sz = task.resources.size();
		int min_duration = (load+sz-1)/sz; // round to largest
		if (pb.verbosity>3) {
		    cout << ") duration=" << min_duration << "..."<<load;
		}
		linear(SELF, res_tasks_duration, IRT_EQ, load);
		cardinality(SELF, real_tasks[task_id], min_duration, load);
	    } else if (task.load_type==TASK_ONEOF) {
		cardinality(SELF, real_tasks[task_id], load, load);
		if (pb.verbosity>3) {
		    cout << ") duration=" <<load;
		}
		int load_set_values[2] = { 0, load };
		IntSet load_set( load_set_values, 2);
		for(j=0;j<task.resources.size();++j) {
		    dom(SELF, res_tasks_duration[j], load_set );
		}
		linear(SELF, res_tasks_duration, IRT_EQ, load);
	    } else if (task.load_type==TASK_SAMEFORALL) {
		int tmax = 0;
		for(j=0;j<task.resources.size();++j) {
		    uint_t pseudo_id = task.res_tasks_id[j];
            int real_load = load;
		    if (load>tmax) {
			tmax = load;
		    }
		    cardinality(SELF, res_tasks[pseudo_id], real_load, real_load);
		}
		cardinality(SELF, real_tasks[task_id], tmax, tmax);
	    }

	    rel(SELF,SOT_UNION,the_tasks,real_tasks[task_id]);

	    if (task.convex) {
		// make sure the task isn't interrupted
		SetVar task_total(SELF);
		rel(SELF,SOT_UNION,the_tasks_nw,task_total);
		convex(SELF,task_total);
	    }

	} else if (task.load_type==TASK_MILESTONE) {
	    // load 0, milestone
	    if (pb.verbosity>3) {
		cout  << ") M"<< task.milestone ;
	    }
	    cardinality(SELF, real_tasks[task_id], 0, 0);
	    dom(SELF, milestones[task.milestone], task.range_low, task.range_high );
	}
	if (pb.verbosity>3) {
	    cout << " range=" << task.range_low << ".." << task.range_high << endl;
	}
	dom(SELF, real_tasks[task_id], SRT_SUB, task.range_low, task.range_high );

    } 
    
    // Expresses that tasks which use the same resource must not overlap
    for(uint_t res_id=0;res_id<pb.resources.size();++res_id) {
	const resource_t& res=pb.resources[res_id];

	if (pb.verbosity>0) {
	    cout << "Resource:" << res.rid << " ";
	    for(i=0;i<res.tasks.size();++i) {
		cout << pb.tasks[res.tasks[i]].tid << ";";
	    }
	    cout << endl;
	}
	
	if (res.tasks.size()>1) {
	    // the non overlapping is for all task couples i<j that are associated with resource res_id 
	    for(i=0;i<res.res_tasks_id.size();++i) {
		for(j=i+1;j<res.res_tasks_id.size();++j) {
		    rel(SELF, res_tasks[res.res_tasks_id[i]], SRT_DISJ, res_tasks[res.res_tasks_id[j]]);
		}
	    }
	    // XXX consider using rel( SOT_DUNION )
#if 1
	    SetVarArgs  this_res_tasks_var(res.tasks.size());
	    SetVar      this_res_overload(SELF);
	    for(i=0;i<res.res_tasks_id.size();++i) {
		this_res_tasks_var[i] = res_tasks[ res.res_tasks_id[i] ];
	    }
	    rel(SELF, SOT_UNION, this_res_tasks_var, this_res_overload );
	    // this is a global constraint which means it's supposed to
	    // propagate better than the n*(n-1)/2 disjoint constraints above
	    rel(SELF, SOT_DUNION, this_res_tasks_var, this_res_overload );
#endif
	}
    }
    if (pb.verbosity>3) {
	show_status("1");
	cout << "Before convex" << endl;
	debug(pb, "Pseudo tasks", res_tasks);
	cout << "------------------" << endl;
    }

    // union of tasks is convex
    // and contains 0
    //SetVar all_days(this);
    SetVar all_days(SELF);
    //rel(SELF, SOT_UNION, task_plus_nw_cvx, all_days );
    //dom(SELF, all_days, SRT_SUP, pb.first_day );
    rel(SELF, SOT_UNION, res_tasks, all_days ); // all_w_days = union (res_tasks)
    dom(SELF, all_days, SRT_SUP, pb.first_day );
    max(SELF, all_days, last_day);

    if (pb.verbosity>3) {
	show_status("2");
	debug(pb, "Pseudo tasks", res_tasks);    
    }

#if USE_LAST_DAYS
    for(uint_t task_id=0;task_id<pb.tasks.size();++task_id) {
	max(SELF, real_tasks[task_id], last_days[task_id] );
    }
    linear(SELF, last_days, IRT_EQ, eta_cost );
    show_status("2x");
#endif
#if 0
    // si on a des trous, ça merdoie...
    // on peut avoir des trous avec les contraintes de dates
    convex(SELF, all_days);
#endif
    
    if (pb.verbosity>3) {
	show_status("3");
    	debug(pb, "Pseudo tasks", res_tasks);    
    }

#if USE_LAST_DAYS
    if (pb.verbosity>3) {
        cout << "eta_cost:" << eta_cost << endl;
        for(uint_t task_id=0;task_id<pb.tasks.size();++task_id) {
            cout << "last_day[" << task_id << "]=" << last_days[task_id] << endl;
        }
    } 
#endif
    register_order( pb, real_tasks );

    if (pb.verbosity>3) {
	show_status("4");
        debug(pb, "Pseudo tasks", res_tasks);    
    }
    // add convexity constraints
    register_convex_tasks( pb, real_tasks);

    if (pb.verbosity>3) {
	show_status("5");
        debug(pb, "Pseudo tasks", res_tasks);
    }

    if (pb.verbosity>1) {
	    if (pb.verbosity>3) {
	        cout << "Current Res" << endl;
	        debug(pb, "Pseudo tasks", res_tasks);
	        cout << "------------------" << endl;
		show_status("6");
        }
	
    	cout << "After first propagation" << endl;
    	debug(pb, "Pseudo tasks", res_tasks);
    	cout << "------------------" << endl;
    	debug(pb, "Real tasks", real_tasks);
    	debug(pb, "Cvx tasks", task_plus_nw_cvx);
    	debug(pb, "Hull", hull);

    	cout << "ALL DAYS:" << all_days << endl;
    }
    branch(SELF, res_tasks, SET_VAR_MAX_MIN, SET_VAL_MIN_INC);
    branch(SELF, milestones, INT_VAR_NONE, INT_VAL_MIN);
}

#if GE_VERSION < PM_VERSION(3,0,0)
void ProjmanSolver::show_status(const string& str)
{
    unsigned long pn=0;
    int st=0;
    st = status( pn );
    cout << str << " Propagation status="<<st<<" pn="<<pn<<endl;	
}
#else
void ProjmanSolver::show_status(const string& str)
{
    StatusStatistics pn;
    int st=0;
    st = status( pn );
    cout << str << " Propagation status="<<st<<" pn="<<pn.propagate<<endl;
}
#endif


void ProjmanSolver::debug(const ProjmanProblem& pb, std::string s, SetVarArray& _tasks)
{
    for(int i=0;i<_tasks.size();++i) {
	cout << s <<  setw(2) << i << "  ";
	cout << _tasks[i] << endl;
    }
}
	

/// Print solution
void ProjmanSolver::print(ProjmanProblem& pb)
{
    uint_t i,j;
    if (pb.verbosity>1) {
	cout << "Planning:" << pb.max_duration << endl;
	cout << "                           ";
	for(i=0;i<pb.max_duration;++i) {
	    cout << i/100;
	}
//	cout << endl << "               ";
	cout << endl << "                           ";
	for(i=0;i<pb.max_duration;++i) {
	    cout << (i/10)%10;
	}
	cout << endl << "                           ";
	for(i=0;i<pb.max_duration;++i) {
	    cout << i%10;
	}
	cout << endl;
    }
    ProjmanSolution S(pb.res_tasks.size(),pb.max_duration,milestones.size());

    for(i=0;i<pb.res_tasks.size();++i) {
	int real_task_id = pb.res_tasks[i].task_id;
	const task_t& task = pb.tasks[real_task_id];
	int res_id = pb.res_tasks[i].res_id;
	const resource_t& res = pb.resources[res_id];

	if (pb.verbosity>1) {
	    cout <<  setw(2) << i << " ";
	    cout <<  setw(15) << task.tid << " " << setw(8) << res.rid<< " ";
	}
	
	
	for(j=0;j<pb.max_duration;++j) {
	    int  ok=0;
	    S.task_days[i][j] = false;
	    if (res_tasks[i].contains(j)) {
		S.task_days[i][j] = true;
		ok = 1;
	    } else if (find(res.not_working.begin(), res.not_working.end(), j)!=res.not_working.end()) {
		ok = 2;
	    }
	    if (pb.verbosity>1) {
		if (ok==1) {
		    cout << "-";
		} else if (ok==0) {
		    cout << ".";
		} else if (ok==2) {
		    cout << "x";
		}
	    }
	}
	if (pb.verbosity>1) {
	    cout << endl;
	}
    }
    for(int m=0;m<milestones.size();++m) {
	if (pb.verbosity>1) {
	    cout << "Milestone " << m << " : " ;
	}
	IntVarValues vl(milestones[m]);
	int last_val = -1;
	while ( vl() ) {
	    last_val = vl.val();
	    if (pb.verbosity>1) {
		cout << last_val << ", ";
	    }
	    ++vl;
	}
	S.milestones[m] = last_val;
	if (pb.verbosity>1) {
	    cout << endl;
	}
    }
    if (pb.verbosity>1) {
	debug(pb, "Task sol", res_tasks);
    }
    pb.projman_solutions.push_back( S );
}



template <template<class> class Engine>
void ProjmanSolver::run( ProjmanProblem& pb, Search::Stop *stop )
{
    double t0 = 0.0;
    int i = pb.solutions;
    Timer t;
    ProjmanSolver* s = new ProjmanSolver( pb );
    t.start();
    unsigned int n_p = 0;
    unsigned int n_b = 0;
    if (s->status() != SS_FAILED) {
	n_p = s->propagators();
#if GE_VERSION<PM_VERSION(3,2,0)
	n_b = s->branchings();
#else
	n_b = s->branchers();
#endif
    }
    Search::Options opts;
    opts.c_d = pb.c_d;
    opts.a_d = pb.a_d;
    opts.stop = stop;
    Engine<ProjmanSolver> e(s, opts); //,stop); //pb.c_d,pb.a_d,stop);
    delete s;
    do {
	ProjmanSolver* ex = e.next();
	if (ex == NULL)
	    break;
    ex->print(pb);
	delete ex;
    t0 = t0 + t.stop();
    } while (--i != 0 && t0 < pb.time);
    Search::Statistics stat = e.statistics();
    if (pb.verbosity==0) {
	cout << endl;
	cout << "Initial" << endl
	     << "\tpropagators:   " << n_p << endl
	     << "\tbranchings:    " << n_b << endl
	     << endl
	     << "Summary" << endl
	     //<< "\truntime:       " << t.stop() << endl
         << "\truntime:       " << t0 << endl
	     << "\tsolutions:     " << abs(static_cast<int>(pb.solutions) - i) << endl
	     << "\tpropagations:  " << stat.propagate << endl
	     << "\tfailures:      " << stat.fail << endl
#if GE_VERSION < PM_VERSION(3,0,0)
	     << "\tclones:        " << stat.clone << endl
	     << "\tcommits:       " << stat.commit << endl
#else
	     << "\tdepth:        " << stat.depth << endl
	     << "\tnode:       " << stat.node << endl
#endif
	     << "\tpeak memory:   "
	     << static_cast<int>((stat.memory+1023) / 1024) << " KB"
	     << endl;
    }
}

// explicit instantiation
template void ProjmanSolver::run<BAB>(ProjmanProblem& pb, Search::Stop *stop);

#if GE_VERSION < PM_VERSION(3,0,0)
void ProjmanSolver::constrain(Space* s)
{
    const ProjmanSolver& solver = *static_cast<ProjmanSolver*>(s);
#else
void ProjmanSolver::constrain(const Space& s)
{
    const ProjmanSolver& solver = dynamic_cast<const ProjmanSolver&>(s);
#endif
    uint_t day = solver.last_day.val()-1; // XXX -1 make it an option?

#if 1
    /* constraint 1 : finish all tasks earliest */
    dom(SELF, last_day, 0, day );
    for(int i=0;i<res_tasks.size();++i) {
	dom(SELF,res_tasks[i],SRT_SUB,0,day);
    }
#endif
#if 0
    int _eta_cost=0;
    /* constraint 2 : the sum of finish time for all tasks must be smallest */
    for(int i=0;i<last_days.size();++i) {
	_eta_cost+=solver.last_days[i].val();
    }
    //cout << "ETA SUM:" << _eta_cost << "/" << day << endl;
    /* post constraint that next sum of last days must be less than or equal to current */
    dom(SELF, eta_cost,0,_eta_cost);
#endif
}

ProjmanSolver::ProjmanSolver(bool share, ProjmanSolver& s) : Space(share,s)
{
    res_tasks.update(SELF, share, s.res_tasks);
    last_day.update(SELF, share, s.last_day);
#if USE_LAST_DAYS
    eta_cost.update(SELF, share, s.eta_cost);
    last_days.update(SELF, share, s.last_days);
#endif
    milestones.update(SELF, share, s.milestones);
}

Space* ProjmanSolver::copy(bool share)
{
    return new ProjmanSolver(share,*this);
}

void ProjmanSolver::register_order( const ProjmanProblem& pb,
				    SetVarArray& real_tasks )
{
    const_constraint_iter it;
    for(it=pb.task_constraints.begin();it!=pb.task_constraints.end();++it) {
	int p0=it->task0;
	int p1=it->task1;
	const task_t& task0 = pb.tasks[p0];
	const task_t& task1 = pb.tasks[p1];
	constraint_type_t type=it->type;
	IntVar bound0(SELF,task0.range_low,task0.range_high);
	IntVar bound1(SELF,task1.range_low,task1.range_high);
	IntRelType rel_type = IRT_GR;

	if (pb.verbosity>0) {
	    cout << task0.tid ;
	    switch(type) {
	    case BEGIN_AFTER_BEGIN:
		cout << " begin_after_begin ";
		break;
	    case BEGIN_AFTER_END:
		cout << " begin_after_end ";
		break;
	    case END_AFTER_END:
		cout << " end_after_end ";
		break;
	    case END_AFTER_BEGIN:
		cout << " end_after_begin ";
		break;
	    }
	    cout << task1.tid << endl;
	}
	if (task0.load_type!=TASK_MILESTONE) {
	    switch(type) {
	    case BEGIN_AFTER_BEGIN:
	    case BEGIN_AFTER_END:
		min(SELF, real_tasks[p0], bound0);
		break;
	    case END_AFTER_END:
	    case END_AFTER_BEGIN:
		max(SELF, real_tasks[p0], bound0);
	    }
	} else {
	  rel(SELF, bound0, IRT_EQ, milestones[task0.milestone]);
	    rel_type = IRT_GQ;
	}

	if (task1.load_type!=TASK_MILESTONE) {
	    switch(type) {
	    case BEGIN_AFTER_BEGIN:
	    case END_AFTER_BEGIN:
		min(SELF, real_tasks[p1], bound1);
		break;
	    case BEGIN_AFTER_END:
	    case END_AFTER_END:
		max(SELF, real_tasks[p1], bound1);
		break;
	    }
	} else {
	  rel(SELF, bound1, IRT_EQ, milestones[task1.milestone]);
	  //rel_type = IRT_GQ;
	}

	rel(SELF, bound0, rel_type, bound1);
    }
}

void ProjmanSolver::register_convex_tasks( const ProjmanProblem& pb,
				    SetVarArray& real_tasks )
{
    int nb_tasks = pb.tasks.size();
    for (int i=0; i<nb_tasks; i++)
    {
        if (pb.tasks[i].can_interrupt==0)
        {
            convex(SELF, real_tasks[i]);
        }
    }
}
