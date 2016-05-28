import os
import gc
import pickle
from itertools import zip_longest

from nltk.probability import ConditionalFreqDist
from nltk.util import ngrams
import regex

from ParallelGlobal import parallelCorpora


def cleanhtml( raw_html ):
    cleantext = regex.sub( r'<.*?>', '', raw_html )

    return cleantext


#
# def validChar( char ) :
# if (char <= 122 and char >= 97) or (char <= 90 and char >= 65) \
# or (char == 39) or (char == 45) :
# return True
# else :
# return False


def buildNgrams( textFolder ):
    bigram1_1 = ConditionalFreqDist( )
    bigram2_2 = ConditionalFreqDist( )
    bigram3_3 = ConditionalFreqDist( )
    bigram1_2 = ConditionalFreqDist( )
    bigram1_3 = ConditionalFreqDist( )
    bigram2_1 = ConditionalFreqDist( )
    bigram2_3 = ConditionalFreqDist( )
    bigram3_1 = ConditionalFreqDist( )
    bigram3_2 = ConditionalFreqDist( )

    directory = "/home/jcavalie/NLPtools/wiki_dump/" + textFolder + '/'
    print( 'Directory:', directory )

    wikiFiles = os.listdir( directory )
    print( 'Files:', wikiFiles )
    count = 0
    for fileName in wikiFiles:
        print( "file count: ", count )
        count += 1

        with open( directory + fileName, 'r', encoding = "ISO-8859-15" ) as file:
            if 'wiki' in textFolder:
                text_ = cleanhtml( file.read( ) )
            else:
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
        for one_grams, two_grams, three_grams, four_grams, five_grams, six_grams in \
                zip_longest( ngrams( text_, 1 ), ngrams( text_, 2 ),
                             ngrams( text_, 3 ), ngrams( text_, 4 ),
                             ngrams( text_, 5 ),
                             ngrams( text_, 6 ) ):
            counter += 1
            if not (counter) % 1000000:
                print( "1000000 more complete", counter )

            if counter == corporaLength // 4:
                print( "~1/4 complete" )
            elif counter == corporaLength // 2:
                print( "~1/2 complete" )
            elif counter == int( corporaLength * (3 / 4) ):
                print( "~3/4 complete" )

            if two_grams is not None:
                bigram1_1[ ''.join( two_grams[ :1 ] ) ][ ''.join( two_grams[ 1: ] ) ] += 1

            if three_grams is not None:
                bigram1_2[ ''.join( three_grams[ :1 ] ) ][ ''.join( three_grams[ 1: ] ) ] += 1
                bigram2_1[ ''.join( three_grams[ :2 ] ) ][ ''.join( three_grams[ 2: ] ) ] += 1

            if four_grams is not None:
                bigram2_2[ ''.join( four_grams[ :2 ] ) ][ ''.join( four_grams[ 2: ] ) ] += 1
                bigram3_1[ ''.join( four_grams[ :3 ] ) ][ ''.join( four_grams[ 3: ] ) ] += 1
                bigram1_3[ ''.join( four_grams[ :1 ] ) ][ ''.join( four_grams[ 1: ] ) ] += 1

            if five_grams is not None:
                bigram3_2[ ''.join( five_grams[ :3 ] ) ][ ''.join( five_grams[ 3: ] ) ] += 1
                bigram2_3[ ''.join( five_grams[ :2 ] ) ][ ''.join( five_grams[ 2: ] ) ] += 1

            if six_grams is not None:
                bigram3_3[ ''.join( six_grams[ :3 ] ) ][ ''.join( six_grams[ 3: ] ) ] += 1

    print( "finished building, begin pickling" )
    CORPUS = textFolder
    with open( './PickledData/langModels/bigrams1_1' + CORPUS + '.pickle', 'wb' ) as file1:
        pickle.dump( bigram1_1, file1, pickle.HIGHEST_PROTOCOL )

    del bigram1_1

    print( "finished 1-1" )
    with open( './PickledData/langModels/bigrams2_2' + CORPUS + '.pickle', 'wb' ) as file2:
        pickle.dump( bigram2_2, file2, pickle.HIGHEST_PROTOCOL )

    del bigram2_2

    print( "finished 2-2" )
    with open( './PickledData/langModels/bigrams3_3' + CORPUS + '.pickle', 'wb' ) as file3:
        pickle.dump( bigram3_3, file3, pickle.HIGHEST_PROTOCOL )

    del bigram3_3
    gc.collect( )

    print( "finished 3-3" )
    with open( './PickledData/langModels/bigrams1_2' + CORPUS + '.pickle', 'wb' ) as file4:
        pickle.dump( bigram1_2, file4, pickle.HIGHEST_PROTOCOL )

    del bigram1_2

    print( "finished 1-2" )
    with open( './PickledData/langModels/bigrams1_3' + CORPUS + '.pickle', 'wb' ) as file5:
        pickle.dump( bigram1_3, file5, pickle.HIGHEST_PROTOCOL )

    del bigram1_3
    gc.collect( )

    print( "finished 1-3" )
    with open( './PickledData/langModels/bigrams2_1' + CORPUS + '.pickle', 'wb' ) as file6:
        pickle.dump( bigram2_1, file6, pickle.HIGHEST_PROTOCOL )

    del bigram2_1

    print( "finished 2-1" )
    with open( './PickledData/langModels/bigrams2_3' + CORPUS + '.pickle', 'wb' ) as file7:
        pickle.dump( bigram2_3, file7, pickle.HIGHEST_PROTOCOL )

    del bigram2_3

    print( "finished 2-3" )
    with open( './PickledData/langModels/bigrams3_1' + CORPUS + '.pickle', 'wb' ) as file8:
        pickle.dump( bigram3_1, file8, pickle.HIGHEST_PROTOCOL )

    del bigram3_1

    print( "finished 3-2" )
    with open( './PickledData/langModels/bigrams3_2' + CORPUS + '.pickle', 'wb' ) as file9:
        pickle.dump( bigram3_2, file9, pickle.HIGHEST_PROTOCOL )

    del bigram3_2
    gc.collect( )

    print( "finished all" )

    return


if __name__ == '__main__':
    buildNgrams( 'Brit11' )