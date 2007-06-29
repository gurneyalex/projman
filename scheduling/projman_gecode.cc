/* */

#include "projman_gecode.hh"
#include "timer.hh"
#include <iostream>
#include <algorithm>

using namespace std;

ProjmanSolver::ProjmanSolver(const ProjmanProblem& pb)
    : tasks(this,pb.allocations.size(),IntSet::empty,0,pb.max_duration-1),
      last_day(this,0,pb.max_duration)
{
    int i,j,k;
	
    cout << "Initializing..."<< endl;
//	for(i=0;i<pb.allocations.size();++i) {
//	    convex(this, tasks[i]);
//	    cout << "convexity for pseudo task " << i << endl;
//	}

    // This part expresses for each real task k:
    // D(k) = sum size(Ti) for i such as alloc(i).task = k
    for(int task_id=0;task_id<pb.durations.size();++task_id) {
	int duration = pb.durations[task_id];
	vector<int> this_task_pseudo_tasks;
	vector<int> this_task_resources;

	cout << "Duration for real task " << task_id << endl;

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
	} else {
	    IntVarArray res_tasks(this,this_task_pseudo_tasks.size(), 0, pb.max_duration);
	    IntVar real_task_duration(this,0, pb.max_duration);
	    for(j=0;j<this_task_pseudo_tasks.size();++j) {
		int pseudo_id = this_task_pseudo_tasks[j];
		cardinality(this, tasks[pseudo_id], res_tasks[j]);
	    }
	    linear(this, res_tasks, IRT_EQ, duration);
	    cout << "Task " << task_id << "/* using "<<this_task_pseudo_tasks.size()<< " res" << endl;
	}
    }
    
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
		    rel(this, tasks[this_res_tasks[i]], SOT_INTER, tasks[this_res_tasks[j]],
			SRT_EQ, IntSet::empty );
		}
		IntSet not_working_res = pb.get_not_working(res_id);
		rel(this, tasks[this_res_tasks[i]], SOT_INTER, not_working_res , SRT_EQ, IntSet::empty );
	    }
	}
    }
    

    // union of tasks is convex
    // and contains 0
    SetVar all_days(this);
    rel(this, SOT_UNION, tasks, all_days );
    dom(this, all_days, SRT_SUP, 0 );
    max(this, all_days, last_day);
    
    // begin_after_end
    for(alloc_iter task_pair=pb.begin_after_end.begin();task_pair!=pb.begin_after_end.end();++task_pair) {
	SetVarArgs bae(2);
	bae[0] = tasks[task_pair->first];
	bae[1] = tasks[task_pair->second];
	sequence(this, bae);
    }
    // begin_after_begin
    for(alloc_iter task_pair=pb.begin_after_begin.begin();task_pair!=pb.begin_after_begin.end();++task_pair) {
	IntVar min0(this,0,pb.max_duration), min1(this,0,pb.max_duration);
	min(this, tasks[task_pair->first], min0);
	min(this, tasks[task_pair->second], min1);
	rel(this, min0, IRT_LQ, min1);
    }
    
	
    branch(this, tasks, SETBVAR_NONE, SETBVAL_MIN);
}


/// Print solution
void ProjmanSolver::print(const ProjmanProblem& pb)
{ 
    cout << "Planning:" << pb.max_duration << endl;
      
    for(int i=0;i<pb.allocations.size();++i) {
	int real_task_id = pb.allocations[i].first;
	int res_id = pb.allocations[i].second;
	const vector<int>& not_working = pb.not_working[res_id];

	cout << "Task " <<  real_task_id << "/" << res_id << "  ";
	
	
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
    dom(this, last_day, 0, static_cast<ProjmanSolver*>(s)->last_day.val()-1 );
}

ProjmanSolver::ProjmanSolver(bool share, ProjmanSolver& s) : Space(share,s)
{
    tasks.update(this, share, s.tasks);
    last_day.update(this, share, s.last_day);
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
