__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '9/27/14'

import pickle
import os
import gc
from itertools import zip_longest
import multiprocessing

import regex
from nltk.util import ngrams

from ParallelGlobal import parallelCorpora


def errorModelComponents( ):
    with open( 'PickledData/HMM_data/outputs_FIXED1.pickle', 'rb' ) as pklfile:
        ConfusionMatrix = pickle.load( pklfile )

    with open( '/home/jcavalie/Britannica11/fullclean11/allclean.txt', 'r', encoding = 'ISO-8859-15' ) as file:
        _fstr = file.read( )

    cleanstr = parallelCorpora._normalize( _fstr, '' )[ 'clean' ]

    print( len( ConfusionMatrix.conditions( ) ) )
    for cond in ConfusionMatrix.conditions( ):
        alpha = cleanstr.count( cond )

        #errors in the alignment process could result in
        #the number of times X appears in clean text to be
        #less than number of times X was corrupted in OCR text;
        #FUDGE_FACTOR gives partial count to correct for this

        FUDGE_FACTOR=0.25
        if alpha - ConfusionMatrix[ cond ].N( ) < 0:
            print( "WARNING: alpha {0} , N {1}, Cond [{2}]".format( alpha, ConfusionMatrix[ cond ].N( ), cond ) )
            ConfusionMatrix[ cond ][ cond ] = FUDGE_FACTOR

        else:
            ConfusionMatrix[ cond ][ cond ] += (alpha - ConfusionMatrix[ cond ].N( ))

    print( "pickling data" )
    with open( 'PickledData/HMM_data/outputs_FIXED1_stage1.pickle', 'wb' ) as pklfile:
        pickle.dump( ConfusionMatrix, pklfile, pickle.HIGHEST_PROTOCOL )

    return


def adjustOutputsModel( textFolder ):
    with open( 'PickledData/HMM_data/outputs_FIXED1_stage1.pickle', 'rb' ) as file:
        emissions = pickle.load( file )

    directory = "/home/jcavalie/NLPtools/wiki_dump/" + textFolder + '/'
    print( 'Directory:', directory )

    wikiFiles = os.listdir( directory )
    print( 'Files:', wikiFiles )
    count = 0
    for fileName in wikiFiles:
        print( "file count: ", count )
        count += 1

        with open( directory + fileName, 'r', encoding = "ISO-8859-15" ) as file:
            text_ = file.read( )

        text_ = text_.replace( "-", " " )
        text_ = parallelCorpora._normalize( text_, "" )[ 'clean' ]

        text_ = text_.strip( )

        text_ = text_.replace( "''", " " )

        pattern = r'([~`!@#$%&|*)(_+=\\^\]\[}{;:"><.,/?]+)'

        text_, num = regex.subn( pattern, ' ', text_ )

        print( "removed unwanted chars: ", num )
        text_ = regex.sub( r"(\d+)", " ", text_ )
        text_ = regex.sub( r'(\s+)', ' ', text_ )

        text_ = ' ' + text_ + ' '

        gc.collect( )

        print( "building Ngrams" )

        corporaLength = len( text_ )
        print( "CORPUS LENGTH: ", corporaLength )
        counter = 0

        print( "starting loop" )
        for one_grams, two_grams, three_grams in zip_longest( ngrams( text_, 1 ), ngrams( text_, 2 ),
                                                              ngrams( text_, 3 ) ):
            counter += 1
            if not (counter) % 1000:
                print( "1000 more complete", counter )

            if counter == corporaLength // 4:
                print( "~1/4 complete" )
            elif counter == corporaLength // 2:
                print( "~1/2 complete" )
            elif counter == int( corporaLength * (3 / 4) ):
                print( "~3/4 complete" )

            if one_grams is not None:
                if emissions[ ''.join( one_grams ) ].get(''.join( one_grams ),None ) is None:
                    N1 = emissions[ ''.join( one_grams ) ].N( )
                    # print( 'one_gram:[{0}]'.format( ''.join( one_grams ) ) )
                    emissions[ ''.join( one_grams ) ][ ''.join( one_grams ) ] += \
                        text_.count( ''.join( one_grams ) ) - N1

                    if emissions[ ''.join( one_grams ) ][ ''.join( one_grams ) ] < 0:
                        emissions[ ''.join( one_grams ) ][ ''.join( one_grams ) ]=0

            if two_grams is not None:
                if emissions[ ''.join( two_grams ) ].get(''.join( two_grams ),None ) is None:
                    N2 = emissions[ ''.join( two_grams ) ].N( )
                    # print( 'two_gram:[{0}]'.format( ''.join( two_grams ) ) )
                    emissions[ ''.join( two_grams ) ][ ''.join( two_grams ) ] += \
                        text_.count( ''.join( two_grams ) ) - N2

                    if emissions[ ''.join( two_grams ) ][ ''.join( two_grams ) ] < 0:
                        emissions[ ''.join( two_grams ) ][ ''.join( two_grams ) ]=0

            if three_grams is not None:
                if emissions[ ''.join( three_grams ) ].get(''.join( three_grams ),None ) is None:
                    N3 = emissions[ ''.join( three_grams ) ].N( )
                    # print( 'three_gram:[{0}]'.format( ''.join( three_grams ) ) )
                    emissions[ ''.join( three_grams ) ][ ''.join( three_grams ) ] += text_.count(
                        ''.join( three_grams ) ) - N3

                    if emissions[ ''.join( three_grams ) ][ ''.join( three_grams ) ] < 0:
                        emissions[ ''.join( three_grams ) ][ ''.join( three_grams ) ]=0

    with open( 'PickledData/HMM_data/outputs_FIXED1_final.pickle', 'wb' ) as file:
        pickle.dump( emissions, file, pickle.HIGHEST_PROTOCOL )


# import sys
# from collections import defaultdict
#
#
# def _computeFertilities( job ):
#     count = job[ 0 ]
#     if count % 100:
#         print( 'working on:', count )
#         sys.stdout.flush( )
#
#     items = job[ 1 ]
#     state = items[ 0 ]
#     freqDist = items[ 1 ]
#
#     fertility = defaultdict( int )
#
#     for sample in freqDist.keys( ):
#
#         for conditions in OutputsModel.conditions( ):
#
#             fertility[ sample ] += bool( OutputsModel[ conditions ][ sample ] )
#     return state, fertility
#
#
# def _computeNumUniqueMappings( ):
#     B = 0
#     for freqDist in OutputsModel.values( ):
#         B += freqDist.B( )
#     return B
#
#
# def _KNcomponents( freqdist ):
#     N1 = freqdist.Nr( r = 1 )
#     N2 = freqdist.Nr( r = 2 )
#     N3 = freqdist.Nr( r = 3 )
#     N4 = freqdist.Nr( r = 4 )
#     return N1, N2, N3, N4
#
#
# def computeEmissionFertilites( ):
#     with open( 'PickledData/HMM_data/outputsXL_adjusted.pickle', 'rb' ) as pklfile:
#         global OutputsModel
#         OutputsModel = pickle.load( pklfile )
#         print( len( OutputsModel ) )
#         sys.stdout.flush( )
#
#     with multiprocessing.Pool( 4 ) as processPool1:
#         components = processPool1.map( _KNcomponents, OutputsModel.values( ) )
#
#     processPool1.join( )
#     print( "after first job" )
#     sys.stdout.flush( )
#
#     # with multiprocessing.Pool( 1 ) as processPool2:
#     # mappingBins = processPool2.apply( _computeNumUniqueMappings )
#     #
#     # processPool2.join( )
#     # print( "after computing bins" )
#     # sys.stdout.flush( )
#
#     # state_fertilityDict = dict( )
#     #
#     # print( "waiting before for loop" )
#     # sys.stdout.flush( )
#     # for state, fertility in fertilities:
#     #     state_fertilityDict[ state ] = fertility
#     N1 = 0
#     N2 = 0
#     N3 = 0
#     N4 = 0
#     for T in components:
#         N1 += T[ 0 ]
#         N2 += T[ 1 ]
#         N3 += T[ 2 ]
#         N4 += T[ 3 ]
#     print( "after for loop" )
#     print( "N1 {} N2 {} N3 {} N4 {}".format( N1, N2, N3, N4 ) )
#     sys.stdout.flush( )
#
#     with open( 'PickledData/KNcomponents.pickle', 'wb' ) as pklfile:
#         pickle.dump( (N1, N2, N3, N4), pklfile, pickle.HIGHEST_PROTOCOL )
#
#     print( "goodbye" )
#     sys.stdout.flush( )
#     return


if __name__ == '__main__':
    print( "starting" )
    errorModelComponents();
    print("finished errorModelCompents")
    adjustOutputsModel("Brit11")
    print( "finished" )