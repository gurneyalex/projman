



from gcsp import ProjmanProblem, solve

DURATIONS = [ 2, 4, 2, 2, 2, 3 ]
NW0 = [5,6,12,13]
NW1 = [4,5,6,11,12,13]

def problem( max_duration ):
    pb = ProjmanProblem( 6, 2, max_duration )
    for i,d in enumerate(DURATIONS):
        pb.set_duration( i, d )
    T = []
    T.append( pb.alloc( 0, 1 ) )
    T.append( pb.alloc( 1, 0 ) )
    T.append( pb.alloc( 1, 1 ) )
    T.append( pb.alloc( 2, 0 ) )
    T.append( pb.alloc( 3, 1 ) )
    T.append( pb.alloc( 4, 1 ) )
    T.append( pb.alloc( 5, 0 ) )
    T.append( pb.alloc( 5, 1 ) )

    pb.begin_after_end( T[0], T[1] )
    pb.begin_after_end( T[0], T[2] )
    pb.begin_after_end( T[0], T[3] )
    pb.begin_after_end( T[0], T[4] )
    pb.begin_after_end( T[1], T[5] )
    pb.begin_after_end( T[2], T[5] )
    pb.begin_after_end( T[3], T[5] )
    pb.begin_after_end( T[4], T[5] )
    pb.begin_after_begin( T[5], T[6] )
    pb.begin_after_begin( T[5], T[7] )

    for nw in NW0:
        pb.add_not_working_day( 0, nw )
    for nw in NW1:
        pb.add_not_working_day( 1, nw )

    return pb
import sys
pb = problem( int(sys.argv[1]) )
solve( pb )

