__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '9/29/14'

import regex

from ParallelGlobal import parallelCorpora
from customizedProbability import FreqDist


def compileDictionary( ):
    with open( '/home/jcavalie/Britannica11/fullclean11/allclean.txt', 'r', encoding = 'ISO-8859-15' ) as file:
        fstr = file.read( )

    fstr = fstr.replace( '-', ' ' )

    cleanstr = parallelCorpora._normalize( fstr, '' )[ 'clean' ]

    wordPattern = r"((?:[a-z]+[\']?[a-z]*)|(?:[a-z]+[\.]?[a-z]+))"

    wordFreqs = FreqDist( regex.findall( wordPattern, cleanstr ) )