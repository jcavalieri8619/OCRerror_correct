__author__ = 'jcavalie'

import Levenshtein


def alignChars( source, target, ErrStats = None, ErrStats_lock = None ):
    """
    alignChars takes a pair of words from parallel corpora that have been word aligned.
    Errors introduced by the noisy channel (OCR) are revealed by finding the sequence of edit operations that
    map source to target using Levenshtein Edit Distance module.  The edit sequence can
    be used to generate character alignments.

    @param source: original word from corrected corpora
    @type source: str
    @param target: OCR output word from uncorrected corpora
    @type target: str
    @return: source and target words represented character aligned in a
            list of tuples e.g. [(s_1,t_1),...,(s_n,t_n)]
    @rtype: list
    """

    editops = Levenshtein.editops( source, target )

    SPOS = 1
    TPOS = 2
    OP = 0

    sourceArray = [ char for char in source ]
    targetArray = [ char for char in target ]

    substituteCount = 0
    insertCount = 0
    deleteCount = 0

    for element in editops:
        if element[ OP ] == 'insert':
            sourceArray.insert( element[ TPOS ], '' )
            insertCount += 1
        if element[ OP ] == 'delete':
            targetArray.insert( element[ SPOS ], '' )
            deleteCount += 1
        if element[ OP ] == 'replace':
            substituteCount += 1

    if ErrStats:
        with ErrStats_lock:


            ErrStats.updateDistribution( 'editDist_correctLen', len( editops ), len( source ) )

            ErrStats.updateDistribution( 'editDist_errorLen', len( editops ), len( target ) )

            ErrStats.updateDistribution( 'errorLen_correctLen', len( target ), len( source ) )

            ErrStats.updateDistribution( 'errorLen_editDist', len( target ), len( editops ) )

            ErrStats.updateDistribution( 'errorLen_editOps', len( target ),
                                         (insertCount, deleteCount, substituteCount) )

            ErrStats.updateDistribution( 'errorLen_insertOp', len( target ), insertCount )

            ErrStats.updateDistribution( 'errorLen_deleteOp', len( target ), deleteCount )

            ErrStats.updateDistribution( 'errorLen_substituteOp', len( target ), substituteCount )

            ErrStats.updateDistribution( 'correctLen_editDist', len( source ), len( editops ) )

            ErrStats.updateDistribution( 'errorLens', len( target ) )

            ErrStats.updateDistribution( 'correctLens', len( source ) )

            ErrStats.updateDistribution( 'editDists', len( editops ) )

            ErrStats.updateDistribution( 'insertEdits', insertCount )

            ErrStats.updateDistribution( 'deleteEdits', deleteCount )

            ErrStats.updateDistribution( 'substituteEdits', substituteCount )

    output = [ w for w in zip( targetArray, sourceArray ) ]

    return output


if __name__ == '__main__':
    from locateErrorWindows import determineErrWindows
    from generateSubstringMappings import genSubstrMaps

    S='grenie'
    T="greni"
    print((S,T))
    rv = alignChars( S, T, None, None )
    rv, errwin = determineErrWindows( rv, None, None )
    mappings = genSubstrMaps( rv, errwin, False)
    print(errwin)
    print(rv)
    print( len( mappings ) )
    # print( mappings )
    for map_ in mappings:
        print( map_ )
