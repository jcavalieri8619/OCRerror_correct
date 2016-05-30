__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '7/28/14'

import multiprocessing
from collections import deque
import pickle
import sys

from ParallelOCRalign_Global import Manager, parallelCorpora, sharedSet, ErrorContext
from ParallelOCRalign_Consumer import makeConsumer, initConsumer
from ParallelOCRalign_Producer import produceOCRErrors


_PICKLE = True

NUMWORKERS = multiprocessing.cpu_count( )
alignments = deque( )


def consumerWrapper( item ):
    count, task = item
    return makeConsumer.closure( task, count, TotalErrors )


def buildWordMappings( alignmentContainer ):
    resources = Manager.generateInstance( Set = sharedSet, Corpora = parallelCorpora )

    global shared_set
    shared_set = resources.Set( )
    parallel_corpora = resources.Corpora( )

    fileOutputLock = multiprocessing.Lock( )
    fileOutputLock2 = multiprocessing.Lock( )
    shared_setLock = multiprocessing.Lock( )

    with open( "./Dictionaries/BritannicaWordList.txt", 'r' ) as file:
        BRIT_WordList = file.read( )

    makeConsumer( shared_set, parallel_corpora, stream_lock = fileOutputLock, \
                  splitErrors_lock = shared_setLock,
                  stream2_lock = fileOutputLock2, WordList = BRIT_WordList )

    for workload in produceOCRErrors( parallel_corpora ):
        global TotalErrors
        TotalErrors = parallel_corpora.getProperty( "TotalErrors" )

        print( "aligning corpus {ID} with {TotalErrors} errors".format( **parallel_corpora.getProperty( ) ) )
        sys.stdout.flush( )

        with multiprocessing.Pool( NUMWORKERS, initConsumer, maxtasksperchild = 1 ) as processPool:
            resultsAsync = processPool.map_async( consumerWrapper, enumerate( workload ) )
            results = resultsAsync.get( )

        alignmentContainer.extend( results )
        print( "finished aligning corpus {ID}".format( **parallel_corpora.getProperty( ) ) )

        processPool.join( )

    if _PICKLE:
        print( "pickling data" )
        with open( 'PickledData/parallelWordMappingsUPDATED.pickle', 'wb' ) as pklfile:
            pickle.dump( alignments, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( 'PickledData/parallelWordMappings_sharedSetUPDATED.pickle', 'wb' ) as pklfile:
            shared_set.add( ErrorContext( str( ), tuple( ), int( ), ErrorContext.LAST_ERROR ) )
            pickle.dump( shared_set._getvalue( ), pklfile, pickle.HIGHEST_PROTOCOL )

    return


def test( ):
    print( "beginning alignment process" )
    try:
        buildWordMappings( alignments )
    except KeyboardInterrupt:
        print( "caught keyboard intrerupt:" )
        if input( "Enter Yes to pickle completed alignments, else No:  " ) == "Yes":

            print( "pickling alignments" )
            with open( 'PickledData/parallelWordMappings.pickle', 'wb' ) as pklfile:
                pickle.dump( alignments, pklfile, pickle.HIGHEST_PROTOCOL )

            print( "pickling shared set" )
            with open( 'PickledData/parallelWordMappings_sharedSet.pickle', 'wb' ) as pklfile:
                shared_set.add( ErrorContext( str( ), tuple( ), int( ), ErrorContext.LAST_ERROR ) )
                pickle.dump( shared_set._getvalue( ), pklfile, pickle.HIGHEST_PROTOCOL )

    print( "finished" )


if __name__ == '__main__':
    print( "beginning alignment process" )
    try:
        buildWordMappings( alignments )
    except:
        print( "caught exception:" )
        if len( alignments ) > 0:

            print( "pickling alignments" )
            with open( 'PickledData/parallelWordMappingsNEW.pickle', 'wb' ) as pklfile:
                pickle.dump( alignments, pklfile, pickle.HIGHEST_PROTOCOL )

            print( "pickling shared set" )
            with open( 'PickledData/parallelWordMappings_sharedSetNEW.pickle', 'wb' ) as pklfile:
                shared_set.add( ErrorContext( str( ), tuple( ), int( ), ErrorContext.LAST_ERROR ) )
                pickle.dump( shared_set._getvalue( ), pklfile, pickle.HIGHEST_PROTOCOL )

    print( "finished" )
