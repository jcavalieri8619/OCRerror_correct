__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '8/24/14'

import os
import gc
import gzip
import multiprocessing
import pickle

import regex
from nltk.probability import FreqDist

from MSFT_NgramServer import LookupService


class NgramWordBreaker( object ):
    def __init__( self ):
        self._trigramModel = LookupService( model = 'bing-body/2013-12/3' )


    def breakWords( self, phrase ):
        rv = self._trigramModel.breakWord( phrase ).decode( )
        results = rv.split( '\r\n' )

        return list( map( lambda arg: arg.split( ';' )[ 0 ], results ) )


class NgramServer( object ):
    def __init__( self ):
        self._5gram = LookupService( model = 'bing-body/apr10/5' )
        self._4gram = LookupService( model = 'bing-body/apr10/4' )
        self._3gram = LookupService( model = 'bing-body/apr10/3' )
        self._2gram = LookupService( model = 'bing-body/apr10/2' )


    def query( self, phrase, order ):

        if order >= 5:

            P = self._5gram.GetConditionalProbability( phrase )
            return P
        elif order == 4:

            P = self._4gram.GetConditionalProbability( phrase )
            return P
        elif order == 3:

            P = self._3gram.GetConditionalProbability( phrase )
            return P
        elif order <= 2:

            P = self._2gram.GetConditionalProbability( phrase )
            return P


_POS_pattern = r"_(?:NOUN|VERB|ADJ|ADV|PRON|DET|ADP|NUM|CONJ|PRT|ROOT|START|END)_?"
_POS_REGEX = regex.compile( _POS_pattern )
import sys


def _buildUnigram( unigramFile ):
    print( unigramFile )
    sys.stdout.flush( )

    unigramFreqDist = FreqDist( )
    with gzip.open( unigramFile, 'rt' ) as fileObj:

        while True:

            lines = fileObj.readlines( 50000000 )

            if not lines:
                break

            for fstr in lines:

                fstr = _POS_REGEX.sub( r'', fstr )
                fstr = fstr.lower( )

                unigram, year, count, vol = fstr.split( '\t' )
                unigramFreqDist[ unigram ] += int( count )

            del lines, fstr
            gc.collect( )

    return unigramFreqDist


def initProcess( ):
    print( "Starting Process:", os.getpid( ) )


def buildGoogleUnigram( ):
    DirPrefix = "/home/jcavalie/googleNgrams_unigrams/"

    unigramFiles = os.listdir( DirPrefix )

    unigramFiles = list( map( lambda _fileName: DirPrefix + _fileName, unigramFiles ) )

    masterUnigram = FreqDist( )

    with multiprocessing.Pool( 8, initializer = initProcess ) as ProcessPool:
        resAsync = ProcessPool.map_async( _buildUnigram, unigramFiles )
        results = resAsync.get( )

    ProcessPool.join( )

    print( "all jobs finished, building master unigram" )
    for freqdist in results:
        masterUnigram.update( freqdist )

    with open( "PickledData/GoogleUnigram.pickle", 'wb' ) as pklFile:
        pickle.dump( masterUnigram, pklFile, pickle.HIGHEST_PROTOCOL )

    return


if __name__ == "__main__":
    print( "beginning process" )
    buildGoogleUnigram( )
    print( "finished" )


