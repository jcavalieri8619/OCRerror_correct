__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '8/28/14'

import os
import sys
import urllib
import time
import math


class LookupService( object ):
    def __init__( self, token = '8a95a6d9-71c7-4cc1-8ffd-082c9bd3f5f1', model = None, serviceUri = None ):
        self.token = token
        if (token is None):
            self.token = os.getenv( 'NGRAM_TOKEN' )
        else:
            self.token = token
        if (self.token is None):
            raise ValueError(
                'token must be specified, either as an argument, or as an environment variable named NGRAM_TOKEN' )

        if (model is None):
            _model = os.getenv( 'NGRAM_MODEL' )
            if (_model is not None):
                self.model = LookupService._parseModel( _model )
            else:
                self.model = "bing-body/2013-12/3"
        else:
            self.model = LookupService._parseModel( model );

        if (serviceUri is None):
            self.serviceUri = os.getenv( 'NGRAM_SERVICEURI' )
            if (self.serviceUri is None):
                self.serviceUri = 'http://weblm.research.microsoft.com/rest.svc/'
        else:
            self.serviceUri = serviceUri


    @staticmethod
    def _parseModel( model ):
        import re


        result = re.match( 'urn:ngram:(.*):(.*):(\d+)', model )
        return result.group( 1 ) + "/" + result.group( 2 ) + "/" + result.group( 3 ) if (result is not None) else model


    @staticmethod
    def GetModels( ):
        service = LookupService( token = 'bogus' )
        val = urllib.request.urlopen( service.serviceUri ).read( )
        val = val.decode( 'utf-8' )
        return val.split( '\r\n' )  # defines a tuple on the fly


    def SetModel( self, model ):
        self.model = LookupService._parseModel( model )


    def GetModel( self ):
        return self.model


    def _getData( self, phrase, operation, **kwargs ):


        if (self.model is None):
            raise ValueError(
                'model must be specified, either as an argument to the LookupService constructor, or as an environment variable named NGRAM_MODEL' )
        urlAddr = self.serviceUri + self.model + '/' + operation + '?p=' + urllib.parse.quote(
            phrase ) + '&u=' + self.token
        if (kwargs is not None):
            for k, v in kwargs.items( ):
                urlAddr = urlAddr + '&' + k + '=' + urllib.parse.quote( str( v ) )

        try:
            result = urllib.request.urlopen( urlAddr )
        except KeyboardInterrupt:
            raise
        except :
            print( "MSFT_NGRAM_SERVER: Exception" )
            result = str(math.log10(0.98))
            return result
        else:
            return result.read( )


    def _getProbabilityData( self, phrase, operation ):
        return float( self._getData( phrase, operation ) )


    def GetJointProbability( self, phrase ):
        return self._getProbabilityData( phrase, 'jp' )


    def GetConditionalProbability( self, phrase ):
        return self._getProbabilityData( phrase, 'cp' )


    def breakWord( self, phrase ):
        return self._getData( phrase, 'wb', n = 5 )


    def Generate( self, phrase, maxgen = None ):
        nstop = sys.maxint if (maxgen is None) else maxgen;
        arg = { }
        while (True):
            arg[ 'n' ] = min( 1000, max( 0, nstop ) );
            result = self._getData( phrase, 'gen', arg ).split( '\r\n' )
            if (len( result ) <= 2):
                break;
            nstop -= len( result ) - 2;
            arg[ 'cookie' ] = result[ 0 ]
            backoff = result[ 1 ]
            for x in result[ 2: ]:
                pair = x.split( ';' )
                yield pair[ 0 ], float( pair[ 1 ] )


# Retry decorator with exponential backoff
def retry( tries, delay = 3, backoff = 2 ):
    '''Retries a function or method until it returns True.

    delay sets the initial delay in seconds, and backoff sets the factor by which
    the delay should lengthen after each failure. backoff must be greater than 1,
    or else it isn't really a backoff. tries must be at least 0, and delay
    greater than 0.'''

    if backoff <= 1:
        raise ValueError( "backoff must be greater than 1" )

    tries = math.floor( tries )
    if tries < 0:
        raise ValueError( "tries must be 0 or greater" )

    if delay <= 0:
        raise ValueError( "delay must be greater than 0" )


    def deco_retry( f ):
        def f_retry( *args, **kwargs ):
            mtries, mdelay = tries, delay  # make mutable

            rv = f( *args, **kwargs )  # first attempt
            while mtries > 0:
                if rv is True:  # Done on success
                    return True

                mtries -= 1  # consume an attempt
                time.sleep( mdelay )  # wait...
                mdelay *= backoff  # make future wait longer

                rv = f( *args, **kwargs )  # Try again

            return False  # Ran out of tries :-(


        return f_retry  # true decorator -> decorated function


    return deco_retry  # @retry(arg[, ...]) -> true decorator