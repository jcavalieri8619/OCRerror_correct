__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '8/16/14'

import multiprocessing
import pickle
import signal

import CharacterAligner
from locateErrorWindows import determineErrWindows
from generateSubstringMappings import genSubstrMaps
from spellingErrorStats import OCRErrorStats
from ParallelGlobal import Manager


_CORRECT = 0
_INCORRECT = 1

_NUMWORKERS = 4


class timeout:
    def __init__( self, seconds, error_message = 'Timeout' ):
        self.seconds = seconds
        self.error_message = error_message


    def handle_timeout( self, signum, frame ):
        raise TimeoutError( self.error_message )


    def __enter__( self ):
        signal.signal( signal.SIGALRM, self.handle_timeout )
        signal.alarm( self.seconds )


    def __exit__( self, type, value, traceback ):
        signal.alarm( 0 )


def partitioner( word_mapping ):
    count = word_mapping[ 0 ]

    word_mapping = word_mapping[ 1 ]

    char_mapping = CharacterAligner.alignChars( word_mapping[ _CORRECT ], word_mapping[ _INCORRECT ],
                                                ErrStats = OCRErrStats, ErrStats_lock = Statslock )

    char_mapping, error_wins = determineErrWindows( char_mapping, ErrStats = OCRErrStats, ErrStats_lock = Statslock )

    try:
        with timeout( seconds = 19 ):
            rv = (word_mapping[ _CORRECT ], genSubstrMaps( char_mapping, error_wins,
                                                           bool( OCRErrStats ) ))
    except TimeoutError as err:
        print( 'PARTITION_TIMEOUT:', word_mapping )
        rv = (None, [ ])

    return rv


_sharedResource = Manager.generateInstance( OCRStats = OCRErrorStats )


def partitionStrAlignments( word_mappings, **kwargs ):
    print( "START: partitioning {} word mappings".format( len( word_mappings ) ) )

    global OCRErrStats, Statslock
    if kwargs.get( 'phase', None ) == 'training':
        OCRErrStats = _sharedResource.OCRStats( )
        Statslock = multiprocessing.Lock( )
    elif kwargs.get( 'phase', None ) is None:
        OCRErrStats = None
        Statslock = None
    elif kwargs.get( 'phase' ) == 'still-training':
        pass

    with multiprocessing.Pool( _NUMWORKERS ) as processPool:
        results = processPool.map( partitioner, enumerate( word_mappings ), chunksize = 20 )

    processPool.join( )

    partitionContainer = dict( )
    for k, v in results:
        if k is not None:
            partitionContainer[ k ] = v

    if kwargs.get( 'pickle_stats' ) is True:
        OCRErrStats.pickleAllErrorStats( )

    print("END: partitioning word mappings")
    return partitionContainer


if __name__ == '__main__':
    print( "starting test" )
    with open( '/home/jcavalie/PycharmProjs_unsynced/OCRpickledExtras/EnchantWordMappings.pickle',
               'rb' ) as mappingFile:
        word_mappings1 = pickle.load( mappingFile )
    word_mappingSLICE = [ word_mappings1[ i ] for i in range( 200 ) ]
    Partitions = partitionStrAlignments( word_mappingSLICE )
    with open( 'printedData/testmaps2NEW.txt', 'w' ) as file:
        for thing in Partitions:
            file.write( str( thing ) + '\n\n' )
    print( "finished" )