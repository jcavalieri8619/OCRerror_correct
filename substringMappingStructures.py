__author__ = 'jcavalie'


def subgroups( my_list ):
    for each_tuple in (lambda p, f = lambda n, g:
        { (x,) + y for x in range( 1, n ) for y in g( n - x, g ) } | { (n,) }:
                       f( p, f ))( len( my_list ) ):
        yield list( my_list[ sum( each_tuple[ :index ] ):sum( each_tuple[ :index ] ) + length ] for index, length in
                    enumerate( each_tuple ) )


_OBS = 0
_HIDN = 1


class mappingObject( object ):
    def __init__( self, charMapping, initposition ):
        self._substrMapping = (charMapping[ _OBS ], charMapping[ _HIDN ])
        self._positions = initposition


    def getSubstrMapping( self ):
        return self._substrMapping[ : ]


    def getPositions( self ):
        return self._positions


    def __le__( self, other ):
        return max( self.getPositions( ) ) <= min( other.getPositions( ) )


    def __add__( self, other ):
        observed = self.getSubstrMapping( )[ _OBS ] + other.getSubstrMapping( )[ _OBS ]
        hidden = self.getSubstrMapping( )[ _HIDN ] + other.getSubstrMapping( )[ _HIDN ]
        updatedPositions = sorted( self.getPositions( ) + other.getPositions( ) )
        return mappingObject( (observed, hidden), updatedPositions )


_MAX_ERRWIN = 3


class mappingContainer( object ):
    def __init__( self, mappingLst, possible_positions ):
        self._mappings = list( )
        self.possiblePositions = possible_positions
        self._full_length = len( possible_positions )

        if isinstance( mappingLst[ 0 ], mappingObject ):
            self._mappings = mappingLst[ : ]

        elif isinstance( mappingLst[ 0 ], list ):
            for sublist in mappingLst:
                if len( sublist ) > _MAX_ERRWIN or not len(sublist):
                    self._mappings = list( )
                    raise ValueError( "Max ErrWindow Exceeded or Empty" )
                else:
                    currMapObj = sum( sublist[ 1: ], sublist[ 0 ] )

                    #FIXME
                    #if accuracy drops then restore below code block to original
                    #by simply appending currMapObj without checking anything
                    currMap=currMapObj.getSubstrMapping()

                    if currMap[_OBS] == currMap[_HIDN] and len(currMap[_OBS])>1:
                        raise ValueError( "many-to-many identity mapping" )
                    else:
                        self._mappings.append( currMapObj )

        else:
            raise RuntimeError( "Error occurred in mappingContainer.__init__" )


    def getLstMapObjs( self ):
        return self._mappings[ : ]


    def exportMapping( self, container, **kwargs ):
        temp_container = [ ]
        for arg in self.getLstMapObjs( ):
            substr_mapping = arg.getSubstrMapping( )
            temp_container.append( substr_mapping )

        container.append( temp_container )


    def __add__( self, other ):
        updatedMappings = self.getLstMapObjs( ) + other.getLstMapObjs( )
        return mappingContainer( updatedMappings, self.possiblePositions  )

    def getCurrPositions( self ):
        currPositions = list( )
        for arg in self.getLstMapObjs( ):
            currPositions.extend( arg.getPositions( ) )
        return currPositions


    def positionsNeeded( self ):

        return list( set( self.possiblePositions ) - set( self.getCurrPositions( ) ) )


    def insertMapping( self, other ):
        for index, objct in enumerate( self.getLstMapObjs( ) ):
            if other <= objct:
                self._mappings.insert( index, other )
                break
        else:
            self._mappings.append( other )