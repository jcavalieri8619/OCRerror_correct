__author__ = 'jcavalie'
import collections
import itertools
import copy

from substringMappingStructures import mappingContainer, mappingObject, subgroups


_TESTING = False

def padRightErrWin(posn,total_len):
    if posn == total_len-1:
        #if posn is last character then still need to
        #add 1 to account for range(frst,lst) to map to frst...lst-1
        return 1
    elif total_len - posn > 1:
        return 2


def genSubstrMaps( alignedChars, errorWindows, ErrStats = None ):
    '''

    @param alignedChars: min edit dist alignment of OCR errror and correction in form
                         [(errorChar,trueChar),...,(errorChar,trueChar)]
    @type alignedChars: list
    @param errorWindows: start and end positions of consecutive character errors; if
                         only single character error then start==end
    @type errorWindows: list
    @return:
    @rtype:
    '''

    training = bool( ErrStats )

    fullMappings = list( )

    if len( errorWindows ) == 0:
        return [ alignedChars ]

    mapObjects_DC = [ mappingObject( w[ 1 ], [ w[ 0 ] ] ) for w in enumerate( alignedChars ) ]
    mapObjects = copy.deepcopy( mapObjects_DC )

    partialMaps = collections.defaultdict( list )
    prev_win_ranges=[]

    for index, window in enumerate( errorWindows ):

        if index == 0:
            #first error win so no need to check ranges of prior
            #error windows when determining range
            if window[ 0 ] == 0:
                # if first error window starts at first character
                # then can't include prior characters
                windowRange = list( range( window[ 0 ], window[ 1 ] + padRightErrWin(window[1],len(alignedChars)) ) )


            #testing if including 2 prior chars in influence window is detrimental
            else:
            #elif window[ 0 ] == 1:
                #include 1 prior character
                windowRange = list( range( window[ 0 ] - 1, window[ 1 ] +  padRightErrWin(window[1],len(alignedChars)) ) )

            #else:
                #testing if including 2 prior chars in influence window is detrimental

                #include 2 prior chars
                #windowRange = list( range( window[ 0 ] - 2, window[ 1 ] +  padRightErrWin(window[1],
                # len(alignedChars)) ) )

        else:
            #given that other error windows are associated with portions
            #of the strings, need to prevent overlapping ranges by checking
            #where current window starts and prev window ends
            #if window[ 0 ] - prev_win_ranges[ -1 ][ -1 ] > 2:
                #testing if including 2 prior chars in influence window is detrimental
                #windowRange = list( range( window[ 0 ] - 2, window[ 1 ] +  padRightErrWin(window[1],
                # len(alignedChars)) ) )

            #elif
            if window[ 0 ] - prev_win_ranges[ index - 1 ][ -1 ] > 1:
                windowRange = list( range( window[ 0 ] - 1, window[ 1 ] +  padRightErrWin(window[1],len(alignedChars)) ) )
            else:
                windowRange = list( range( window[ 0 ], window[ 1 ] +  padRightErrWin(window[1],len(alignedChars)) ) )

        prev_win_ranges.append(windowRange)



        groupSet = set( )
        for grouping in subgroups( windowRange ):

            if training is True:
                new_grouping = [ ]
                for index_list in grouping:
                    if tuple( index_list ) not in groupSet:
                        new_grouping.append( index_list )
                        groupSet.add( tuple( index_list ) )
                if not new_grouping:
                    continue
            else:
                new_grouping = grouping

#this was in arg = [] after for indx in mapobj_indices but seems totally unnecessary;
#if no bug shows up then delete
#if indx < len( mapObjects_DC )

            arg = [ [ mapObjects_DC[ indx  ] for indx in mapobj_indicesList  ] for
                    mapobj_indicesList in new_grouping ]

            try:
                partialMaps[ index ].append( mappingContainer( arg, list( range( len( alignedChars ) ) ) ) )
            except ValueError as errmsg:
                continue

    if training is False:
        completeMaps = [ sum( W[ 1: ], W[ 0 ] ) for W in itertools.product( *list( partialMaps.values( ) ) ) ]

        for Map in completeMaps:
            for position in Map.positionsNeeded( ):
                Map.insertMapping( mapObjects[ position ] )
            Map.exportMapping( fullMappings )

    else:
        for containerList in partialMaps.values( ):
            for Map_container in containerList:
                Map_container.exportMapping( fullMappings )

    if _TESTING:
        with open( "printedData/alignmentPartitions.txt", 'w' ) as testout:
            for element in fullMappings:
                testout.write( str( element ) + '\n' )

    return fullMappings