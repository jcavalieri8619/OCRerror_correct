__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '8/16/14'

import pickle

from nltk.probability import ConditionalFreqDist, FreqDist


def posn_to_label( substr_positions, string_length ):
    midpoint = ((substr_positions[ 0 ] + substr_positions[ -1 ]) / 2)

    if midpoint <= string_length / 3:
        return '<BEG>'
    elif string_length / 3 < midpoint <= 2 / 3 * string_length:
        return '<MID>'
    else:
        return '<END>'


class OCRErrorStats( object ):
    def __init__( self ):
        self.editDist_correctLen = ConditionalFreqDist( )

        self.editDist_errorLen = ConditionalFreqDist( )

        self.errorLen_editDist = ConditionalFreqDist( )

        self.errorLen_editOps = ConditionalFreqDist( )

        self.correctLen_editDist = ConditionalFreqDist( )

        self.errorLen_correctLen = ConditionalFreqDist( )

        self.errorLen_insertOp = ConditionalFreqDist( )

        self.errorLen_deleteOp = ConditionalFreqDist( )

        self.errorLen_substituteOp = ConditionalFreqDist( )

        self.errorLen_sizeErrorWins = ConditionalFreqDist( )

        self.editDist_numErrorWins = ConditionalFreqDist( )

        self.errorLens = FreqDist( )

        self.correctLens = FreqDist( )

        self.editDists = FreqDist( )

        self.insertEdits = FreqDist( )

        self.deleteEdits = FreqDist( )

        self.substituteEdits = FreqDist( )

        self.sizeErrorWins = FreqDist( )

        self.numErrorWins = FreqDist( )


    def updateDistribution( self, distribution, arg1, arg2 = None ):
        if arg2 is not None:
            self.__dict__[ distribution ][ arg1 ][ arg2 ] += 1
        else:
            self.__dict__[ distribution ][ arg1 ] += 1


    def load_OCRErrorStats( self ):

        with open( "PickledData/ErrorStats/editDist_correctLen.pickle", 'rb' ) as pklfile:
            self.editDist_correctLen = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/editDist_errorLen.pickle", 'rb' ) as pklfile:
            self.editDist_errorLen = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/errorLen_correctLen.pickle", 'rb' ) as pklfile:
            self.errorLen_correctLen = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/errorLen_editDist.pickle", 'rb' ) as pklfile:
            self.errorLen_editDist = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/errorLen_editOps.pickle", 'rb' ) as pklfile:
            self.errorLen_editOps = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/errorLen_insertOp.pickle", 'rb' ) as pklfile:
            self.errorLen_insertOp = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/errorLen_deleteOp.pickle", 'rb' ) as pklfile:
            self.errorLen_deleteOp = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/errorLen_substituteOp.pickle", 'rb' ) as pklfile:
            self.errorLen_substituteOp = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/errorLen_sizeErrorWins.pickle", 'rb' ) as pklfile:
            self.errorLen_sizeErrorWins = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/editDist_numErrorWins.pickle", 'rb' ) as pklfile:
            self.editDist_numErrorWins = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/correctLen_editDist.pickle", 'rb' ) as pklfile:
            self.correctLen_editDist = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/errorLen.pickle", 'rb' ) as pklfile:
            self.errorLens = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/correctLen.pickle", 'rb' ) as pklfile:
            self.correctLens = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/editDists.pickle", 'rb' ) as pklfile:
            self.editDists = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/insertEdits.pickle", 'rb' ) as pklfile:
            self.insertEdits = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/deleteEdits.pickle", 'rb' ) as pklfile:
            self.deleteEdits = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/substituteEdits.pickle", 'rb' ) as pklfile:
            self.substituteEdits = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/numErrorWins.pickle", 'rb' ) as pklfile:
            self.numErrorWins = pickle.load( pklfile )

        with open( "PickledData/ErrorStats/sizeErrorWins.pickle", 'rb' ) as pklfile:
            self.sizeErrorWins = pickle.load( pklfile )


    def pickleAllErrorStats( self ):

        with open( "PickledData/ErrorStats/editDist_correctLen.pickle", 'wb' ) as pklfile:
            pickle.dump( self.editDist_correctLen, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/editDist_errorLen.pickle", 'wb' ) as pklfile:
            pickle.dump( self.editDist_errorLen, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/errorLen_correctLen.pickle", 'wb' ) as pklfile:
            pickle.dump( self.errorLen_correctLen, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/errorLen_editDist.pickle", 'wb' ) as pklfile:
            pickle.dump( self.errorLen_editDist, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/errorLen_editOps.pickle", 'wb' ) as pklfile:
            pickle.dump( self.errorLen_editOps, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/errorLen_insertOp.pickle", 'wb' ) as pklfile:
            pickle.dump( self.errorLen_insertOp, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/errorLen_deleteOp.pickle", 'wb' ) as pklfile:
            pickle.dump( self.errorLen_deleteOp, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/errorLen_substituteOp.pickle", 'wb' ) as pklfile:
            pickle.dump( self.errorLen_substituteOp, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/correctLen_editDist.pickle", 'wb' ) as pklfile:
            pickle.dump( self.correctLen_editDist, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/errorLen_sizeErrorWins.pickle", 'wb' ) as pklfile:
            pickle.dump( self.errorLen_sizeErrorWins, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/editDist_numErrorWins.pickle", 'wb' ) as pklfile:
            pickle.dump( self.editDist_numErrorWins, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/errorLen.pickle", 'wb' ) as pklfile:
            pickle.dump( self.errorLens, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/correctLen.pickle", 'wb' ) as pklfile:
            pickle.dump( self.correctLens, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/editDists.pickle", 'wb' ) as pklfile:
            pickle.dump( self.editDists, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/insertEdits.pickle", 'wb' ) as pklfile:
            pickle.dump( self.insertEdits, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/deleteEdits.pickle", 'wb' ) as pklfile:
            pickle.dump( self.deleteEdits, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/substituteEdits.pickle", 'wb' ) as pklfile:
            pickle.dump( self.substituteEdits, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/numErrorWins.pickle", 'wb' ) as pklfile:
            pickle.dump( self.numErrorWins, pklfile, pickle.HIGHEST_PROTOCOL )

        with open( "PickledData/ErrorStats/sizeErrorWins.pickle", 'wb' ) as pklfile:
            pickle.dump( self.sizeErrorWins, pklfile, pickle.HIGHEST_PROTOCOL )