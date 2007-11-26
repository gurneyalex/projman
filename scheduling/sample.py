



from gcsp import ProjmanProblem, solve

DURATIONS = [ 20, 60, 20, 20, 20, 30 ]


def reg_csp( func, l0, l1 ):
    for p0 in l0:
        for p1 in l1:
            func( p0, p1 )

def problem( max_duration ):
    NW0 = [ i for i in range(max_duration) if i%7 in (5,6) ]
    NW1 = [ i for i in range(max_duration) if i%7 in (4,5,6) ]
    pb = ProjmanProblem( 6, 3, max_duration )
    for i,d in enumerate(DURATIONS):
        pb.set_duration( i, d )
    T0 = []
    T1 = []
    T2 = []
    T3 = []
    T4 = []
    T5 = []
    T0.append( pb.alloc( 0, 1 ) )
    T1.append( pb.alloc( 1, 0 ) )
    T1.append( pb.alloc( 1, 1 ) )
    T1.append( pb.alloc( 1, 2 ) )
    T2.append( pb.alloc( 2, 0 ) )
    T3.append( pb.alloc( 3, 1 ) )
    T4.append( pb.alloc( 4, 1 ) )
    T4.append( pb.alloc( 4, 2 ) )
    T5.append( pb.alloc( 5, 0 ) )
    T5.append( pb.alloc( 5, 1 ) )

    pb.begin_after_end( 0, 1 )
    pb.begin_after_end( 0, 2 )
    pb.begin_after_end( 0, 3 )
    pb.begin_after_end( 1, 4 )
    pb.begin_after_end( 2, 4 )
    pb.begin_after_end( 3, 4 )
    pb.begin_after_begin( 4, 5 )
    

    for nw in NW0:
        pb.add_not_working_day( 0, nw )
        pb.add_not_working_day( 2, nw )
    for nw in NW1:
        pb.add_not_working_day( 1, nw )

    return pb
import sys
pb = problem( int(sys.argv[1]) )
solve( pb )

