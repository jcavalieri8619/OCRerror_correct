__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '8/30/14'

import math
import random
import time
import multiprocessing
from collections import OrderedDict

from buildWordLangModel import NgramServer
from candidateGenerator import generateCandidates
from partitionStrAlignment import partitionStrAlignments
import globalModelParameters
from collections import defaultdict

_ngram_server = NgramServer( )

_LEFTCONTEXT = 0
_RIGHTCONTEXT = 1

_NINF = float( '-1e300' )

##currently modified to include NUM_PARTITIONS partitions in probability calculation
##despite egregious overlap of substring segments between partitions
def channelModel( candidate_object ):
    partitionProbData = [ ]

    for partition in candidate_object[ 'partitions' ]:


        partitionProbData.append( HMMmodel.log_probability( partition,
                                                        transitions_weight = globalModelParameters.TransitionWeight ) )


    partitionProbData.sort(key=lambda arg: arg['HMMtotal'],reverse=True)

    TopPartitionsProbData=partitionProbData[:globalModelParameters.NUM_PARTITIONS]



    candidate_object.pop( 'partitions' )

    candidate_object[ 'totalProb' ] = 0

    candidate_object[ 'channelProb' ] = round( math.log2(sum(map(lambda arg: 2**arg[ 'HMMtotal' ],TopPartitionsProbData),0)) ,
    3 )
    candidate_object[ 'langProb' ] = 0

    candidate_object[ 'HMMchannel' ] = round( math.log2(sum(map(lambda arg: 2**arg[ 'HMMchannel' ],TopPartitionsProbData),0)) ,
                                              3 )

    candidate_object[ 'HMMsource' ] = round( math.log2(sum(map(lambda arg: 2**arg[ 'HMMsource' ],TopPartitionsProbData),0)) , 3 )

    candidate_object[ 'maxPartition' ] = TopPartitionsProbData[0]['sequence']

    candidate_object['topPartitionsDict'] = TopPartitionsProbData

    return candidate_object


def languageModel( candidate_object ):
    candidate = candidate_object[ 'candidate' ]
    leftContext = candidate_object[ 'context' ][ _LEFTCONTEXT ].split( )
    rightContext = candidate_object[ 'context' ][ _RIGHTCONTEXT ].split( )

    extra = 0
    if '-' in candidate:
        extra = 1

    left_prob = 0
    right_prob = 0

    _RandBackoffs = [ 0.01, 0.02, 0.03, 0.04, ]
    # random back off before entering server query region to adhere to Microsoft Ngram server policy
    time.sleep( random.choice( _RandBackoffs ) )

    if leftContext:
        #+rightContext[ :1 ]
        left_order = len( (leftContext[ 1: ] + candidate.split( )
                            ) ) + extra

        left_prob = 10 ** _ngram_server.query( ' '.join( (leftContext[ 1: ] + candidate.split( ) ) ),
                                               left_order )

    if rightContext:
        #leftContext[ -1: ] +
        right_order = len(  candidate.split( ) + rightContext[ :-1 ] ) + extra

        right_prob = 10 ** _ngram_server.query(
            ' '.join( candidate.split( ) + rightContext[ :-1 ] ),
            right_order )

    if leftContext and rightContext:

        candidate_object[ 'langProb' ] = round( (LambdaParameter - 1) *
                                                (math.log2( left_prob ) + math.log2( right_prob )), 3 )

        return candidate_object

    else:
        candidate_object[ 'langProb' ] = round( (LambdaParameter - 1) * math.log2( right_prob or left_prob ), 3 )

        return candidate_object


def rankCandidates( candidate_object ):
    candidate_object[ 'totalProb' ] = round( candidate_object[ 'channelProb' ] + candidate_object[ 'langProb' ], 3 )

    #FIXME required for EM step

    if globalModelParameters.EM_STEP:
        for partitionData in candidate_object['topPartitionsDict']:

            #EM step probabilities probably shouldn't involve world level language model probability
            partitionData['totalProb'] = round( partitionData[ 'HMMtotal' ],3) #+ candidate_object[ 'langProb' ], 3 )


    return candidate_object


_numCorrect = 0
_total = 0


def correctError( ErrorContextObj, reset, answer = '', **kwargs ):
    # additionalParameters
    N = 80  # top N candidates to be re-ranked by language model

    global _numCorrect, _total
    global HMMmodel, LambdaParameter
    HMMmodel = kwargs.get( 'HMMmodel' )
    LambdaParameter = kwargs.get( 'LambdaParameter' )

    if reset:
        _total = 0
        _numCorrect = 0
    else:
        pass
        # #part of EM update method; updated before each new correction
        #HMMmodel.update_outputsModel()

    if answer.count( ' ' ) > 0:
        # ignoring split errors for now
        ignoreCandidate = [ OrderedDict( [ ('error', ErrorContextObj.Error),
                                           ('candidate', None),
                                           ('context', ErrorContextObj.Context),
                                           ('totalProb', _NINF), ('channelProb', None), ('langProb', None),
                                           ('HMMchannel', None), ('HMMsource', None),
                                           ('maxPartition', [ tuple( ) ]) ] ) ]

        return ignoreCandidate

    Allcandidates = set( )

    bestCandidate = OrderedDict( [ ('error', ErrorContextObj.Error),
                                   ('candidate', 'UNK'),
                                   ('context', ErrorContextObj.Context),
                                   ('totalProb', _NINF), ('channelProb', None), ('langProb', None),
                                   ('HMMchannel', None), ('HMMsource', None), ('maxPartition', [ tuple( ) ]) ] )

    TOP10 = [ bestCandidate ]

    # for itr,(editSeq,editDist) in enumerate(generateAvgEditOpSeq(len(ErrorContextObj.Error))):
    for itr, editDist in enumerate( range( 3, 15 ) ):
        editSeq = None
        candidates = generateCandidates( ErrorContextObj.Error,
                                         ErrorContextObj.Context, itr,
                                         editDist, editSeq ).difference( Allcandidates )

        Allcandidates.update( candidates )

        # remove error from candidates - artifact of large lexicon
        candidates.discard( ErrorContextObj.Error )

        if not candidates:
            continue

        word_mappings = [ (candidate, ErrorContextObj.Error) for candidate in candidates ]

        partitioned_mappings = partitionStrAlignments( word_mappings )

        candidateObjects = [ ]

        for candidate in candidates:

            candidateObjects.append( (OrderedDict( [ ('error', ErrorContextObj.Error),
                                                     ('candidate', candidate), ('context', ErrorContextObj.Context),
                                                     ('partitions', partitioned_mappings[ candidate ]) ] )) )



        with multiprocessing.Pool( 4 ) as Pool:
            candidateObj_Channelranks = Pool.map( channelModel, candidateObjects, chunksize = 20 )



        Pool.join( )

        candidateObj_Channelranks.sort( key = lambda arg: arg[ 'channelProb' ], reverse = True )

        TopCandidates = candidateObj_Channelranks[ :N ]

        with multiprocessing.Pool( 10 ) as Pool:
            candidateObj_Languageranks = Pool.map( languageModel, TopCandidates )


        Pool.join( )

        with multiprocessing.Pool( 4 ) as Pool:
            candidateObj_ranks = Pool.map( rankCandidates, candidateObj_Languageranks, chunksize = 20 )

        Pool.join( )

        del partitioned_mappings, word_mappings


        candidateObj_ranks = sorted( candidateObj_ranks, key = lambda arg: arg[ 'totalProb' ], reverse = True )


        TOP10 = candidateObj_ranks[ :10 ]
        currMaxCandidate = TOP10[ 0 ]

        for count, result in enumerate( TOP10 ):
            if count:
               result.pop( 'context' )

        if currMaxCandidate[ 'totalProb' ] > bestCandidate[ 'totalProb' ]:
            bestCandidate = currMaxCandidate
            break

    printCandidate( bestCandidate, answer )

    isCorrect=False

    if bestCandidate[ 'candidate' ] == answer:
        _numCorrect += 1
        isCorrect=True
    else:
        Iset = set( answer )
        C = set( bestCandidate[ 'candidate' ] )
        diffSet = C.difference( Iset )
        if len( diffSet ) == 1 and ( "'" in diffSet or '.' in diffSet or ' ' in diffSet or 's' in diffSet):
            _numCorrect += 1
            isCorrect=True
        elif len( diffSet ) == 2 and "'" in diffSet and 's' in diffSet:
            _numCorrect += 1
            isCorrect=True

    #todo EM STEP
    if globalModelParameters.EM_STEP and isCorrect:

        normalizing_const=defaultdict(int)
        candidateOptimalPartitions=list()

        for candidate in TOP10:

            for itr,partitionData in enumerate(candidate['topPartitionsDict']):

                normalizing_const[itr] += 2**partitionData['totalProb']

        for itr,partitionData in enumerate(bestCandidate['topPartitionsDict']):

                candidateOptimalPartitions.append((partitionData['sequence'],
                                                   (2**partitionData['totalProb'])/normalizing_const[itr]))

                # print("\nTESTING {0}\n{1}\n".format(partitionData['sequence'],
                #                                  (2**partitionData['totalProb'])/normalizing_const[itr]))

        SEQ=0
        NORMED_PROB=1
        for elements in candidateOptimalPartitions:

            #instead of distributing prob mass equally among non-identity maps
            #just increase each by full prob mass akin to training process
            num_nonIdentity_maps = 1    #sum(map(lambda arg: arg[0] != arg[1],elements[SEQ]),0)

            ERR_MAP=0
            TRUE_MAP=1
            for mapping in elements[SEQ]:

                if mapping[ERR_MAP] != mapping[TRUE_MAP]:

                    globalModelParameters.outputsModel[mapping[TRUE_MAP]][mapping[ERR_MAP]] += \
                        (elements[NORMED_PROB]/num_nonIdentity_maps)





    _total += 1

    print( "RESULTS - accuracy:{0}, numCorrect:{1}, total:{2}\n".format(round(_numCorrect / _total,3), _numCorrect, \
                                                                            _total ) )

    return TOP10


def printCandidate( candidate, answer ):
    print( "[{5}] {0}<->{1}\n{8}"
           "\nT={2}, C={3}, L={4}, HC={6}, HS={7}"
           "\nmax_partition:{9}\n".format( candidate[
                                               'candidate' ],
                                           candidate[
                                               'error' ],
                                           candidate[
                                               'totalProb' ],
                                           candidate[
                                               'channelProb' ],
                                           candidate[
                                               'langProb' ],
                                           (
                                               answer if answer is not None else ""),
                                           candidate[
                                               'HMMchannel' ],
                                           candidate[
                                               'HMMsource' ],
                                           candidate[
                                               'context' ],
                                           candidate[
                                               'maxPartition' ] ) )