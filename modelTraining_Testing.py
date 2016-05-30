__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '8/31/14'

import random
import pickle
import gc
import datetime
import statistics

import globalModelParameters
from HiddenMarkovModel import HiddenMarkovModelTrainer
from partitionStrAlignment import partitionStrAlignments
from ParallelOCRalign_Global import ErrorContext
from ErrorCorrector import correctError


def split_dataset( OCRword_mappings, PickleData = None ):
    print( "building data sets" )

    random.shuffle( OCRword_mappings )

    trainingSet = list( )
    heldoutSet = list( )
    testSet = list( )

    unavailableSlots = dict( )

    print( 'building test set' )

    for itr in range( len( OCRword_mappings ) ):

        # OCRword_mappings[ itr ].OCR_Error.count( ' ' ) == 0 and

        if len( OCRword_mappings[ itr ].OCR_Error ) > 3:

            testSet.append( OCRword_mappings[ itr ] )
            unavailableSlots[ itr ] = True

            if len( testSet ) >= int( .03 * len( OCRword_mappings ) ):
                print( len( testSet ) )
                break

    print( 'building heldout set' )
    for itr in range( len( OCRword_mappings ) ):

        # OCRword_mappings[ itr ].OCR_Error.count( ' ' ) == 0 and \

        if itr not in unavailableSlots and \
                        len( OCRword_mappings[ itr ].OCR_Error ) > 3:

            heldoutSet.append( OCRword_mappings[ itr ] )
            unavailableSlots[ itr ] = True

            if len( heldoutSet ) >= int( .04 * len( OCRword_mappings ) ):
                print( len( heldoutSet ) )
                break

    print( 'building training set' )
    for itr in range( len( OCRword_mappings ) ):

        if itr not in unavailableSlots:

            trainingSet.append( OCRword_mappings[ itr ] )

    print( "all data sets built" )

    DATASets = { 'training': trainingSet, 'heldout': heldoutSet, 'test': testSet }

    if PickleData is not None:
        print( "pickling data sets" )
        with open( 'PickledData/DataSets/training_set1.pickle', 'wb' ) as trainPkl, \
                open( 'PickledData/DataSets/heldout_set1.pickle', 'wb' ) as heldoutPkl, \
                open( 'PickledData/DataSets/test_set1.pickle', 'wb' ) as testPkl:
            pickle.dump( trainingSet, trainPkl, pickle.HIGHEST_PROTOCOL )
            pickle.dump( heldoutSet, heldoutPkl, pickle.HIGHEST_PROTOCOL )
            pickle.dump( testSet, testPkl, pickle.HIGHEST_PROTOCOL )

    return DATASets


def trainHMM( dataSets ):
    print( "trainHMM" )

    maps = [ (arg.intended_Word, arg.OCR_Error) for arg in dataSets[ 'training' ] ]

    supervisedModel = HiddenMarkovModelTrainer( )

    trainer = supervisedModel.train_supervised( )

    next( trainer )

    for itr in range( 4 ):

        partndAlignmnts = partitionStrAlignments(
            maps[ int( len( maps ) * itr / 4 ):int( len( maps ) * (itr + 1) / 4 ) ],
            phase = ('training' if not itr else 'still-training'),
            pickle_stats = (False if itr < 3 else True) )

        partitions = list( partndAlignmnts.values( ) )

        del partndAlignmnts
        # gc.collect( )

        HMMInput = [ mapping for W in partitions for mapping in W ]

        del partitions
        #gc.collect( )

        try:
            trainer.send( HMMInput )
        except StopIteration:
            print( "stopIteration inside for loop", itr )

        del HMMInput
        gc.collect( )

    try:
        trainer.send( None )
    except StopIteration:
        print( "caught stop iteration outside for loop", itr )

    print( "ALL PARTITIONS GENERATED" )

    return


metrics = dict( )


def HMM_modelSelection( dataSets ):
    print( "HMM_modelSelection" )

    HMM = HiddenMarkovModelTrainer( )

    STRT = 900
    LEN = 115

    with open( 'printedData/modelSelection_results_' + str( datetime.date.today( ) ) + '.txt','a' ) as file:
        file.write('Start Position: {0}\nLength: {1}\n\n'.format(STRT,LEN))

    for smoother, HMM_model in HMM.train_supervised( testing = True ):
        for globalModelParameters.NUM_PARTITIONS in [ 2, ]: #12,8,6, > 2
            for Lambda in [1.35, ]: #1.45,1.4, > 1.5, > 1.6,
                for globalModelParameters.EpsilonTransition in [ 0.005,  ]: #0.0005,
                    for globalModelParameters.TransitionWeight in [ 0.45, ]: #0.45 >  0.4,0.55, > 0.5, > 0.3,

                        if not globalModelParameters.TransitionWeight:
                                globalModelParameters.EM_STEP=False

                        # if (Lambda == 1.4 and globalModelParameters.TransitionWeight == 0.5) or \
                        #     (Lambda == 1.4 and globalModelParameters.TransitionWeight == 0.4) or \
                        #     (Lambda == 1.5 and globalModelParameters.TransitionWeight == 0.5) or \
                        #     (Lambda == 1.5 and globalModelParameters.TransitionWeight == 0.4) :
                        #     continue


                        print( "lambda: {0}, Epsilon: {1}, TransWeight: {2}, NumPartitions: {3}".format( Lambda,
                                                                                                         globalModelParameters.EpsilonTransition,
                                                                                                         globalModelParameters.TransitionWeight,
                                                                                                         globalModelParameters.NUM_PARTITIONS ) )
                        print( "smoothing parameters:\n{}\n\n".format( str( smoother ) ) )

                        epsilon = globalModelParameters.EpsilonTransition
                        trans_weight = globalModelParameters.TransitionWeight

                        t1 = datetime.datetime.now( )
                        metrics[ (smoother, Lambda, epsilon, trans_weight, globalModelParameters.NUM_PARTITIONS) ] = \
                            testHMM( dataSets[ 'heldout' ][ STRT:(STRT + LEN) ], HMM_model, smoother, Lambda, True )

                        t2 = datetime.datetime.now( )

                        time_delta = t2 - t1

                        duration_secs = time_delta.total_seconds( )

                        print( "total time in seconds {}".format( duration_secs ) )
                        print( "seconds per correction {}\n\n".format( duration_secs / LEN ) )



                    with open( 'printedData/modelSelection_results_' + str( datetime.date.today( ) ) + '.txt',
                               'a' ) as file:

                        for k, v in sorted( metrics.items( ), key = lambda arg: arg[ 1 ], reverse = True ):
                            file.write( 'Model: {0}\nResults: {1}\n\n'.format( str( k ), v ) )
                        file.write( "\n" )
                        file.write( "-" * 80 )
                        file.write( "\n" * 3 )



    if globalModelParameters.EM_STEP:
        with open( 'PickledData/HMM_data/outputs_FIXED1_final_EM_MOD_500len.pickle', 'wb' ) as pkl:
            pickle.dump(globalModelParameters.outputsModel,pkl,pickle.HIGHEST_PROTOCOL)

    print( "model selection finished\n" )

    return


_BEST_MODELS = [ 0, 0, 0 ]


def testHMM( test_set, HMM, smoother, Lambda, reset ):
    print( "testHMM" )

    # count the number of None returns to offset for ignoring split errors for now
    noneCounts = 0

    ErrorContextObjs = [ ErrorContext( arg.OCR_Error, arg.TrueContext, int( ), arg.ID ) for arg in test_set ]

    intendedWords = [ arg.intended_Word for arg in test_set ]

    correctionsData = [ ]
    for error, answer in zip( ErrorContextObjs, intendedWords ):
        correctionsData.append( correctError( error, reset, answer, HMMmodel = HMM, LambdaParameter = Lambda ) )
        if reset:
            reset = False

    numCorrect = 0
    for C, I in zip( map( lambda arg: arg[ 0 ][ 'candidate' ], correctionsData ), intendedWords ):
        if C == I:
            numCorrect += 1
        elif C is None:
            noneCounts += 1
        else:
            Iset = set( I )
            cand = set( C )
            diffSet = cand.difference( Iset )
            if len( diffSet ) == 1 and ( "'" in diffSet or '.' in diffSet or ' ' in diffSet or 's' in diffSet):
                numCorrect += 1
            elif len( diffSet ) == 2 and "'" in diffSet and 's' in diffSet:
                numCorrect += 1

    percentCorrect = numCorrect / (len( intendedWords ) - noneCounts)

    with open( 'printedData/intendedWord_Err_corrections_' + str( datetime.date.today( ) ) + '.txt', 'a' ) as output:
        output.write( 'BEGIN-MODEL\n' )
        output.write( 'Accuracy: ' + str( percentCorrect ) + '\n' )
        output.write( '[smoothing parameters]\n{0}\n[lambda] {1} [epsilon] {2} [trans weight] {3} [num partitions] {'
                      '4}\n'.format(
            str( smoother ), Lambda, globalModelParameters.EpsilonTransition,
            globalModelParameters.TransitionWeight, globalModelParameters.NUM_PARTITIONS ) )
        output.write( "KEY: leftContext [intended,candidate,error] rightContext\n\n" )

        for intended, result in zip( intendedWords, correctionsData ):
            output.write(
                "[context]{left} [{I},{C},{E}] {right}\n\n".format( left = result[ 0 ][ 'context' ][ 0 ], I = intended,
                                                                    C = result[ 0 ][ 'candidate' ],
                                                                    E = result[ 0 ][ 'error' ],
                                                                    right = result[ 0 ][ 'context' ][ 1 ] ) )

            for subresult in result:
                output.write( "[candidate] {5} [total] {0}, [channel] {1}, [lang] {2}, [HMMchannel] {3}, [HMMsource] {"
                              "4}\n[maxPartition] {6}\n\n"
                              .format( subresult[ 'totalProb' ], subresult[ 'channelProb' ],
                                       subresult[ 'langProb' ], subresult[ 'HMMchannel' ],
                                       subresult[ 'HMMsource' ], subresult[ 'candidate' ],
                                       subresult[ 'maxPartition' ] ) )
            output.write( '---------------------------------------------------------------------------\n\n\n' )

        output.write( 'END-MODEL\n\n\n\n' )

    if percentCorrect > _BEST_MODELS[ 0 ]:
        _BEST_MODELS[ 0 ] = percentCorrect
        with open( 'PickledData/firstModelData_' + str( datetime.date.today( ) ) + '.pickle', 'wb' ) as pklfile:
            pickle.dump( { str( (Lambda, smoother, globalModelParameters.EpsilonTransition,
                                 globalModelParameters.TransitionWeight, globalModelParameters.NUM_PARTITIONS) ):
                               list( zip( intendedWords, correctionsData ) ) },
                         pklfile, pickle.HIGHEST_PROTOCOL )

    elif percentCorrect > _BEST_MODELS[ 1 ]:
        _BEST_MODELS[ 1 ] = percentCorrect
        with open( 'PickledData/secondModelData_' + str( datetime.date.today( ) ) + '.pickle', 'wb' ) as pklfile:
            pickle.dump( { str( (Lambda, smoother, globalModelParameters.EpsilonTransition,
                                 globalModelParameters.TransitionWeight, globalModelParameters.NUM_PARTITIONS) ):
                               list( zip( intendedWords, correctionsData ) ) },
                         pklfile, pickle.HIGHEST_PROTOCOL )

    elif percentCorrect > _BEST_MODELS[ 2 ]:
        _BEST_MODELS[ 2 ] = percentCorrect
        with open( 'PickledData/thirdModelData_' + str( datetime.date.today( ) ) + '.pickle', 'wb' ) as pklfile:
            pickle.dump( { str( (Lambda, smoother, globalModelParameters.EpsilonTransition,
                                 globalModelParameters.TransitionWeight, globalModelParameters.NUM_PARTITIONS) ):
                               list( zip( intendedWords, correctionsData ) ) },
                         pklfile, pickle.HIGHEST_PROTOCOL )

    return percentCorrect


if __name__ == '__main__':
    with open( 'PickledData/DataSets/heldout_set1.pickle', 'rb' ) as pklfile:
        _dataSet = pickle.load( pklfile )

    print( len( _dataSet ) )

    HMM_modelSelection( { 'heldout': _dataSet } )

    # with open('PickledData/all_wordMappings_taggedV1_17.pickle','rb') as pklfile:
    # _dataSet=list(pickle.load(pklfile))
    #
    # d=split_dataset(_dataSet,True)
    #
    # trainHMM(d)


