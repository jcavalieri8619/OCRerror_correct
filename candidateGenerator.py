__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '8/13/14'

import string

import regex

from buildWordLangModel import NgramWordBreaker


_wordBreaker = NgramWordBreaker( )

with open( 'Dictionaries/BritDict_plus.txt', 'r' ) as file:
    Lexicon = file.read( )

LexiconDict = set( Lexicon.splitlines( ) )


def buildMergeCandidates( OCR_Error, OCR_Context ):
    # merge with preceding and succeeding words; inverse of splitL and splitR errors

    splitL = OCR_Context[ 0 ].split( )
    if splitL:
        splitL = splitL[ -1 ]
    else:
        splitL = None

    splitR = OCR_Context[ 1 ].split( )
    if splitR:
        splitR = splitR[ 0 ]
    else:
        splitR = None

    mergeCandidates = [ ]

    if splitR and splitR not in string.punctuation:

        splitR = splitR if splitR[ -1 ] not in string.punctuation else splitR[ :-1 ]
        mergeCandidates.append( OCR_Error + splitR )

    if splitL and splitL not in string.punctuation:

        splitL = splitL if splitL[ 0 ] not in string.punctuation else splitL[ 1: ]
        mergeCandidates.append( splitL + OCR_Error )

    return [ word for word in mergeCandidates if word in LexiconDict ]


def buildSplitCandidates( OCR_Error ):
    WORD_BREAKER_LEN = 17

    Splits = [ ]

    if len( OCR_Error ) < WORD_BREAKER_LEN:

        Splits.extend( [ (OCR_Error[ :i ] + ' ' + OCR_Error[ i: ]) for i in range( len( OCR_Error ) + 1 )
                         if (OCR_Error[ :i ] in LexiconDict) and (len( OCR_Error[ :i ] ) > 1)
                         and (OCR_Error[ i: ] in LexiconDict) and (len( OCR_Error[ i: ] ) > 1) ] )

    else:
        Splits.extend( _wordBreaker.breakWords( OCR_Error ) )

    return Splits


def generateCandidates( OCR_Error, OCR_Context, iteration, maxEditDist, editOps = None ):
    MIN_SPLIT_LEN = 27

    if editOps is not None:

        params = r"{i<=" + str( editOps[ 0 ] ) + r",d<=" + str( editOps[ 1 ] ) + r",s<=" + str(
            editOps[ 2 ] ) + r",e<=" + str( maxEditDist ) + r"}"

        candidatePattern = r"^(" + regex.escape( OCR_Error ) + r")" + params + r"$"

    else:

        candidatePattern = r"^(" + regex.escape( OCR_Error ) + r"){1i+1d+1s<=" + str( maxEditDist ) + r"}$"

    candidates = regex.findall( candidatePattern, Lexicon, regex.ASCII | regex.MULTILINE | regex.ENHANCEMATCH )

    if len( OCR_Error ) > MIN_SPLIT_LEN:
        candidates += buildSplitCandidates( OCR_Error )

    return set( candidates )


def generateAvgEditOpSeq( error_length ):
    pass

