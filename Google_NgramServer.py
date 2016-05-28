__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '9/2/14'

from ast import literal_eval

import regex
import requests
from pandas import DataFrame


_corpora = dict( eng_us_2012 = 17, eng_us_2009 = 5, eng_gb_2012 = 18, eng_gb_2009 = 6,
                 chi_sim_2012 = 23, chi_sim_2009 = 11, eng_2012 = 15, eng_2009 = 0,
                 eng_fiction_2012 = 16, eng_fiction_2009 = 4, eng_1m_2009 = 1,
                 fre_2012 = 19, fre_2009 = 7, ger_2012 = 20, ger_2009 = 8, heb_2012 = 24,
                 heb_2009 = 9, spa_2012 = 21, spa_2009 = 10, rus_2012 = 25, rus_2009 = 12,
                 ita_2012 = 22 )


class NgramServer( object ):
    def __init__( self, V, N ):
        self.V = V
        self.N = N


    def queryServer( self, phrase ):

        words = phrase.split( )

        order = len( words )

        if order == 1:
            expression = phrase

        elif order > 1:
            expression = "{phrase}/{hist}".format( phrase = phrase, hist = words[ :-1 ] )
        else:
            raise RuntimeError( 'Google NgramServer: empty phrase' )


    @staticmethod
    def getNgrams( query, corpus, startYear, endYear, smoothing, caseInsensitive ):
        params = dict( content = query, year_start = startYear, year_end = endYear,
                       corpus = _corpora[ corpus ], smoothing = smoothing,
                       case_insensitive = caseInsensitive )
        if params[ 'case_insensitive' ] is False:
            params.pop( 'case_insensitive' )
        if '?' in params[ 'content' ]:
            params[ 'content' ] = params[ 'content' ].replace( '?', '*' )
        if '@' in params[ 'content' ]:
            params[ 'content' ] = params[ 'content' ].replace( '@', '=>' )
        req = requests.get( 'http://books.google.com/ngrams/graph', params = params )
        res = regex.findall( 'var data = (.*?);\\n', req.text )
        data = { qry[ 'ngram' ]: qry[ 'timeseries' ] for qry in literal_eval( res[ 0 ] ) }
        df = DataFrame( data )
        df.insert( 0, 'year', range( startYear, endYear + 1 ) )
        return req.url, params[ 'content' ], df