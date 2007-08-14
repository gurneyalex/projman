/* */

#include "projman_problem.hh"
#include "projman_gecode.hh"
#include "timer.hh"
#include <iostream>
#include <algorithm>
#include <iomanip>

using namespace std;

ProjmanSolver::ProjmanSolver(const ProjmanProblem& pb)
    : res_tasks(this,pb.res_tasks.size(),IntSet::empty,0,pb.max_duration-1),
      last_day(this,0,pb.max_duration),
      milestones(this,pb.milestones.size(),0,pb.max_duration-1)
{
    uint_t i,j;
    SetVarArray real_tasks(this, pb.tasks.size(), IntSet::empty,0,pb.max_duration-1);
    SetVarArray hull(this, pb.res_tasks.size(), IntSet::empty,0,pb.max_duration-1);
    SetVarArray task_plus_nw_cvx(this, pb.res_tasks.size(),
				 IntSet::empty,0,pb.max_duration-1);
    IntSet not_working_res[pb.resources.size()];

    for(i=0;i<pb.resources.size();++i)
	not_working_res[i] = pb.get_not_working( i );

//    cout << "BEGIN" << endl;
//    debug(pb,tasks);
//    cout << "------------------" << endl;
    if (pb.verbosity>0)
	cout << "Initializing..."<< endl;

    for(i=0;i<pb.res_tasks.size();++i) {
	uint_t res_id = pb.res_tasks[i].second;
	SetVar task_plus_nw(this);

	convexHull(this, res_tasks[i], hull[i]);
	rel(this, res_tasks[i], SOT_UNION, not_working_res[res_id], SRT_EQ, task_plus_nw );
	rel(this, task_plus_nw, SOT_INTER, hull[i], SRT_EQ, task_plus_nw_cvx[i]);
	if (pb.convexity) {
	    // this imposes a (pseudo-task) is convex when including not-working days
	    convex(this, task_plus_nw_cvx[i]);
	}

	// imposes resource res_id not working days on task i
	dom(this, res_tasks[i], SRT_DISJ, not_working_res[res_id]);
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
	    cardinality(this, res_tasks[pseudo_id], load, load);
	    if (pb.verbosity>3) {
		cout << pseudo_id << ") duration=" << load;
	    }
	    rel(this, res_tasks[pseudo_id], SRT_EQ, real_tasks[task_id] );
	    cardinality(this, real_tasks[task_id], load, load);
	} else if (task.resources.size()>1) {
	    IntVarArray res_tasks_duration(this,task.resources.size(), 0, load);
	    IntVar real_task_duration(this,0, pb.max_duration);
	    SetVarArgs the_tasks(task.resources.size());
	    SetVarArgs the_tasks_nw(task.resources.size());
	    for(j=0;j<task.resources.size();++j) {
 		uint_t pseudo_id = task.res_tasks_id[j];
		cardinality(this, res_tasks[pseudo_id], 0, load);
		cardinality(this, res_tasks[pseudo_id], res_tasks_duration[j]);
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
		linear(this, res_tasks_duration, IRT_EQ, load);
		cardinality(this, real_tasks[task_id], min_duration, load);
	    } else if (task.load_type==TASK_ONEOF) {
		cardinality(this, real_tasks[task_id], load, load);
		if (pb.verbosity>3) {
		    cout << ") duration=" <<load;
		}
		int load_set_values[2] = { 0, load };
		IntSet load_set( load_set_values, 2);
		for(j=0;j<task.resources.size();++j) {
		    dom(this, res_tasks_duration[j], load_set );
		}
		linear(this, res_tasks_duration, IRT_EQ, load);
	    } else if (task.load_type==TASK_SAMEFORALL) {
		for(j=0;j<task.resources.size();++j) {
		    uint_t pseudo_id = task.res_tasks_id[j];
		    cardinality(this, res_tasks[pseudo_id], load, load);
		}
		cardinality(this, real_tasks[task_id], load, load);
	    }

	    rel(this,SOT_UNION,the_tasks,real_tasks[task_id]);

	    if (task.convex) {
		// make sure the task isn't interrupted
		SetVar task_total(this);
		rel(this,SOT_UNION,the_tasks_nw,task_total);
		convex(this,task_total);
	    }

	} else if (task.load_type==TASK_MILESTONE) {
	    // load 0, milestone
	    if (pb.verbosity>3) {
		cout  << ") M"<< task.milestone ;
	    }
	    cardinality(this, real_tasks[task_id], 0, 0);
	    dom(this, milestones[task.milestone], task.range_low, task.range_high );
	}
	if (pb.verbosity>3) {
	    cout << " range=" << task.range_low << ".." << task.range_high << endl;
	}
	dom(this, real_tasks[task_id], SRT_SUB, task.range_low, task.range_high );

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
		    rel(this, res_tasks[res.res_tasks_id[i]], SRT_DISJ, res_tasks[res.res_tasks_id[j]]);
		}
	    }
	    // XXX consider using rel( SOT_DUNION )
#if 0
	    SetVarArgs  this_res_tasks_var(res.tasks.size());
	    SetVar      this_res_overload(this);
	    for(i=0;i<res.res_tasks_id.size();++i) {
		this_res_tasks_var[i] = res_tasks[ res.res_tasks_id[i] ];
	    }
	    rel(this, SOT_UNION, this_res_tasks_var, this_res_overload );
	    rel(this, SOT_DUNION, this_res_tasks_var, this_res_overload );
#endif
	}
    }
    
    if (pb.verbosity>3) {
	cout << "Before convex" << endl;
	debug(pb, "Pseudo tasks", res_tasks);
	cout << "------------------" << endl;
    }

    // union of tasks is convex
    // and contains 0
    SetVar all_days(this);
    //SetVar all_w_days(this);
    rel(this, SOT_UNION, task_plus_nw_cvx, all_days );
    dom(this, all_days, SRT_SUP, pb.first_day );
    max(this, all_days, last_day);
#if 0
    // si on a des trous, ça merdoie...
    // on peut avoir des trous avec les contraintes de dates
    convex(this, all_days);
#endif
    //rel(this, SOT_UNION, tasks, all_w_days );
    //dom(this, all_w_days, SRT_SUP, 0 );

    register_order( pb, real_tasks );
    
    if (pb.verbosity>1) {
	if (pb.verbosity>3) {
	    cout << "Current Res" << endl;
	    debug(pb, "Pseudo tasks", res_tasks);
	    cout << "------------------" << endl;
	}

	int st=0;
	unsigned long pn=0;
	st = status( pn );
	cout << "Propagation status="<<st<<" pn="<<pn<<endl;
	
	cout << "After first propagation" << endl;
	debug(pb, "Pseudo tasks", res_tasks);
	cout << "------------------" << endl;
	debug(pb, "Real tasks", real_tasks);
	debug(pb, "Cvx tasks", task_plus_nw_cvx);
	debug(pb, "Hull", hull);

	cout << "ALL DAYS:" << all_days << endl;
    }
    branch(this, res_tasks, SETBVAR_MIN_CARD, SETBVAL_MIN);
    branch(this, milestones, BVAR_NONE, BVAL_MIN);
}


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
    if (pb.verbosity>0) {
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
	int real_task_id = pb.res_tasks[i].first;
	const task_t& task = pb.tasks[real_task_id];
	int res_id = pb.res_tasks[i].second;
	const resource_t& res = pb.resources[res_id];

	if (pb.verbosity>0) {
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
	    if (pb.verbosity>0) {
		if (ok==1) {
		    cout << "-";
		} else if (ok==0) {
		    cout << ".";
		} else if (ok==2) {
		    cout << "x";
		}
	    }
	}
	if (pb.verbosity>0) {
	    cout << endl;
	}
    }
    for(int m=0;m<milestones.size();++m) {
	if (pb.verbosity>0) {
	    cout << "Milestone " << m << " : " ;
	}
	IntVarValues vl(milestones[m]);
	int last_val = -1;
	while ( vl() ) {
	    last_val = vl.val();
	    if (pb.verbosity>0) {
		cout << last_val << ", ";
	    }
	    ++vl;
	}
	S.milestones[m] = last_val;
	if (pb.verbosity>0) {
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
    int i = pb.solutions;
    Timer t;
    ProjmanSolver* s = new ProjmanSolver( pb );
    t.start();
    unsigned int n_p = 0;
    unsigned int n_b = 0;
    if (s->status() != SS_FAILED) {
	n_p = s->propagators();
	n_b = s->branchings();
    }
    Engine<ProjmanSolver> e(s,pb.c_d,pb.a_d,stop);
    delete s;
    do {
	ProjmanSolver* ex = e.next();
	if (ex == NULL)
	    break;
	ex->print(pb);
	delete ex;
    } while (--i != 0);
    Search::Statistics stat = e.statistics();
    if (pb.verbosity>0) {
	cout << endl;
	cout << "Initial" << endl
	     << "\tpropagators:   " << n_p << endl
	     << "\tbranchings:    " << n_b << endl
	     << endl
	     << "Summary" << endl
	     << "\truntime:       " << t.stop() << endl
	     << "\tsolutions:     " << abs(static_cast<int>(pb.solutions) - i) << endl
	     << "\tpropagations:  " << stat.propagate << endl
	     << "\tfailures:      " << stat.fail << endl
	     << "\tclones:        " << stat.clone << endl
	     << "\tcommits:       " << stat.commit << endl
	     << "\tpeak memory:   "
	     << static_cast<int>((stat.memory+1023) / 1024) << " KB"
	     << endl;
    }
}

// explicit instantiation
template void ProjmanSolver::run<BAB>(ProjmanProblem& pb, Search::Stop *stop);

void ProjmanSolver::constrain(Space* s)
{
    IntVar& v = static_cast<ProjmanSolver*>(s)->last_day;
    uint_t day = v.val(); // XXX -1 make it an option?
    dom(this, last_day, 0, day );
    for(int i=0;i<res_tasks.size();++i) {
	dom(this,res_tasks[i],SRT_SUB,0,day);
    }
}

ProjmanSolver::ProjmanSolver(bool share, ProjmanSolver& s) : Space(share,s)
{
    res_tasks.update(this, share, s.res_tasks);
    last_day.update(this, share, s.last_day);
    milestones.update(this, share, s.milestones);
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
	IntVar bound0(this,task0.range_low,task0.range_high);
	IntVar bound1(this,task1.range_low,task1.range_high);
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
		min(this, real_tasks[p0], bound0);
		break;
	    case END_AFTER_END:
	    case END_AFTER_BEGIN:
		max(this, real_tasks[p0], bound0);
	    }
	} else {
	    eq(this, bound0, milestones[task0.milestone]);
	    rel_type = IRT_GQ;
	}

	if (task1.load_type!=TASK_MILESTONE) {
	    switch(type) {
	    case BEGIN_AFTER_BEGIN:
	    case END_AFTER_BEGIN:
		min(this, real_tasks[p1], bound1);
		break;
	    case BEGIN_AFTER_END:
	    case END_AFTER_END:
		max(this, real_tasks[p1], bound1);
		break;
	    }
	} else {
	    eq(this, bound1, milestones[task1.milestone]);
	    //rel_type = IRT_GQ;
	}

	rel(this, bound0, rel_type, bound1);
    }
}
