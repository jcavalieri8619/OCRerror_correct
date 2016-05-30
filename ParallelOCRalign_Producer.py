__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '7/14/14'

import os
import sys
from itertools import tee
from collections import deque

from ParallelGlobal import ErrorContext, getAspellChecker


_DEBUG = True


def _pairwise( iterable ):
    a, b = tee( iterable )
    next( b, None )
    return zip( a, b )


def produceOCRErrors( parallel_corpora ):
    prefix = './parallel/'
    cleanCorpora = os.listdir( prefix + 'clean/' )
    dirtyCorpora = os.listdir( prefix + 'dirty/' )

    cleanCorpora.sort( )
    dirtyCorpora.sort( )

    totalErrorCount = 0

    checker = getAspellChecker( )

    for (corpusNum, (clean, dirty)) in enumerate( zip( cleanCorpora, dirtyCorpora ) ):

        with open( prefix + 'clean/' + clean, 'r', encoding = 'ISO-8859-15' ) as cleanfile, \
                open( prefix + 'dirty/' + dirty, 'r' ) as dirtyfile:

            parallel_corpora.setCorpora( cleanfile.read( ), dirtyfile.read( ), corpusNum + 1 )

        cleanErrs = set( )
        dirtyErrs = deque( )

        if _DEBUG:
            print( "START: building error list" )
            sys.stdout.flush( )

        checker.set_text( parallel_corpora.getCorpora( "clean" ) )

        for err in checker:
            cleanErrs.add( err.word )

        checker.set_text( parallel_corpora.getCorpora( "dirty" ) )

        for err in checker:
            if err.word not in cleanErrs:
                dirtyErrs.append( ErrorContext( Error = err.word, \
                                                Context = (err.leading_context( ErrorContext.LCONTEXT_SIZE ), \
                                                           err.trailing_context( ErrorContext.RCONTEXT_SIZE )), \
                                                Position = err.wordpos, \
                                                ID = totalErrorCount ) )
                totalErrorCount += 1

        if _DEBUG:
            print( "END: building error list" )
            sys.stdout.flush( )

        parallel_corpora.setProperties( TotalErrors = len( dirtyErrs ) )

        dirtyErrs.append( ErrorContext( Error = str( ), Context = tuple( ), \
                                        Position = int( ), ID = ErrorContext.LAST_ERROR ) )

        yield [ list( W ) for W in _pairwise( dirtyErrs ) ]

    raise StopIteration









