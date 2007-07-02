/* */

#include "projman_gecode.hh"
#include "timer.hh"
#include <iostream>
#include <algorithm>
#include <iomanip>

using namespace std;

ProjmanSolver::ProjmanSolver(const ProjmanProblem& pb)
    : tasks(this,pb.allocations.size(),IntSet::empty,0,pb.max_duration-1),
      last_day(this,0,pb.max_duration),
      milestones(this,pb.n_milestones,0,pb.max_duration-1)
{
    int i,j,k;
    SetVarArray real_tasks(this, pb.ntasks, IntSet::empty,0,pb.max_duration-1);
    SetVarArray task_plus_nw_cvx(this, pb.allocations.size(),
				 IntSet::empty,0,pb.max_duration-1);
    IntSet not_working_res[pb.max_resources];

    for(i=0;i<pb.max_resources;++i)
	not_working_res[i] = pb.get_not_working( i );

//    cout << "BEGIN" << endl;
//    debug(pb,tasks);
//    cout << "------------------" << endl;
	
    cout << "Initializing..."<< endl;

    for(i=0;i<pb.allocations.size();++i) {
	int res_id = pb.allocations[i].second;
	int task_id = pb.allocations[i].first;
	SetVar hull(this);
	SetVar task_plus_nw(this);

	convexHull(this, tasks[i], hull);
	rel(this, tasks[i], SOT_UNION, not_working_res[res_id], SRT_EQ, task_plus_nw );
	rel(this, task_plus_nw, SOT_INTER, hull, SRT_EQ, task_plus_nw_cvx[i]);
	if (pb.convexity) {
	    // this imposes a (pseudo-task) is convex when including not-working days
	    convex(this, task_plus_nw_cvx[i]);
	}

	// imposes resource res_id not working days on task i
	dom(this, tasks[i], SRT_DISJ, not_working_res[res_id]);
    }

    cout << "INIT" << endl;
    debug(pb, "Pseudo tasks", tasks);
    cout << "------------------" << endl;

    // This part expresses for each real task k:
    // D(k) = sum size(Ti) for i such as alloc(i).task = k
    for(int task_id=0;task_id<pb.durations.size();++task_id) {
	int duration = pb.durations[task_id];
	vector<int> this_task_pseudo_tasks;
	vector<int> this_task_resources;

	cout << "Duration for real task " << task_id << ":" << duration << endl;

	// find ressources and pseudo tasks allocated to this (real) task
	for(alloc_iter alloc=pb.allocations.begin();alloc!=pb.allocations.end();++alloc) {
	    if (alloc->first==task_id) {
		this_task_pseudo_tasks.push_back( alloc-pb.allocations.begin() );
		this_task_resources.push_back( alloc->second );
	    }
	}
	if (this_task_pseudo_tasks.size()==1) {
	    int pseudo_id = this_task_pseudo_tasks.front();
	    cardinality(this, tasks[pseudo_id], duration, duration);
	    cout << "Task " << task_id << "/" << pseudo_id << " single res" << endl;
	    rel(this, tasks[pseudo_id], SRT_EQ, real_tasks[task_id] );
	} else if (this_task_pseudo_tasks.size()>1) {
	    IntVarArray res_tasks(this,this_task_pseudo_tasks.size(), 0, duration);
	    IntVar real_task_duration(this,0, pb.max_duration);
	    SetVarArgs the_tasks(this_task_pseudo_tasks.size());
	    SetVarArgs the_tasks_nw(this_task_pseudo_tasks.size());
	    cout << "Task " << task_id << "/(";
	    for(j=0;j<this_task_pseudo_tasks.size();++j) {
		int pseudo_id = this_task_pseudo_tasks[j];
		cardinality(this, tasks[pseudo_id], 0, duration);
		cardinality(this, tasks[pseudo_id], res_tasks[j]);
		cout << pseudo_id << ",";
		the_tasks[j] = tasks[pseudo_id];
		the_tasks_nw[j] = task_plus_nw_cvx[pseudo_id];
	    }
	    linear(this, res_tasks, IRT_EQ, duration);

	    rel(this,SOT_UNION,the_tasks,real_tasks[task_id]);
	    cout << ") multiple res" << endl;

	    if (pb.convexity) {
		// make sure the task isn't interrupted
		SetVar task_total(this);
		rel(this,SOT_UNION,the_tasks_nw,task_total);
		convex(this,task_total);
	    }
	} else {
	    // duration 0, milestone
	    cardinality(this, real_tasks[task_id], duration, duration);
	    dom(this, milestones[pb.milestones[task_id]], pb.task_low[task_id], pb.task_high[task_id] );
	}
	if (this_task_pseudo_tasks.size()>=1) {
	    int min_duration = duration/this_task_pseudo_tasks.size();
	    cout << "Duration " << task_id << ":" << min_duration << "..."<<duration<<endl;
	    cardinality(this, real_tasks[task_id], min_duration, duration);
	}
	cout << "task:"<< task_id <<" "<<pb.task_low[task_id]<<"..."<<pb.task_high[task_id]<<endl;
	dom(this, real_tasks[task_id], SRT_SUB, pb.task_low[task_id], pb.task_high[task_id] );

    }

//    cout << "Before overlap" << endl;
//    debug(pb);
//    cout << "------------------" << endl;

    
    // Expresses that tasks which use the same resource must not overlap
    for(int res_id=0;res_id<pb.max_resources;++res_id) {
	vector<int> this_res_tasks;
	for(alloc_iter alloc=pb.allocations.begin();alloc!=pb.allocations.end();++alloc) {
	    if (alloc->second==res_id) {
		this_res_tasks.push_back( alloc-pb.allocations.begin() );
	    }
	}
	cout << "Resource:" << res_id << " ";
	for(i=0;i<this_res_tasks.size();++i) {
	    cout << this_res_tasks[i] << ";";
	}
	cout << endl;
	
	if (this_res_tasks.size()>1) {
	    SetVarArgs  this_res_tasks_var(this_res_tasks.size());
	    SetVar      this_res_overload(this);
	    // the non overlapping is for all task couples i<j that are associated with resource res_id 
	    for(i=0;i<this_res_tasks.size();++i) {
		for(j=i+1;j<this_res_tasks.size();++j) {
		    rel(this, tasks[this_res_tasks[i]], SRT_DISJ, tasks[this_res_tasks[j]]);
		}
	    }
	}
    }
    
    
    cout << "Before convex" << endl;
    debug(pb, "Pseudo tasks", tasks);
    cout << "------------------" << endl;

    // union of tasks is convex
    // and contains 0
    SetVar all_days(this);
    rel(this, SOT_UNION, task_plus_nw_cvx, all_days );
    dom(this, all_days, SRT_SUP, 0 );
    max(this, all_days, last_day);
    convex(this, all_days);
    


//    cout << "Before scheduling" << endl;
//    debug(pb);
//    cout << "------------------" << endl;


    // begin_after_end
    for(alloc_iter task_pair=pb.begin_after_end.begin();task_pair!=pb.begin_after_end.end();++task_pair) {
	int p0=task_pair->first;
	int p1=task_pair->second;
	IntVar max0(this,pb.task_low[p0],pb.task_high[p0]);
	IntVar min1(this,pb.task_low[p1],pb.task_high[p1]);

	if (pb.durations[p0])
	    max(this, real_tasks[p0], max0);
	else
	    eq(this, max0, milestones[pb.milestones[p0]]);

	if (pb.durations[p1])
	    min(this, real_tasks[p1], min1);
	else
	    eq(this, min1, milestones[pb.milestones[p1]]);

	rel(this, max0, IRT_LQ, min1);


 	SetVarArgs bae(2);
 	bae[0] = real_tasks[p0];
 	bae[1] = real_tasks[p1];
 	sequence(this, bae);
    }


    // begin_after_begin
    for(alloc_iter task_pair=pb.begin_after_begin.begin();
	task_pair!=pb.begin_after_begin.end();++task_pair) {
	int p0=task_pair->first;
	int p1=task_pair->second;
	IntVar min0(this,pb.task_low[p0],pb.task_high[p0]);
	IntVar min1(this,pb.task_low[p1],pb.task_high[p1]);
	if (pb.durations[p0])
	    min(this, real_tasks[p0], min0);
	else
	    eq(this, min0, milestones[pb.milestones[p0]]);
	if (pb.durations[p1])
	    min(this, real_tasks[p1], min1);
	else
	    eq(this, min1, milestones[pb.milestones[p1]]);
	rel(this, min0, IRT_LQ, min1);
    }
    // end_after_end
    for(alloc_iter task_pair=pb.end_after_end.begin();
	task_pair!=pb.end_after_end.end();++task_pair) {
	int p0=task_pair->first;
	int p1=task_pair->second;
	IntVar max0(this,pb.task_low[p0],pb.task_high[p0]);
	IntVar max1(this,pb.task_low[p1],pb.task_high[p1]);
	if (pb.durations[p0])
	    max(this, real_tasks[p0], max0);
	else
	    eq(this, max0, milestones[pb.milestones[p0]]);
	if (pb.durations[p1])
	    max(this, real_tasks[p1], max1);
	else
	    eq(this, max1, milestones[pb.milestones[p1]]);
	rel(this, max0, IRT_LQ, max1);
    }
    
    cout << "Current Res" << endl;
    debug(pb, "Pseudo tasks", tasks);
    cout << "------------------" << endl;

    int st=0;
    unsigned long pn=0;
    st = status( pn );
    cout << "Propagation status="<<st<<" pn="<<pn<<endl;

    cout << "After first propagation" << endl;
    debug(pb, "Pseudo tasks", tasks);
    cout << "------------------" << endl;
    debug(pb, "Real tasks", real_tasks);
    debug(pb, "Cvx tasks", task_plus_nw_cvx);

    cout << "ALL DAYS:" << all_days << endl;

    branch(this, tasks, SETBVAR_MIN_CARD, SETBVAL_MIN);
    branch(this, milestones, BVAR_NONE, BVAL_MIN);
}


void ProjmanSolver::debug(const ProjmanProblem& pb, std::string s, SetVarArray& _tasks)
{
    for(int i=0;i<_tasks.size();++i) {
//	int real_task_id = pb.allocations[i].first;
//	int res_id = pb.allocations[i].second;
	cout << s <<  setw(2) << i << "  ";
//	cout << "(" << _tasks[i].glbSize() << "/" << _tasks[i].lubSize() << ") ";
//	cout << "(" << _tasks[i].cardMin() << "/" << _tasks[i].cardMax() << ") ";
	cout << _tasks[i] << endl;
    }
}
	

/// Print solution
void ProjmanSolver::print(const ProjmanProblem& pb)
{ 
    cout << "Planning:" << pb.max_duration << endl;
    
    cout << "            ";
    for(int i=0;i<pb.max_duration;++i) {
	cout << i/100;
    }
    cout << endl << "            ";
    for(int i=0;i<pb.max_duration;++i) {
	cout << (i/10)%10;
    }
    cout << endl << "            ";
    for(int i=0;i<pb.max_duration;++i) {
	cout << i%10;
    }
    cout << endl;

    for(int i=0;i<pb.allocations.size();++i) {
	int real_task_id = pb.allocations[i].first;
	int res_id = pb.allocations[i].second;
	const vector<int>& not_working = pb.not_working[res_id];

	cout << "Task " <<  setw(2) << real_task_id << "/" << setw(2) << res_id << "  ";
	
	
	for(int j=0;j<pb.max_duration;++j) {
	    int  ok=0;
	    if (tasks[i].contains(j)) {
		ok = 1;
	    } else if (find(not_working.begin(), not_working.end(), j)!=not_working.end()) {
		ok = 2;
	    }
	    if (ok==1) {
		cout << "-";
	    } else if (ok==0) {
		cout << ".";
	    } else if (ok==2) {
		cout << "x";
	    }
	}
	cout << endl;
    }
    for(int i=0;i<milestones.size();++i) {
	cout << "Milestone " << i << " : " ;
	IntVarValues vl(milestones[i]);
	while ( vl() ) {
	    cout << vl.val() << ", ";
	    ++vl;
	}
	cout << endl;
    }

    debug(pb, "Task sol", tasks);
}


class FailTimeStop : public Search::Stop {
private:
    Search::TimeStop *ts;
    Search::FailStop *fs;
    FailTimeStop(int fails, int time) {
	ts = new Search::TimeStop(time);
	fs = new Search::FailStop(fails);
    }
public:
    bool stop(const Search::Statistics& s) {
	return fs->stop(s) || ts->stop(s);
    }
    /// Create appropriate stop-object
    static Search::Stop* create(int fails, int time) {
	if (fails < 0 && time < 0) return NULL;
	if (fails < 0) return new Search::TimeStop( time);
	if (time  < 0) return new Search::FailStop(fails);
	return new FailTimeStop(fails, time);
    }
};

template <template<class> class Engine>
void ProjmanSolver::run( const ProjmanProblem& pb )
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
    Search::Stop* stop = FailTimeStop::create(pb.fails, pb.time);
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

// explicit instantiation
template void ProjmanSolver::run<BAB>(const ProjmanProblem& pb);

void ProjmanSolver::constrain(Space* s)
{
    IntVar& v = static_cast<ProjmanSolver*>(s)->last_day;
    dom(this, last_day, 0, v.val()-1 );
    for(int i=0;i<tasks.size();++i) {
	dom(this,tasks[i],SRT_SUB,0,v.val()-1);
    }
}

ProjmanSolver::ProjmanSolver(bool share, ProjmanSolver& s) : Space(share,s)
{
    tasks.update(this, share, s.tasks);
    last_day.update(this, share, s.last_day);
    milestones.update(this, share, s.milestones);
}

Space* ProjmanSolver::copy(bool share)
{
    return new ProjmanSolver(share,*this);
}

IntSet ProjmanProblem::get_not_working( int res ) const
{
    const vector<int>& nw = not_working[res];
    int values[nw.size()];
    copy( nw.begin(), nw.end(), &values[0] );
    return IntSet( values, nw.size() );
//    delete values;
//    return ret;
}
