__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '6/23/14'

import os
import pickle
import gc
import string
from collections import deque
import math
from difflib import SequenceMatcher

import regex
from nltk.probability import ConditionalFreqDist

from ParallelGlobal import OCRalignment



# (r"[\~\`\!\@\$\^\&\*\)\(\_\+\=\}\{\]\[\|\"\;\:\?\/\.\,\%\<\>\\]",'')
# (r"(\d+)","#")
def regexSubstitute( string_ ):
    regexTasks = [ (r"(\s+)", " ") ]

    for task in regexTasks:
        string_ = regex.sub( task[ 0 ], task[ 1 ], string_ )
    return string_


def hasPunkt( string_ ):
    punkt = r"[|]"
    return True if regex.search( punkt, string_ ) is not None else False


def hasNonWordChars( string_ ):
    nonWordChars = r"[@$%\^&*)(=+\]\[{}|\\><`~#/]"
    return True if regex.search( nonWordChars, string_ ) is not None else False


def removePunctBigrams( ):
    with open( 'PickledData/langModels/britOnly/transitionsB.pickle', 'rb' ) as file:
        masterBigram = pickle.load( file )

    masterBigram_noPunkt = ConditionalFreqDist( )

    for condition, freqDist in masterBigram.items( ):

        for sample, numOutcomes in freqDist.items( ):

            sample = regexSubstitute( sample )
            condition = regexSubstitute( condition )

            if sample and condition:
                masterBigram_noPunkt[ condition ][ sample ] += numOutcomes

    print( "finished, dumping Master ..." )

    with open( './PickledData/langModels/britOnly/transitionsB1.pickle', 'wb' ) as output:
        pickle.dump( masterBigram_noPunkt, output, pickle.HIGHEST_PROTOCOL )


def combineCharBigrams( ):
    masterBigram = ConditionalFreqDist( )

    langModelDir = './PickledData/langModels/BritWikiCharBigram/'
    PklBigrams = os.listdir( langModelDir )

    for bigramFile in PklBigrams:
        print( "working on: ", bigramFile )

        with open( langModelDir + bigramFile, 'rb' ) as input_:

            bigram = pickle.load( input_ )

        for condition, freqDist in bigram.items( ):

            for sample, numOutcomes in freqDist.items( ):

                sample = regexSubstitute( sample )

                condition = regexSubstitute( condition )

                masterBigram[ condition ][ sample ] += numOutcomes

        print( "finished with ", bigramFile )

        del bigram
        gc.collect( )

    print( "dumping Master ..." )

    with open( './PickledData/langModels/BritWikiCharBigram/fullMasterBigramBritWiki.pickle', 'wb' ) as output:
        pickle.dump( masterBigram, output, pickle.HIGHEST_PROTOCOL )

    print( "finished dumping Master" )
    return


def prune_alignments( ):
    with open( 'PickledData/parallelWordMappingsV2_3.pickle', 'rb' ) as pklAlignments2_3, \
            open( 'PickledData/parallelWordMappingsV1.pickle', 'rb' ) as pklAlignments1, \
            open( 'PickledData/parallelWordMappingsV4.pickle', 'rb' ) as pklAlignments4, \
            open( 'PickledData/parallelWordMappingsV5_17.pickle', 'rb' ) as pklAlignments5_17, \
            open( 'PickledData/parallelWordMappings_sharedSetV5_17.pickle', 'rb' ) as pklsharedSet:
        alignments1 = pickle.load( pklAlignments1 )
        alignments2_3 = pickle.load( pklAlignments2_3 )
        alignments4 = pickle.load( pklAlignments4 )
        alignments5_17 = pickle.load( pklAlignments5_17 )
        shared_set = pickle.load( pklsharedSet )

    alignments = deque( )
    alignments.extend( alignments1 )
    alignments.extend( alignments2_3 )
    alignments.extend( alignments4 )
    alignments.extend( alignments5_17 )

    regexTasks = [ ("\n", ""), ]
    regexCleanTasks = [ (r"[:;?!,]", ""), (r"[\-]", " "), ]
    regexAllTasks = [ ]
    LEFTCONTEXT = 0
    RIGHTCONTEXT = 1

    cleaned_alignments = deque( )
    pruned = deque( )
    ordinals = deque( )
    nonWords = deque( )

    wordChars = string.ascii_lowercase + string.digits + "'-"

    print( "beginning pruning process" )

    for alignment in alignments:
        pruneItem = True
        PRUNE = False

        if alignment is not None and alignment not in shared_set:

            intended_Word = alignment.intended_Word.strip( )
            OCR_Error = alignment.OCR_Error.strip( )
            TrueContext = alignment.TrueContext
            OCR_Context = alignment.OCR_Context

            trueLeft = TrueContext[ LEFTCONTEXT ]
            trueRight = TrueContext[ RIGHTCONTEXT ]
            OCRLeft = OCR_Context[ LEFTCONTEXT ]
            OCRRight = OCR_Context[ RIGHTCONTEXT ]

            if 'greek' in intended_Word:
                PRUNE = True

            if not PRUNE:

                for task in regexTasks:
                    intended_Word = regex.sub( task[ 0 ], task[ 1 ], intended_Word )
                    OCR_Error = regex.sub( task[ 0 ], task[ 1 ], OCR_Error )


                # if intended_Word[-1] in string.punctuation and OCR_Error[-1] in string.punctuation \
                # and intended_Word[-1] == OCR_Error[-1]:
                #     intended_Word=intended_Word[:-1]
                #     OCR_Error=OCR_Error[:-1]
                #
                # elif intended_Word[-1] in string.punctuation and OCR_Context[RIGHTCONTEXT].split()[0][0] \
                #     in  string.punctuation:
                #
                #     intended_Word=intended_Word[:-1]
                #
                #
                #
                # if intended_Word[0] in string.punctuation and OCR_Error[0] in string.punctuation \
                #     and intended_Word[0] == OCR_Error[0]:
                #     intended_Word=intended_Word[1:]
                #     OCR_Error=OCR_Error[1:]
                #
                # elif intended_Word[0] in string.punctuation and OCR_Context[LEFTCONTEXT].split()[-1][-1] \
                #     in  string.punctuation:
                #
                #     intended_Word=intended_Word[1:]

                intended_Word = intended_Word.strip( '!"$%&\'()*+,-./:;<=>?@[\\]^_`{|}~#' )
                OCR_Error = OCR_Error.strip( '!"$%&\'()*+,-./:;<=>?@[\\]^_`{|}~#' )

                if (TrueContext[ RIGHTCONTEXT ] and OCR_Context[ RIGHTCONTEXT ]) and \
                        (TrueContext[ LEFTCONTEXT ] and OCR_Context[ LEFTCONTEXT ]):

                    rightAdj_Trueword = TrueContext[ RIGHTCONTEXT ].split( )[ 0 ]
                    rightAdj_Trueword = rightAdj_Trueword.rstrip( ".,?;:" )
                    rightAdj_OCRword = OCR_Context[ RIGHTCONTEXT ].split( )[ 0 ]
                    rightAdj_OCRword = rightAdj_OCRword.rstrip( ".,?;:" )

                    leftAdj_Trueword = TrueContext[ LEFTCONTEXT ].split( )[ -1 ]
                    leftAdj_OCRword = OCR_Context[ LEFTCONTEXT ].split( )[ -1 ]

                    if rightAdj_OCRword != rightAdj_Trueword and \
                            (((OCR_Error.find( rightAdj_Trueword, -len( rightAdj_Trueword ) ) != -1) and
                                      intended_Word.find( rightAdj_Trueword, -len( rightAdj_Trueword ) ) == -1) or

                                 (((len( OCR_Error ) - len( intended_Word )) == len( rightAdj_Trueword )) and
                                          SequenceMatcher( autojunk = False,
                                                           a = OCR_Error[ -len( rightAdj_Trueword ): ],
                                                           b = rightAdj_Trueword ).ratio( ) > 0.61)):

                        intended_Word = intended_Word + ' ' + rightAdj_Trueword

                        trueRight = TrueContext[ RIGHTCONTEXT ][ TrueContext[ RIGHTCONTEXT ]. \
                                                                     find( rightAdj_Trueword ) + len(
                            rightAdj_Trueword ): ]

                    if TrueContext[ LEFTCONTEXT ][ -1 ] in wordChars or \
                                    OCR_Context[ LEFTCONTEXT ][ -1 ] in wordChars:

                        if abs( len( leftAdj_OCRword ) - len( leftAdj_Trueword ) ) < 3:

                            intended_Word = leftAdj_Trueword + intended_Word
                            OCR_Error = leftAdj_OCRword + OCR_Error

                            trueLeft = TrueContext[ LEFTCONTEXT ] \
                                [ :TrueContext[ LEFTCONTEXT ].rfind( leftAdj_Trueword ) ]

                            OCRLeft = OCR_Context[ LEFTCONTEXT ] \
                                [ :OCR_Context[ LEFTCONTEXT ].rfind( leftAdj_OCRword ) ]

                if (alignment.Type == 'SPLITDICT-R') or (alignment.Type == 'SPLITDICT-L'):

                    errWords = OCR_Error.split( )

                    if ''.join( errWords ) == intended_Word:

                        if alignment.Type == 'SPLITDICT-R':
                            splitR = errWords[ -1 ]

                            OCRRight = OCR_Context[ RIGHTCONTEXT ] \
                                [ (OCR_Context[ RIGHTCONTEXT ].find( splitR ) + len( splitR )): ]

                            trueRight = OCRRight
                            trueLeft = OCRLeft

                        if alignment.Type == 'SPLITDICT-L':
                            splitL = errWords[ 0 ]
                            OCRLeft = OCR_Context[ LEFTCONTEXT ][ :OCR_Context[ LEFTCONTEXT ].rfind( splitL ) ]
                            trueLeft = OCRLeft
                            trueRight = OCRRight
                    else:
                        PRUNE = True


                elif alignment.Type == 'SPLITDICT':
                    trueLeft = OCRLeft
                    trueRight = OCRRight

            if 'greek' in intended_Word:
                PRUNE = True

            if not PRUNE:
                if math.floor( len( OCR_Error ) / 1.2 ) <= len( intended_Word ) <= math.ceil(
                                len( OCR_Error ) * 1.256 ):


                    if regex.search( r"(\d)", intended_Word ):

                        intended_Word = regexSubstitute( intended_Word )

                        ordinal = OCRalignment( intended_Word.strip( ), OCR_Error.strip( ), (OCRLeft, OCRRight),
                                                (trueLeft, trueRight), alignment.ID, alignment.Type )

                        ordinals.append( ordinal )

                        pruneItem = False

                    elif hasNonWordChars( intended_Word ):

                        # intended_Word=regexSubstitute(intended_Word)

                        nonWord = OCRalignment( intended_Word.strip( ), OCR_Error.strip( ), (OCRLeft, OCRRight),
                                                (trueLeft, trueRight), alignment.ID, alignment.Type )

                        nonWords.append( nonWord )

                        pruneItem = False

                    elif SequenceMatcher( a = intended_Word, b = OCR_Error, autojunk = False ).ratio( ) > .27:

                        for task in regexCleanTasks:
                            intended_Word = regex.sub( task[ 0 ], task[ 1 ], intended_Word )

                        if alignment.Type == 'SPLIT' and \
                                        intended_Word.count( ' ' ) == OCR_Error.count( ' ' ) and \
                                        intended_Word.count( ' ' ) > 0:

                            intendedWords = intended_Word.split( )
                            errorWords = OCR_Error.split( )

                            for itr in range( len( intendedWords ) ):

                                intendedWords[ itr ] = regexSubstitute( intendedWords[ itr ] )
                                errorWords[ itr ] = regexSubstitute( errorWords[ itr ] )

                                cleaned = OCRalignment( intendedWords[ itr ].strip( ),
                                                        errorWords[ itr ].strip( ),

                                                        (OCRLeft + (' '.join( errorWords[ :itr ] )) + (
                                                            '' if not itr else ' '),
                                                         (' ' if itr < len( errorWords ) - 1 else '') +
                                                         (' '.join( errorWords[ itr + 1: ] ) + OCRRight)),

                                                        (trueLeft + (' '.join( intendedWords[ :itr ] )) + (
                                                            '' if not itr else ' '),
                                                         (' ' if itr < len( errorWords ) - 1 else '') +
                                                         (' '.join( intendedWords[ itr + 1: ] ) + trueRight)),

                                                        alignment.ID, 'SPLIT->REG' )

                                cleaned_alignments.append( cleaned )
                                pruneItem = False

                        else:
                            intended_Word = regexSubstitute( intended_Word )
                            OCR_Error = regexSubstitute( OCR_Error )

                            cleaned = OCRalignment( intended_Word.strip( ), OCR_Error.strip( ), (OCRLeft, OCRRight),
                                                    (trueLeft, trueRight), alignment.ID, alignment.Type )

                            cleaned_alignments.append( cleaned )
                            pruneItem = False

        if alignment and pruneItem:
            pruned.append( alignment )
            with open( "printedData/prunedAlignmentsV1_17.txt", 'a' ) as outputfile:
                outputfile.write( str( alignment ) + '\n' )

    print( "alignments count:", len( cleaned_alignments ) )
    print( "ordinals count:", len( ordinals ) )
    print( "nonWords count:", len( nonWords ) )
    print( "pruned count:", len( pruned ) )

    print( "printing updated alignments" )
    with open( 'printedData/all_wordMappings_taggedV1_17.txt', 'w' ) as outputfile:
        for item in cleaned_alignments:
            outputfile.write( str( item ) + '\n' )

    print( "pickling data" )
    with open( 'PickledData/all_wordMappings_taggedV1_17.pickle', 'wb' ) as pklfile:
        pickle.dump( cleaned_alignments, pklfile, pickle.HIGHEST_PROTOCOL )

    with open( 'PickledData/pruned_wordMappingstV1_17.pickle', 'wb' ) as pklfile:
        pickle.dump( pruned, pklfile, pickle.HIGHEST_PROTOCOL )

    with open( 'PickledData/ordinals_wordMappingstV1_17.pickle', 'wb' ) as pklfile:
        pickle.dump( ordinals, pklfile, pickle.HIGHEST_PROTOCOL )

    with open( 'PickledData/nonWords_wordMappingstV1_17.pickle', 'wb' ) as pklfile:
        pickle.dump( nonWords, pklfile, pickle.HIGHEST_PROTOCOL )

    print( "finished" )

    return


if __name__ == '__main__':
    print( "starting" )
    # prune_alignments()

    #combineCharBigrams()

    removePunctBigrams( )