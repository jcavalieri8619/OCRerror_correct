__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '7/22/14'

from collections import namedtuple
from multiprocessing.managers import BaseManager
import unicodedata
import sys
import math
import os

import regex
from enchant.checker import SpellChecker


_DEBUG = True


class sharedSet( set ):
    pass


class parallelCorpora( object ):
    SLICE_CONTEXT = 1217


    @staticmethod
    def getSLICE_CONTEXT( ):
        return parallelCorpora.SLICE_CONTEXT


    def __init__( self, clean_corpus = None, dirty_corpus = None, ID = None ):

        self._clean_corpus = None
        self._dirty_corpus = None
        self._properties = dict( )

        if clean_corpus and dirty_corpus and ID:
            self.setCorpora( clean_corpus, dirty_corpus, ID )


    def setProperties( self, **kwargs ):
        self._properties.update( **kwargs )


    def getProperty( self, property_ = None ):
        return self._properties.get( property_, None ) if property_ is not None else self._properties


    def getCorporaSlice( self, version, base_position, context_multiple ):

        corpus = self.getCorpora( version )

        if context_multiple == 0:
            PADDING = 0
        else:
            PADDING = 157

        EXPAND = 1
        if base_position - (context_multiple + 1) * parallelCorpora.SLICE_CONTEXT < 0:
            left_left = 0
            if base_position - context_multiple * parallelCorpora.SLICE_CONTEXT < 0:
                left_right = 0
                EXPAND = 2

            else:
                left_right = base_position - context_multiple * parallelCorpora.SLICE_CONTEXT + PADDING
        else:
            left_left = base_position - (context_multiple + 1) * parallelCorpora.SLICE_CONTEXT * EXPAND
            left_right = base_position - (context_multiple * parallelCorpora.SLICE_CONTEXT * EXPAND) + PADDING

        leftSlice = corpus[ left_left:left_right ]

        right_left = base_position + (context_multiple * parallelCorpora.SLICE_CONTEXT) - PADDING
        right_right = base_position + (context_multiple + 1) * parallelCorpora.SLICE_CONTEXT

        rightSlice = corpus[ right_left:right_right ]

        if context_multiple == 0:
            corpusSlice = leftSlice + rightSlice
        else:
            corpusSlice = leftSlice + ' ' + rightSlice

        return { "slice": corpusSlice, "data": { 'LLpos': left_left, 'LRpos': left_right, 'RLpos': right_left } }


    def getCorpora( self, version = None ):
        """
        gets parallel corpora; if version not None then get the particular version
        :return: dict {"clean":clean_corpus, "dirty":dirty_corpus}[version]

        """
        if not self._clean_corpus and not self._dirty_corpus:
            raise RuntimeError( "Corpora text must be set before accessing" )
        else:

            corporaDict = { "clean": self._clean_corpus, "dirty": self._dirty_corpus }
            return corporaDict[ version ] if version else corporaDict


    def setCorpora( self, clean, dirty, ID ):
        """
        normalizes and sets parallel documents
        :param clean: clean version of corpus
        :param dirty: dirty version of corpus
        :param ID: parallel corpora ID
        :return: None
        """
        if _DEBUG:
            print( "START: preprocessing parallel corpora" )
            sys.stdout.flush( )
        parallelText = self._normalize( clean, dirty )
        if _DEBUG:
            print( "END: preprocessing parallel corpora" )
            sys.stdout.flush( )
        self._clean_corpus = parallelText[ "clean" ]
        self._dirty_corpus = parallelText[ "dirty" ]
        self._properties[ 'ID' ] = ID


    @staticmethod
    def _normalize( cleanTxt, dirtyTxt ):
        cleanCorpus = unicodedata.normalize( 'NFKD', cleanTxt.lower( ) ).encode( 'ascii', 'ignore' )
        cleanCorpus = cleanCorpus.decode( 'ascii' )
        dirtyCorpus = dirtyTxt.lower( )

        cleanCorpus = cleanCorpus.replace( '_', ' ' ).replace( '|', '' ).replace( '&c.', ' ' ). \
            replace( '`', ' ' ).replace( '@', ' ' ).replace( '(', '' ).replace( ')', '' ).replace( '"', '' ). \
            replace( "''", "" )

        dirtyCorpus = dirtyCorpus.replace( '&amp;c.', ' ' ). \
            replace( '&amp;', ' ' ).replace( '&lt', ' ' ). \
            replace( '&gt', ' ' ).replace( r"\\", " " ).replace( '/', ' ' ).replace( '(', '' ).replace( ')',
                                                                                                        '' ).replace(
            '"', '' )

        regexTasks = [
            (r'(\w)\^(\w)', r'\1\2', lambda: cleanCorpus, "clean"),

            (r'([^-+])--([^-+])', r'\1 \2', lambda: corpus, "clean" ),

            (r'(\w)- (\w)', r'\1-\2', lambda: corpus, "clean" ),

            (r'\+-+?|-+\+|(-\s?){2,}', r' ', lambda: corpus, "clean" ),

            (r'\[[=)\']?(\w)[.]?\]', r'\1', lambda: corpus, "clean"),

            (r'[\]\[\}\{]', r' ', lambda: corpus, "clean"),

            (r'(\s?\.\s*){2,}', r' ', lambda: corpus, "clean"),

            (r'\s+', r' ', lambda: corpus, "clean"),

            (r'\n{4}.+\n{4}(?:.+\n{4})?', r' ', lambda: dirtyCorpus, "dirty"),

            (r'(\w)-\s{2,}(\w)', r'\1\2', lambda: corpus, "dirty" ),

            (r'(\s?\.\s*){2,}', r' ', lambda: corpus, "dirty"),

            (r'-{3,}', r' ', lambda: corpus, "dirty"),

            (r'\s+', r' ', lambda: corpus, "dirty" ),

        ]

        updated_corpora = dict( )
        taskNum = 0

        for ((corpus, n), Type) in map( lambda argLst: (regex.subn( *argLst[ 0 ] ), argLst[ 1 ]),
                                        map( lambda T: [ (T[ 0 ], T[ 1 ], T[ 2 ]( )), T[ 3 ] ], regexTasks ) ):
            updated_corpora[ Type ] = corpus

            if _DEBUG:
                print(
                    "substituted {0} of {1} in {2} corpus".format( n, regexTasks[ taskNum ][ 0 ], Type ) )
                taskNum += 1
                sys.stdout.flush( )

        return updated_corpora


class Manager( BaseManager ):
    @classmethod
    def generateInstance( cls, **kwargs ):
        for item in kwargs.items( ):
            cls.register( item[ 0 ], item[ 1 ] )
        instance = cls( )
        instance.start( )
        return instance


def isErrOrdinal( stringArg ):
    ord_pattern = r'^((\w{1,3})(?:th|st|nd|rd)[=+,.\'\";:\-]?)|(\woo[o]*\w)$'
    rx = regex.compile( ord_pattern )
    return bool( rx.match( stringArg ) )


def isStrOrdinal( stringArg ):
    ord_pattern = r'^\d+(?:th|st|nd|rd)?$'
    rx = regex.compile( ord_pattern )
    return bool( rx.match( stringArg ) )


def getAspellChecker( ):
    return SpellChecker( "en_US" )


def constructErrorRegex( Error, Context ):
    LEFTCONTEXT = 0
    RIGHTCONTEXT = 1

    LeftContext = regex.escape( Context[ LEFTCONTEXT ].lstrip( ) )

    RightContext = regex.escape( Context[ RIGHTCONTEXT ].rstrip( ) )

    minMaxLen = r"{" + str( int( len( Error ) * (1 / 2) ) ) + r"," + str( math.ceil( len( Error ) * 1.8 ) ) + r"}"

    fullPattern = r"(?:(?:" + LeftContext + r"){1s+1i+1d<=7})(?=." + minMaxLen + r"(?:(?:" + RightContext + "){" \
                                                                                                            "1s+1i+1d<=6}))" + \
                  r"(?P<errorMatch>(?:\w++[\-\']?\w*+)(?:(?=(?:" + RightContext + r"){1s+1i+1d<=6})|\W{1,2}))+?" + \
                  r"(?:(?:" + RightContext + "){1s+1i+2d<=6})"

    return regex.compile( fullPattern, regex.BESTMATCH | regex.V1 )


def constructSplitErrorRegex( Error, Context, nextError ):
    LEFTCONTXT = 0
    RIGHTCONTXT = 1

    LeftContext = regex.escape( Context[ LEFTCONTXT ].lstrip( ) )
    RightContext = regex.escape( nextError.Context[ RIGHTCONTXT ].rstrip( ) )

    minMaxLen = r"{" + str( int( len( Error ) * (1 / 2) ) ) + r"," + str(
        math.ceil( len( Error + nextError.Error ) * 1.8 ) ) + r"}"

    fullContext = r"(?:(?:" + LeftContext + r"){1s+1i+1d<=7})(?=." + minMaxLen + r"(?:(?:" + RightContext + "){" \
                                                                                                            "1s+1i+1d<=6}))" + \
                  r"(?P<errorMatch>(?:\w++[\-\']?\w*+)(?:(?=(?:" + RightContext + r"){1s+1i+1d<=6})|\W{1,2}))+?" + \
                  r"(?:(?:" + RightContext + "){1s+1i+2d<=6})"

    rxContextPattern = regex.compile( fullContext, regex.BESTMATCH | regex.V1 )

    return rxContextPattern


class _BASE( object ):
    def __hash__( self ):
        return self.ID


    def __eq__( self, other ):
        return not (self.ID - other.ID)


    def __ne__( self, other ):
        return not self.__eq__( other )


_OCRalignment = namedtuple( 'Alignment', [ 'intended_Word', 'OCR_Error', 'OCR_Context', \
                                           'TrueContext', 'ID', 'Type' ] )


class OCRalignment( _BASE, _OCRalignment ):
    def __str__( self ):
        mapping = "({intended}:{error})".format( intended = self.intended_Word, error = self.OCR_Error )
        if 'SPLITDICT' in self.Type:
            output = """{dirtyL}<{mapping}>\t{dirtyR} [{Type}]\n""". \
                format( dirtyL = self.OCR_Context[ 0 ], dirtyR = self.OCR_Context[ 1 ], mapping = mapping,
                        Type = self.Type )
        else:
            output = """{cleanL}<{mapping}>\t{cleanR} [{Type}]\n{dirtyL}<{mapping}>\t{dirtyR} [{Type}]\n""". \
                format( cleanL = self.TrueContext[ 0 ], cleanR = self.TrueContext[ 1 ],
                        dirtyL = self.OCR_Context[ 0 ], dirtyR = self.OCR_Context[ 1 ], mapping = mapping,
                        Type = self.Type )

        return output


_ErrorContext = namedtuple( 'ErrorContext', [ "Error", "Context", "Position", "ID" ] )


class ErrorContext( _BASE, _ErrorContext ):
    LAST_ERROR = -1
    LCONTEXT_SIZE = 25
    RCONTEXT_SIZE = 21


    def __str__( self ):
        return "({0}<{1}>{2})\t\t{3}".format( self.Context[ 0 ], self.Error, self.Context[ 1 ], self.Position )


def printProgress( totalItems, numComplete ):
    if numComplete == (totalItems // 4):
        print( "\t{0} - completed 25%".format( os.getpid( ) ) )
        sys.stdout.flush( )
    elif numComplete == (totalItems // 2):
        print( "\t{0} - completed 50%".format( os.getpid( ) ) )
        sys.stdout.flush( )
    elif numComplete == int( (3 / 4) * totalItems ):
        print( "\t{0} - completed 75%".format( os.getpid( ) ) )
        sys.stdout.flush( )
    elif not numComplete % 100:
        print( "\t{0} - completed {1}".format( os.getpid( ), numComplete ) )
        sys.stdout.flush( )
