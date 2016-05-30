__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '7/23/14'

from difflib import SequenceMatcher
from functools import partial
from collections import deque
import gc
import os
import string
import sys
import statistics

import regex

from ParallelGlobal import OCRalignment, constructSplitErrorRegex, \
    constructErrorRegex, ErrorContext, printProgress


_DEBUG = True


def initConsumer( ):
    global _CleanDirtyDiffs, _MostProbablePos, _CurrentCorpus
    _CleanDirtyDiffs = deque( )
    _MostProbablePos = None
    _CurrentCorpus = None
    print( "starting process:", os.getpid( ) )
    sys.stdout.flush( )


def _relativeToActual( matchPosition, slicePosObj ):
    if matchPosition < abs( slicePosObj[ 'LLpos' ] - slicePosObj[ 'LRpos' ] ):
        truePosition = slicePosObj[ 'LLpos' ] + matchPosition
    else:
        truePosition = slicePosObj[ 'RLpos' ] + abs(
            matchPosition - abs( slicePosObj[ 'LLpos' ] - slicePosObj[ 'LRpos' ] ) )

    return truePosition


def CD_avg( ):
    if not _CleanDirtyDiffs:
        return 0
    else:
        return statistics.mean( _CleanDirtyDiffs )


SimFunc = partial( SequenceMatcher, autojunk = False )


def makeConsumer( splitErrors_found, parallel_corpora, **kwargs ):
    def consumer( ErrorBundle, currCount, TotalErrors ):


        printProgress( TotalErrors, currCount )

        RIGHTCONTEXT = 1
        LEFTCONTEXT = 0
        global _MostProbablePos, _CurrentCorpus

        if not _CurrentCorpus:
            _CurrentCorpus = parallel_corpora.getCorpora( 'clean' )

        getFullMatch = lambda matchObject, name: "".join( matchObject.captures( name ) )

        OCRError, nextOCRError = ErrorBundle

        if _MostProbablePos is None:
            _MostProbablePos = CD_avg( ) + OCRError.Position

        if OCRError in splitErrors_found._getvalue( ):
            _MostProbablePos = CD_avg( ) + nextOCRError.Position
            splitErrors_found.remove( OCRError )
            return None

        Error, OCRContext = OCRError.Error, OCRError.Context

        Left = _CurrentCorpus.find( OCRContext[ 0 ].lstrip( ) )
        Right = _CurrentCorpus.find( OCRContext[ 1 ].rstrip( ) )
        SEARCHPOS = None

        if Left != -1 and Right != -1:
            if 0 < (Right - Left) < 88:
                SEARCHPOS = int( (Left + Right) / 2 )

        DO_REG_SEARCH = True

        if nextOCRError.ID != ErrorContext.LAST_ERROR and \
                        abs( OCRError.Position - nextOCRError.Position ) <= len( Error ) + 2:

            start = OCRContext[ RIGHTCONTEXT ].find( nextOCRError.Error[ 0 ] )
            ErrorSR = Error + OCRContext[ RIGHTCONTEXT ][ :start ] + nextOCRError.Error

            dictMatch = regex.search( r"(?P<match>^" + Error + nextOCRError.Error + r"$){1i<=1}",
                                      kwargs.get( 'WordList' ),
                                      regex.MULTILINE )
            if dictMatch:
                with kwargs.get( "splitErrors_lock" ):
                    splitErrors_found.add( nextOCRError )

                X = OCRalignment( dictMatch.group( 'match' ), ErrorSR,
                                  (OCRContext[ 0 ], nextOCRError.Context[ 1 ]), ("", ""),
                                  OCRError.ID, 'SPLITDICT' )

                _MostProbablePos = CD_avg( ) + nextOCRError.Position

                if _DEBUG:
                    with kwargs.get( "stream_lock" ):
                        with open( 'printedData/Enchant/matched.txt', 'a' ) as Aout:
                            Aout.write( str( X ) + '\n' )
                return X

            else:


                LeftS = _CurrentCorpus.find( OCRContext[ 0 ].lstrip( ) )
                RightS = _CurrentCorpus.find( nextOCRError.Context[ 1 ].rstrip( ) )
                SPLITSEARCHPOS = None

                if LeftS != -1 and RightS != -1:
                    if 0 < (RightS - LeftS) < 98:
                        SPLITSEARCHPOS = int( (LeftS + RightS) / 2 )

                rxSplitErrPattern = constructSplitErrorRegex( Error, OCRContext, nextOCRError )

                split_search_itr = 0

                split_search_max = 250
                splitMatches = [ ]
                countUpdate = False
                while split_search_itr < split_search_max:


                    corporaSliceObj = parallel_corpora.getCorporaSlice( "clean", (
                        SPLITSEARCHPOS if SPLITSEARCHPOS is not None else int( _MostProbablePos )),
                                                                        split_search_itr )

                    if not corporaSliceObj[ 'slice' ] and split_search_itr > 4:
                        break

                    matchObjSplitErr = rxSplitErrPattern.search( corporaSliceObj[ 'slice' ] )

                    split_search_itr += 1

                    if not matchObjSplitErr:

                        if not split_search_itr % 13:
                            regex.purge( )
                            gc.collect( )

                    else:

                        matchObjSplitErr.detach_string( )

                        splitMatches.append( (matchObjSplitErr, corporaSliceObj) )

                        if sum( matchObjSplitErr.fuzzy_counts, 0 ) < 4:
                            break

                        if not countUpdate:
                            if SPLITSEARCHPOS is not None:
                                split_search_max = split_search_itr
                            else:
                                split_search_max = split_search_itr + 14
                            countUpdate = True

                if splitMatches:

                    editDists = list( map( lambda arg: sum( arg[ 0 ].fuzzy_counts, 0 ), splitMatches ) )

                    correctMatch, SliceObj = splitMatches[ editDists.index( min( editDists ) ) ]

                    intendedWrdSR = getFullMatch( correctMatch, 'errorMatch' )

                    clean_context = (SliceObj[ 'slice' ][ correctMatch.spans( 'errorMatch' )[ 0 ][ 0 ] - 25: \
                        correctMatch.spans( 'errorMatch' )[ 0 ][ 0 ] ],
                                     SliceObj[ 'slice' ][ correctMatch.spans( 'errorMatch' )[ -1 ][ 1 ]: \
                                         correctMatch.spans( 'errorMatch' )[ -1 ][ 1 ] + 21 ])

                    CurrMatchPos = _relativeToActual( int( .5 * sum( correctMatch.span( ) ) ), SliceObj[ 'data' ] )

                    offset = CurrMatchPos - OCRError.Position

                    _CleanDirtyDiffs.append( offset )

                    _MostProbablePos = CD_avg( ) + nextOCRError.Position

                    with kwargs.get( "splitErrors_lock" ):
                        splitErrors_found.add( nextOCRError )

                    X = OCRalignment( intendedWrdSR, ErrorSR,
                                      (OCRContext[ 0 ], nextOCRError.Context[ 1 ]), clean_context, OCRError.ID,
                                      'SPLIT' )

                    if _DEBUG:
                        with kwargs.get( "stream_lock" ):
                            with open( 'printedData/Enchant/matched.txt', 'a' ) as Aout:
                                Aout.write( str( X ) + '\n' )
                    return X
                else:
                    DO_REG_SEARCH = False


        else:

            splitL = OCRContext[ 0 ].split( )
            if splitL:
                splitL = splitL[ -1 ]
            else:
                splitL = None

            splitR = OCRContext[ 1 ].split( )
            if splitR:
                splitR = splitR[ 0 ]
            else:
                splitR = None

            if splitR and splitR not in string.punctuation:

                _splitR = splitR if splitR[ -1 ] not in string.punctuation else splitR[ :-1 ]
                _splitR = r"(?P<match>^" + Error + regex.escape( _splitR ) + r"$)"

                dictMatchR = (regex.search( _splitR, kwargs.get( 'WordList' ), regex.MULTILINE ) if _splitR else None)

                if dictMatchR:


                    if OCRContext[ RIGHTCONTEXT ][ 0 ] == ' ':
                        SEP = ' '
                    else:
                        SEP = ''

                    X = OCRalignment( dictMatchR.group( 'match' ),
                                      Error + SEP + splitR,
                                      (OCRContext[ 0 ], OCRContext[ 1 ]), ('', ''),
                                      OCRError.ID, 'SPLITDICT-R' )

                    _MostProbablePos = CD_avg( ) + nextOCRError.Position

                    if _DEBUG:
                        with kwargs.get( "stream_lock" ):
                            with open( 'printedData/Enchant/matched.txt', 'a' ) as Aout:
                                Aout.write( str( X ) + '\n' )
                    return X

            if splitL and splitL not in string.punctuation:

                _splitL = splitL if splitL[ 0 ] not in string.punctuation else splitL[ 1: ]
                _splitL = r"(?P<match>^" + regex.escape( _splitL ) + Error + r"$)"

                dictMatchL = (regex.search( _splitL, kwargs.get( 'WordList' ), regex.MULTILINE ) if _splitL else None)

                if dictMatchL:

                    if OCRContext[ LEFTCONTEXT ][ -1 ] == ' ':
                        SEP = ' '
                    else:
                        SEP = ''
                    X = OCRalignment( dictMatchL.group( 'match' ), splitL + SEP + Error,
                                      (OCRContext[ 0 ], OCRContext[ 1 ]), ('', ''),
                                      OCRError.ID, 'SPLITDICT-L' )

                    _MostProbablePos = CD_avg( ) + nextOCRError.Position

                    if _DEBUG:
                        with kwargs.get( "stream_lock" ):
                            with open( 'printedData/Enchant/matched.txt', 'a' ) as Aout:
                                Aout.write( str( X ) + '\n' )
                    return X

        if DO_REG_SEARCH:

            rx = constructErrorRegex( Error, OCRContext )

            iteration = 0

            max_iteration = 250
            matches = [ ]
            countUpdate2 = False

            while iteration < max_iteration:


                corporaSliceObj = parallel_corpora.getCorporaSlice( "clean", (
                    SEARCHPOS if SEARCHPOS is not None else int( _MostProbablePos )),
                                                                    iteration )

                if not corporaSliceObj[ 'slice' ] and iteration > 4:
                    break

                matchObj = rx.search( corporaSliceObj[ 'slice' ] )

                iteration += 1

                if not matchObj:
                    if not iteration % 13:
                        regex.purge( )
                        gc.collect( )
                else:

                    matchObj.detach_string( )

                    matches.append( (matchObj, corporaSliceObj) )

                    if sum( matchObj.fuzzy_counts, 0 ) < 4:
                        break

                    if not countUpdate2:
                        if SEARCHPOS is not None:
                            max_iteration = iteration
                        else:
                            max_iteration = iteration + 14
                            countUpdate2 = True

            if matches:

                editDists = list( map( lambda arg: sum( arg[ 0 ].fuzzy_counts, 0 ), matches ) )

                correctMatch, SliceObj = matches[ editDists.index( min( editDists ) ) ]

                intendedWord = getFullMatch( correctMatch, 'errorMatch' )

                clean_context = (SliceObj[ 'slice' ][ correctMatch.spans( 'errorMatch' )[ 0 ][ 0 ] - 25: \
                    correctMatch.spans( 'errorMatch' )[ 0 ][ 0 ] ],
                                 SliceObj[ 'slice' ][ correctMatch.spans( 'errorMatch' )[ -1 ][ 1 ]: \
                                     correctMatch.spans( 'errorMatch' )[ -1 ][ 1 ] + 21 ])

                CurrMatchPos = _relativeToActual( int( .5 * sum( correctMatch.span( ) ) ), SliceObj[ 'data' ] )

                offset = CurrMatchPos - OCRError.Position

                _CleanDirtyDiffs.append( offset )

                _MostProbablePos = CD_avg( ) + nextOCRError.Position

                X = OCRalignment( intendedWord, Error, OCRContext, clean_context, OCRError.ID, 'REG' )

                if _DEBUG:
                    with kwargs.get( "stream_lock" ):
                        with open( 'printedData/Enchant/matched.txt', 'a' ) as Aout:
                            Aout.write( str( X ) + '\n' )
                return X

        with kwargs.get( "stream2_lock" ):
            with open( 'printedData/Enchant/unmatched.txt', 'a' ) as Uout:
                Uout.write( str( OCRError ) + "," + str( _MostProbablePos ) + '\n' )

        _MostProbablePos = CD_avg( ) + nextOCRError.Position

        return None


    makeConsumer.closure = consumer
    return




