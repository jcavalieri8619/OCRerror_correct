# Natural Language Toolkit: Hidden Markov Model
#
# Copyright (C) 2001-2016 NLTK Project
# Author: Trevor Cohn <tacohn@csse.unimelb.edu.au>
#         Philip Blunsom <pcbl@csse.unimelb.edu.au>
#         Tiago Tresoldi <tiago@tresoldi.pro.br> (fixes)
#         Steven Bird <stevenbird1@gmail.com> (fixes)
#         Joseph Frazee <jfrazee@mail.utexas.edu> (fixes)
#         Steven Xu <xxu@student.unimelb.edu.au> (fixes)
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT

#MOST of this is NLTK source but I made some modifications -JPC
import itertools
import pickle


try:
    import numpy as np
except ImportError:
    pass

from customizedProbability import (ConditionalProbDist, DictionaryProbDist, DictionaryConditionalProbDist,
                                   LidstoneProbDist, MutableProbDist,
                                   RandomProbDist, WittenBellProbDist, LaplaceProbDist,
                                   SimpleGoodTuringProbDist, Lidstone_03, Lidstone_15,
                                   Lidstone_003, Lidstone_07,ELEProbDist)

from collections import OrderedDict
from nltk.metrics import accuracy
from nltk.util import LazyMap, unique_list
from nltk.compat import python_2_unicode_compatible, izip, imap
from nltk.tag.api import TaggerI
import math
import globalModelParameters


_TEXT = 0  # index of text in a tuple
_TAG = 1  # index of tag in a tuple


def _identity( labeled_symbols ):
    return labeled_symbols


@python_2_unicode_compatible
class HiddenMarkovModelTagger( TaggerI ):
    """
    Hidden Markov model class, a generative model for labelling sequence data.
    These models define the joint probability of a sequence of symbols and
    their labels (state transitions) as the product of the starting state
    probability, the probability of each state transition, and the probability
    of each observation being generated from each state. This is described in
    more detail in the module documentation.

    This implementation is based on the HMM description in Chapter 8, Huang,
    Acero and Hon, Spoken Language Processing and includes an extension for
    training shallow HMM parsers or specialized HMMs as in Molina et.
    al, 2002.  A specialized HMM modifies training data by applying a
    specialization function to create a new training set that is more
    appropriate for sequential tagging with an HMM.  A typical use case is
    chunking.

    :param symbols: the set of output symbols (alphabet)
    :type symbols: seq of any
    :param states: a set of states representing state space
    :type states: seq of any
    :param transitions: transition probabilities; Pr(s_i | s_j) is the
        probability of transition from state i given the model is in
        state_j
    :type transitions: ConditionalProbDistI
    :param outputs: output probabilities; Pr(o_k | s_i) is the probability
        of emitting symbol k when entering state i
    :type outputs: ConditionalProbDistI
    :param priors: initial state distribution; Pr(s_i) is the probability
        of starting in state i
    :type priors: ProbDistI
    :param transform: an optional function for transforming training
        instances, defaults to the identity function.
    :type transform: callable
    """


    def __init__( self, symbols, states, transitions, outputs, priors,
                  transform = _identity ):
        self._symbols = unique_list( symbols )
        self._states = unique_list( states )
        self._transitions = transitions
        self._outputs = outputs
        self._priors = priors
        self._cache = None
        self._transform = transform


    @classmethod
    def _train( cls, labeled_sequence, test_sequence = None,
                unlabeled_sequence = None, transform = _identity,
                estimator = None, **kwargs ):

        if estimator is None:
            def estimator( fd, bins ):
                return LidstoneProbDist( fd, 0.1, bins )

        labeled_sequence = LazyMap( transform, labeled_sequence )
        symbols = unique_list( word for sent in labeled_sequence
                               for word, tag in sent )
        tag_set = unique_list( tag for sent in labeled_sequence
                               for word, tag in sent )

        trainer = HiddenMarkovModelTrainer( tag_set, symbols )
        hmm = trainer.train_supervised( labeled_sequence, estimator = estimator )
        hmm = cls( hmm._symbols, hmm._states, hmm._transitions, hmm._outputs,
                   hmm._priors, transform = transform )

        if test_sequence:
            hmm.test( test_sequence, verbose = kwargs.get( 'verbose', False ) )

        if unlabeled_sequence:
            max_iterations = kwargs.get( 'max_iterations', 5 )
            hmm = trainer.train_unsupervised( unlabeled_sequence, model = hmm,
                                              max_iterations = max_iterations )
            if test_sequence:
                hmm.test( test_sequence, verbose = kwargs.get( 'verbose', False ) )

        return hmm


    @classmethod
    def train( cls, labeled_sequence, test_sequence = None,
               unlabeled_sequence = None, **kwargs ):
        """
        Train a new HiddenMarkovModelTagger using the given labeled and
        unlabeled training instances. Testing will be performed if test
        instances are provided.

        :return: a hidden markov model tagger
        :rtype: HiddenMarkovModelTagger
        :param labeled_sequence: a sequence of labeled training instances,
            i.e. a list of sentences represented as tuples
        :type labeled_sequence: list(list)
        :param test_sequence: a sequence of labeled test instances
        :type test_sequence: list(list)
        :param unlabeled_sequence: a sequence of unlabeled training instances,
            i.e. a list of sentences represented as words
        :type unlabeled_sequence: list(list)
        :param transform: an optional function for transforming training
            instances, defaults to the identity function, see ``transform()``
        :type transform: function
        :param estimator: an optional function or class that maps a
            condition's frequency distribution to its probability
            distribution, defaults to a Lidstone distribution with gamma = 0.1
        :type estimator: class or function
        :param verbose: boolean flag indicating whether training should be
            verbose or include printed output
        :type verbose: bool
        :param max_iterations: number of Baum-Welch interations to perform
        :type max_iterations: int
        """
        return cls._train( labeled_sequence, test_sequence,
                           unlabeled_sequence, **kwargs )


    def probability( self, sequence, transitions_weight = None, outputs_weight = 1 ):
        """
        Returns the probability of the given symbol sequence. If the sequence
        is labelled, then returns the joint probability of the symbol, state
        sequence. Otherwise, uses the forward algorithm to find the
        probability over all label sequences.

        :return: the probability of the sequence
        :rtype: float
        :param sequence: the sequence of symbols which must contain the TEXT
            property, and optionally the TAG property
        :type sequence:  Token
        """
        return 2 ** (self.log_probability( self._transform( sequence ), transitions_weight, outputs_weight ))


    def update_outputsModel( self ):
        self._outputs = ConditionalProbDist( globalModelParameters.outputsModel, WittenBellProbDist,
                                             size_output_alphabet )


    def log_probability( self, sequence, transitions_weight = None, outputs_weight = 1 ):
        """
        Returns the log-probability of the given symbol sequence. If the
        sequence is labelled, then returns the joint log-probability of the
        symbol, state sequence. Otherwise, uses the forward algorithm to find
        the log-probability over all label sequences.

        :return: the log-probability of the sequence
        :rtype: float
        :param sequence: the sequence of symbols which must contain the TEXT
            property, and optionally the TAG property
        :type sequence:  Token
        """
        if transitions_weight is None:
            transitions_weight = 1

        sequence = self._transform( sequence )

        T = len( sequence )
        EPSILON = ''
        channelModel = 0
        sourceModel = 0

        if T > 0 and sequence[ 0 ][ _TAG ] is not None:
            last_state = sequence[ 0 ][ _TAG ]

            if last_state != EPSILON:
                if transitions_weight:
                    sourceModel += transitions_weight * self._priors.logprob( last_state )

            else:
                if transitions_weight:
                    sourceModel += transitions_weight * math.log2( globalModelParameters.EpsilonTransition )

            channelModel += outputs_weight * self._output_logprob( last_state, sequence[ 0 ][ _TEXT ] )

            for t in range( 1, T ):
                state = sequence[ t ][ _TAG ]

                if last_state != EPSILON:
                    if state != EPSILON:
                        if transitions_weight:
                            sourceModel += transitions_weight * self._transitions[ last_state ].logprob( state )
                    else:
                        if transitions_weight:
                            sourceModel += transitions_weight * math.log2( globalModelParameters.EpsilonTransition )
                else:
                    # check if last_state is epsilon; if so then transition with probability of Epsilon
                    if transitions_weight:
                        sourceModel += transitions_weight * math.log2( globalModelParameters.EpsilonTransition )

                channelModel += outputs_weight * self._output_logprob( state, sequence[ t ][ _TEXT ] )

                last_state = state

            # FIXME changed exponentiation
            return { 'HMMtotal':  (sourceModel + channelModel),
                     'HMMchannel':  channelModel,
                     'HMMsource':  sourceModel,
                     'sequence': sequence}


    def tag( self, unlabeled_sequence ):
        """
        Tags the sequence with the highest probability state sequence. This
        uses the best_path method to find the Viterbi path.

        :return: a labelled sequence of symbols
        :rtype: list
        :param unlabeled_sequence: the sequence of unlabeled symbols
        :type unlabeled_sequence: list
        """
        unlabeled_sequence = self._transform( unlabeled_sequence )
        return self._tag( unlabeled_sequence )


    def _tag( self, unlabeled_sequence ):
        path = self._best_path( unlabeled_sequence )
        return list( izip( unlabeled_sequence, path ) )


    def _output_logprob( self, state, symbol ):
        """
        :return: the log probability of the symbol being observed in the given
            state
        :rtype: float
        """
        return self._outputs[ state ].logprob( symbol )


    def _create_cache( self ):
        """
        The cache is a tuple (P, O, X, S) where:

          - S maps symbols to integers.  I.e., it is the inverse
            mapping from self._symbols; for each symbol s in
            self._symbols, the following is true::

              self._symbols[S[s]] == s

          - O is the log output probabilities::

              O[i,k] = log( P(token[t]=sym[k]|tag[t]=state[i]) )

          - X is the log transition probabilities::

              X[i,j] = log( P(tag[t]=state[j]|tag[t-1]=state[i]) )

          - P is the log prior probabilities::

              P[i] = log( P(tag[0]=state[i]) )
        """
        if not self._cache:
            N = len( self._states )
            M = len( self._symbols )
            P = np.zeros( N, np.float32 )
            X = np.zeros( (N, N), np.float32 )
            O = np.zeros( (N, M), np.float32 )
            for i in range( N ):
                si = self._states[ i ]
                P[ i ] = self._priors.logprob( si )
                for j in range( N ):
                    X[ i, j ] = self._transitions[ si ].logprob( self._states[ j ] )
                for k in range( M ):
                    O[ i, k ] = self._output_logprob( si, self._symbols[ k ] )
            S = { }
            for k in range( M ):
                S[ self._symbols[ k ] ] = k
            self._cache = (P, O, X, S)


    def _update_cache( self, symbols ):
        # add new symbols to the symbol table and repopulate the output
        # probabilities and symbol table mapping
        if symbols:
            self._create_cache( )
            P, O, X, S = self._cache
            for symbol in symbols:
                if symbol not in self._symbols:
                    self._cache = None
                    self._symbols.append( symbol )
            # don't bother with the work if there aren't any new symbols
            if not self._cache:
                N = len( self._states )
                M = len( self._symbols )
                Q = O.shape[ 1 ]
                # add new columns to the output probability table without
                # destroying the old probabilities
                O = np.hstack( [ O, np.zeros( (N, M - Q), np.float32 ) ] )
                for i in range( N ):
                    si = self._states[ i ]
                    # only calculate probabilities for new symbols
                    for k in range( Q, M ):
                        O[ i, k ] = self._output_logprob( si, self._symbols[ k ] )
                # only create symbol mappings for new symbols
                for k in range( Q, M ):
                    S[ self._symbols[ k ] ] = k
                self._cache = (P, O, X, S)


    def reset_cache( self ):
        self._cache = None


    def best_path( self, unlabeled_sequence ):
        """
        Returns the state sequence of the optimal (most probable) path through
        the HMM. Uses the Viterbi algorithm to calculate this part by dynamic
        programming.

        :return: the state sequence
        :rtype: sequence of any
        :param unlabeled_sequence: the sequence of unlabeled symbols
        :type unlabeled_sequence: list
        """
        unlabeled_sequence = self._transform( unlabeled_sequence )
        return self._best_path( unlabeled_sequence )


    def _best_path( self, unlabeled_sequence ):
        T = len( unlabeled_sequence )
        N = len( self._states )
        self._create_cache( )
        self._update_cache( unlabeled_sequence )
        P, O, X, S = self._cache

        V = np.zeros( (T, N), np.float32 )
        B = -np.ones( (T, N), np.int )

        V[ 0 ] = P + O[ :, S[ unlabeled_sequence[ 0 ] ] ]
        for t in range( 1, T ):
            for j in range( N ):
                vs = V[ t - 1, : ] + X[ :, j ]
                best = np.argmax( vs )
                V[ t, j ] = vs[ best ] + O[ j, S[ unlabeled_sequence[ t ] ] ]
                B[ t, j ] = best

        current = np.argmax( V[ T - 1, : ] )
        sequence = [ current ]
        for t in range( T - 1, 0, -1 ):
            last = B[ t, current ]
            sequence.append( last )
            current = last

        sequence.reverse( )
        return list( map( self._states.__getitem__, sequence ) )


    def best_path_simple( self, unlabeled_sequence ):
        """
        Returns the state sequence of the optimal (most probable) path through
        the HMM. Uses the Viterbi algorithm to calculate this part by dynamic
        programming.  This uses a simple, direct method, and is included for
        teaching purposes.

        :return: the state sequence
        :rtype: sequence of any
        :param unlabeled_sequence: the sequence of unlabeled symbols
        :type unlabeled_sequence: list
        """
        unlabeled_sequence = self._transform( unlabeled_sequence )
        return self._best_path_simple( unlabeled_sequence )


    def _best_path_simple( self, unlabeled_sequence ):
        T = len( unlabeled_sequence )
        N = len( self._states )
        V = np.zeros( (T, N), np.float64 )
        B = { }

        # find the starting log probabilities for each state
        symbol = unlabeled_sequence[ 0 ]
        for i, state in enumerate( self._states ):
            V[ 0, i ] = self._priors.logprob( state ) + \
                        self._output_logprob( state, symbol )
            B[ 0, state ] = None

        # find the maximum log probabilities for reaching each state at time t
        for t in range( 1, T ):
            symbol = unlabeled_sequence[ t ]
            for j in range( N ):
                sj = self._states[ j ]
                best = None
                for i in range( N ):
                    si = self._states[ i ]
                    va = V[ t - 1, i ] + self._transitions[ si ].logprob( sj )
                    if not best or va > best[ 0 ]:
                        best = (va, si)
                V[ t, j ] = best[ 0 ] + self._output_logprob( sj, symbol )
                B[ t, sj ] = best[ 1 ]

        # find the highest probability final state
        best = None
        for i in range( N ):
            val = V[ T - 1, i ]
            if not best or val > best[ 0 ]:
                best = (val, self._states[ i ])

        # traverse the back-pointers B to find the state sequence
        current = best[ 1 ]
        sequence = [ current ]
        for t in range( T - 1, 0, -1 ):
            last = B[ t, current ]
            sequence.append( last )
            current = last

        sequence.reverse( )
        return sequence


    def random_sample( self, rng, length ):
        """
        Randomly sample the HMM to generate a sentence of a given length. This
        samples the prior distribution then the observation distribution and
        transition distribution for each subsequent observation and state.
        This will mostly generate unintelligible garbage, but can provide some
        amusement.

        :return:        the randomly created state/observation sequence,
                        generated according to the HMM's probability
                        distributions. The SUBTOKENS have TEXT and TAG
                        properties containing the observation and state
                        respectively.
        :rtype:         list
        :param rng:     random number generator
        :type rng:      Random (or any object with a random() method)
        :param length:  desired output length
        :type length:   int
        """

        # sample the starting state and symbol prob dists
        tokens = [ ]
        state = self._sample_probdist( self._priors, rng.random( ), self._states )
        symbol = self._sample_probdist( self._outputs[ state ],
                                        rng.random( ), self._symbols )
        tokens.append( (symbol, state) )

        for i in range( 1, length ):
            # sample the state transition and symbol prob dists
            state = self._sample_probdist( self._transitions[ state ],
                                           rng.random( ), self._states )
            symbol = self._sample_probdist( self._outputs[ state ],
                                            rng.random( ), self._symbols )
            tokens.append( (symbol, state) )

        return tokens


    def _sample_probdist( self, probdist, p, samples ):
        cum_p = 0
        for sample in samples:
            add_p = probdist.prob( sample )
            if cum_p <= p <= cum_p + add_p:
                return sample
            cum_p += add_p
        raise Exception( 'Invalid probability distribution - '
                         'does not sum to one' )


    def entropy( self, unlabeled_sequence ):
        """
        Returns the entropy over labellings of the given sequence. This is
        given by::

            H(O) = - sum_S Pr(S | O) log Pr(S | O)

        where the summation ranges over all state sequences, S. Let
        *Z = Pr(O) = sum_S Pr(S, O)}* where the summation ranges over all state
        sequences and O is the observation sequence. As such the entropy can
        be re-expressed as::

            H = - sum_S Pr(S | O) log [ Pr(S, O) / Z ]
            = log Z - sum_S Pr(S | O) log Pr(S, 0)
            = log Z - sum_S Pr(S | O) [ log Pr(S_0) + sum_t Pr(S_t | S_{t-1}) + sum_t Pr(O_t | S_t) ]

        The order of summation for the log terms can be flipped, allowing
        dynamic programming to be used to calculate the entropy. Specifically,
        we use the forward and backward probabilities (alpha, beta) giving::

            H = log Z - sum_s0 alpha_0(s0) beta_0(s0) / Z * log Pr(s0)
            + sum_t,si,sj alpha_t(si) Pr(sj | si) Pr(O_t+1 | sj) beta_t(sj) / Z * log Pr(sj | si)
            + sum_t,st alpha_t(st) beta_t(st) / Z * log Pr(O_t | st)

        This simply uses alpha and beta to find the probabilities of partial
        sequences, constrained to include the given state(s) at some point in
        time.
        """
        unlabeled_sequence = self._transform( unlabeled_sequence )

        T = len( unlabeled_sequence )
        N = len( self._states )

        alpha = self._forward_probability( unlabeled_sequence )
        beta = self._backward_probability( unlabeled_sequence )
        normalisation = logsumexp2( alpha[ T - 1 ] )

        entropy = normalisation

        # starting state, t = 0
        for i, state in enumerate( self._states ):
            p = 2 ** (alpha[ 0, i ] + beta[ 0, i ] - normalisation)
            entropy -= p * self._priors.logprob( state )
            # print 'p(s_0 = %s) =' % state, p

        # state transitions
        for t0 in range( T - 1 ):
            t1 = t0 + 1
            for i0, s0 in enumerate( self._states ):
                for i1, s1 in enumerate( self._states ):
                    p = 2 ** (alpha[ t0, i0 ] + self._transitions[ s0 ].logprob( s1 ) +
                              self._outputs[ s1 ].logprob(
                                  unlabeled_sequence[ t1 ][ _TEXT ] ) +
                              beta[ t1, i1 ] - normalisation)
                    entropy -= p * self._transitions[ s0 ].logprob( s1 )
                    # print 'p(s_%d = %s, s_%d = %s) =' % (t0, s0, t1, s1), p

        # symbol emissions
        for t in range( T ):
            for i, state in enumerate( self._states ):
                p = 2 ** (alpha[ t, i ] + beta[ t, i ] - normalisation)
                entropy -= p * self._outputs[ state ].logprob(
                    unlabeled_sequence[ t ][ _TEXT ] )
                # print 'p(s_%d = %s) =' % (t, state), p

        return entropy


    def point_entropy( self, unlabeled_sequence ):
        """
        Returns the pointwise entropy over the possible states at each
        position in the chain, given the observation sequence.
        """
        unlabeled_sequence = self._transform( unlabeled_sequence )

        T = len( unlabeled_sequence )
        N = len( self._states )

        alpha = self._forward_probability( unlabeled_sequence )
        beta = self._backward_probability( unlabeled_sequence )
        normalisation = logsumexp2( alpha[ T - 1 ] )

        entropies = np.zeros( T, np.float64 )
        probs = np.zeros( N, np.float64 )
        for t in range( T ):
            for s in range( N ):
                probs[ s ] = alpha[ t, s ] + beta[ t, s ] - normalisation

            for s in range( N ):
                entropies[ t ] -= 2 ** (probs[ s ]) * probs[ s ]

        return entropies


    def _exhaustive_entropy( self, unlabeled_sequence ):
        unlabeled_sequence = self._transform( unlabeled_sequence )

        T = len( unlabeled_sequence )
        N = len( self._states )

        labellings = [ [ state ] for state in self._states ]
        for t in range( T - 1 ):
            current = labellings
            labellings = [ ]
            for labelling in current:
                for state in self._states:
                    labellings.append( labelling + [ state ] )

        log_probs = [ ]
        for labelling in labellings:
            labeled_sequence = unlabeled_sequence[ : ]
            for t, label in enumerate( labelling ):
                labeled_sequence[ t ] = (labeled_sequence[ t ][ _TEXT ], label)
            lp = self.log_probability( labeled_sequence )
            log_probs.append( lp )
        normalisation = _log_add( *log_probs )

        # ps = zeros((T, N), float64)
        # for labelling, lp in zip(labellings, log_probs):
        # for t in range(T):
        # ps[t, self._states.index(labelling[t])] += \
        #    2**(lp - normalisation)

        #for t in range(T):
        #print 'prob[%d] =' % t, ps[t]

        entropy = 0
        for lp in log_probs:
            lp -= normalisation
            entropy -= 2 ** (lp) * lp

        return entropy


    def _exhaustive_point_entropy( self, unlabeled_sequence ):
        unlabeled_sequence = self._transform( unlabeled_sequence )

        T = len( unlabeled_sequence )
        N = len( self._states )

        labellings = [ [ state ] for state in self._states ]
        for t in range( T - 1 ):
            current = labellings
            labellings = [ ]
            for labelling in current:
                for state in self._states:
                    labellings.append( labelling + [ state ] )

        log_probs = [ ]
        for labelling in labellings:
            labelled_sequence = unlabeled_sequence[ : ]
            for t, label in enumerate( labelling ):
                labelled_sequence[ t ] = (labelled_sequence[ t ][ _TEXT ], label)
            lp = self.log_probability( labelled_sequence )
            log_probs.append( lp )

        normalisation = _log_add( *log_probs )

        probabilities = _ninf_array( (T, N) )

        for labelling, lp in zip( labellings, log_probs ):
            lp -= normalisation
            for t, label in enumerate( labelling ):
                index = self._states.index( label )
                probabilities[ t, index ] = _log_add( probabilities[ t, index ], lp )

        entropies = np.zeros( T, np.float64 )
        for t in range( T ):
            for s in range( N ):
                entropies[ t ] -= 2 ** (probabilities[ t, s ]) * probabilities[ t, s ]

        return entropies


    def _transitions_matrix( self ):
        """ Return a matrix of transition log probabilities. """
        trans_iter = (self._transitions[ sj ].logprob( si )
                      for sj in self._states
                      for si in self._states)

        transitions_logprob = np.fromiter( trans_iter, dtype = np.float64 )
        N = len( self._states )
        return transitions_logprob.reshape( (N, N) ).T


    def _outputs_vector( self, symbol ):
        """
        Return a vector with log probabilities of emitting a symbol
        when entering states.
        """
        out_iter = (self._output_logprob( sj, symbol ) for sj in self._states)
        return np.fromiter( out_iter, dtype = np.float64 )


    def _forward_probability( self, unlabeled_sequence ):
        """
        Return the forward probability matrix, a T by N array of
        log-probabilities, where T is the length of the sequence and N is the
        number of states. Each entry (t, s) gives the probability of being in
        state s at time t after observing the partial symbol sequence up to
        and including t.

        :param unlabeled_sequence: the sequence of unlabeled symbols
        :type unlabeled_sequence: list
        :return: the forward log probability matrix
        :rtype: array
        """
        T = len( unlabeled_sequence )
        N = len( self._states )
        alpha = _ninf_array( (T, N) )

        transitions_logprob = self._transitions_matrix( )

        # Initialization
        symbol = unlabeled_sequence[ 0 ][ _TEXT ]
        for i, state in enumerate( self._states ):
            alpha[ 0, i ] = self._priors.logprob( state ) + \
                            self._output_logprob( state, symbol )

        # Induction
        for t in range( 1, T ):
            symbol = unlabeled_sequence[ t ][ _TEXT ]
            output_logprob = self._outputs_vector( symbol )

            for i in range( N ):
                summand = alpha[ t - 1 ] + transitions_logprob[ i ]
                alpha[ t, i ] = logsumexp2( summand ) + output_logprob[ i ]

        return alpha


    def _backward_probability( self, unlabeled_sequence ):
        """
        Return the backward probability matrix, a T by N array of
        log-probabilities, where T is the length of the sequence and N is the
        number of states. Each entry (t, s) gives the probability of being in
        state s at time t after observing the partial symbol sequence from t
        .. T.

        :return: the backward log probability matrix
        :rtype:  array
        :param unlabeled_sequence: the sequence of unlabeled symbols
        :type unlabeled_sequence: list
        """
        T = len( unlabeled_sequence )
        N = len( self._states )
        beta = _ninf_array( (T, N) )

        transitions_logprob = self._transitions_matrix( ).T

        # initialise the backward values;
        # "1" is an arbitrarily chosen value from Rabiner tutorial
        beta[ T - 1, : ] = np.log2( 1 )

        # inductively calculate remaining backward values
        for t in range( T - 2, -1, -1 ):
            symbol = unlabeled_sequence[ t + 1 ][ _TEXT ]
            outputs = self._outputs_vector( symbol )

            for i in range( N ):
                summand = transitions_logprob[ i ] + beta[ t + 1 ] + outputs
                beta[ t, i ] = logsumexp2( summand )

        return beta


    def test( self, test_sequence, verbose = False, **kwargs ):
        """
        Tests the HiddenMarkovModelTagger instance.

        :param test_sequence: a sequence of labeled test instances
        :type test_sequence: list(list)
        :param verbose: boolean flag indicating whether training should be
            verbose or include printed output
        :type verbose: bool
        """


        def words( sent ):
            return [ word for (word, tag) in sent ]


        def tags( sent ):
            return [ tag for (word, tag) in sent ]


        def flatten( seq ):
            return list( itertools.chain( *seq ) )


        test_sequence = self._transform( test_sequence )
        predicted_sequence = list( imap( self._tag, imap( words, test_sequence ) ) )

        if verbose:
            for test_sent, predicted_sent in izip( test_sequence, predicted_sequence ):
                print( 'Test:',
                       ' '.join( '%s/%s' % (token, tag)
                                 for (token, tag) in test_sent ) )
                print( )
                print( 'Untagged:',
                       ' '.join( "%s" % token for (token, tag) in test_sent ) )
                print( )
                print( 'HMM-tagged:',
                       ' '.join( '%s/%s' % (token, tag)
                                 for (token, tag) in predicted_sent ) )
                print( )
                print( 'Entropy:',
                       self.entropy( [ (token, None) for
                                       (token, tag) in predicted_sent ] ) )
                print( )
                print( '-' * 60 )

        test_tags = flatten( imap( tags, test_sequence ) )
        predicted_tags = flatten( imap( tags, predicted_sequence ) )

        acc = accuracy( test_tags, predicted_tags )
        count = sum( len( sent ) for sent in test_sequence )
        print( 'accuracy over %d tokens: %.2f' % (count, acc * 100) )


    def __repr__( self ):
        return ('<HiddenMarkovModelTagger %d states and %d output symbols>'
                % (len( self._states ), len( self._symbols )))


class HiddenMarkovModelTrainer( object ):
    """
    Algorithms for learning HMM parameters from training data. These include
    both supervised learning (MLE) and unsupervised learning (Baum-Welch).

    Creates an HMM trainer to induce an HMM with the given states and
    output symbol alphabet. A supervised and unsupervised training
    method may be used. If either of the states or symbols are not given,
    these may be derived from supervised training.

    :param states:  the set of state labels
    :type states:   sequence of any
    :param symbols: the set of observation symbols
    :type symbols:  sequence of any
    """


    def __init__( self, states = None, symbols = None ):
        self._states = (states if states else [ ])
        self._symbols = (symbols if symbols else [ ])


    def train( self, labeled_sequences = None, unlabeled_sequences = None,
               **kwargs ):
        """
        Trains the HMM using both (or either of) supervised and unsupervised
        techniques.

        :return: the trained model
        :rtype: HiddenMarkovModelTagger
        :param labelled_sequences: the supervised training data, a set of
            labelled sequences of observations
        :type labelled_sequences: list
        :param unlabeled_sequences: the unsupervised training data, a set of
            sequences of observations
        :type unlabeled_sequences: list
        :param kwargs: additional arguments to pass to the training methods
        """
        assert labeled_sequences or unlabeled_sequences
        model = None
        if labeled_sequences:
            model = self.train_supervised( labeled_sequences, **kwargs )
        if unlabeled_sequences:
            if model:
                kwargs[ 'model' ] = model
            model = self.train_unsupervised( unlabeled_sequences, **kwargs )
        return model


    def _baum_welch_step( self, sequence, model, symbol_to_number ):

        N = len( model._states )
        M = len( model._symbols )
        T = len( sequence )

        # compute forward and backward probabilities
        alpha = model._forward_probability( sequence )
        beta = model._backward_probability( sequence )

        # find the log probability of the sequence
        lpk = logsumexp2( alpha[ T - 1 ] )

        A_numer = _ninf_array( (N, N) )
        B_numer = _ninf_array( (N, M) )
        A_denom = _ninf_array( N )
        B_denom = _ninf_array( N )

        transitions_logprob = model._transitions_matrix( ).T

        for t in range( T ):
            symbol = sequence[ t ][ _TEXT ]  # not found? FIXME
            next_symbol = None
            if t < T - 1:
                next_symbol = sequence[ t + 1 ][ _TEXT ]  # not found? FIXME
            xi = symbol_to_number[ symbol ]

            next_outputs_logprob = model._outputs_vector( next_symbol )
            alpha_plus_beta = alpha[ t ] + beta[ t ]

            if t < T - 1:
                numer_add = transitions_logprob + next_outputs_logprob + \
                            beta[ t + 1 ] + alpha[ t ].reshape( N, 1 )
                A_numer = np.logaddexp2( A_numer, numer_add )
                A_denom = np.logaddexp2( A_denom, alpha_plus_beta )
            else:
                B_denom = np.logaddexp2( A_denom, alpha_plus_beta )

            B_numer[ :, xi ] = np.logaddexp2( B_numer[ :, xi ], alpha_plus_beta )

        return lpk, A_numer, A_denom, B_numer, B_denom


    def train_unsupervised( self, unlabeled_sequences, update_outputs = True,
                            **kwargs ):
        """
        Trains the HMM using the Baum-Welch algorithm to maximise the
        probability of the data sequence. This is a variant of the EM
        algorithm, and is unsupervised in that it doesn't need the state
        sequences for the symbols. The code is based on 'A Tutorial on Hidden
        Markov Models and Selected Applications in Speech Recognition',
        Lawrence Rabiner, IEEE, 1989.

        :return: the trained model
        :rtype: HiddenMarkovModelTagger
        :param unlabeled_sequences: the training data, a set of
            sequences of observations
        :type unlabeled_sequences: list

        kwargs may include following parameters:

        :param model: a HiddenMarkovModelTagger instance used to begin
            the Baum-Welch algorithm
        :param max_iterations: the maximum number of EM iterations
        :param convergence_logprob: the maximum change in log probability to
            allow convergence
        """

        # create a uniform HMM, which will be iteratively refined, unless
        # given an existing model
        model = kwargs.get( 'model' )
        if not model:
            priors = RandomProbDist( self._states )
            transitions = DictionaryConditionalProbDist(
                dict( (state, RandomProbDist( self._states ))
                      for state in self._states ) )
            outputs = DictionaryConditionalProbDist(
                dict( (state, RandomProbDist( self._symbols ))
                      for state in self._states ) )
            model = HiddenMarkovModelTagger( self._symbols, self._states,
                                             transitions, outputs, priors )

        self._states = model._states
        self._symbols = model._symbols

        N = len( self._states )
        M = len( self._symbols )
        symbol_numbers = dict( (sym, i) for i, sym in enumerate( self._symbols ) )

        # update model prob dists so that they can be modified
        model._priors = MutableProbDist( model._priors, self._states )

        model._transitions = DictionaryConditionalProbDist(
            dict( (s, MutableProbDist( model._transitions[ s ], self._states ))
                  for s in self._states ) )

        if update_outputs:
            model._outputs = DictionaryConditionalProbDist(
                dict( (s, MutableProbDist( model._outputs[ s ], self._symbols ))
                      for s in self._states ) )

        model.reset_cache( )

        # iterate until convergence
        converged = False
        last_logprob = None
        iteration = 0
        max_iterations = kwargs.get( 'max_iterations', 1000 )
        epsilon = kwargs.get( 'convergence_logprob', 1e-6 )

        while not converged and iteration < max_iterations:
            A_numer = _ninf_array( (N, N) )
            B_numer = _ninf_array( (N, M) )
            A_denom = _ninf_array( N )
            B_denom = _ninf_array( N )

            logprob = 0
            for sequence in unlabeled_sequences:
                sequence = list( sequence )
                if not sequence:
                    continue

                (lpk, seq_A_numer, seq_A_denom,
                 seq_B_numer, seq_B_denom) = self._baum_welch_step( sequence, model, symbol_numbers )

                # add these sums to the global A and B values
                for i in range( N ):
                    A_numer[ i ] = np.logaddexp2( A_numer[ i ], seq_A_numer[ i ] - lpk )
                    B_numer[ i ] = np.logaddexp2( B_numer[ i ], seq_B_numer[ i ] - lpk )

                A_denom = np.logaddexp2( A_denom, seq_A_denom - lpk )
                B_denom = np.logaddexp2( B_denom, seq_B_denom - lpk )

                logprob += lpk

            # use the calculated values to update the transition and output
            # probability values
            for i in range( N ):
                logprob_Ai = A_numer[ i ] - A_denom[ i ]
                logprob_Bi = B_numer[ i ] - B_denom[ i ]

                # We should normalize all probabilities (see p.391 Huang et al)
                # Let sum(P) be K.
                # We can divide each Pi by K to make sum(P) == 1.
                # Pi' = Pi/K
                # log2(Pi') = log2(Pi) - log2(K)
                logprob_Ai -= logsumexp2( logprob_Ai )
                logprob_Bi -= logsumexp2( logprob_Bi )

                # update output and transition probabilities
                si = self._states[ i ]

                for j in range( N ):
                    sj = self._states[ j ]
                    model._transitions[ si ].update( sj, logprob_Ai[ j ] )

                if update_outputs:
                    for k in range( M ):
                        ok = self._symbols[ k ]
                        model._outputs[ si ].update( ok, logprob_Bi[ k ] )

                        # Rabiner says the priors don't need to be updated. I don't
                        # believe him. FIXME

            # test for convergence
            if iteration > 0 and abs( logprob - last_logprob ) < epsilon:
                converged = True

            print( 'iteration', iteration, 'logprob', logprob )
            iteration += 1
            last_logprob = logprob

        return model


    def train_supervised( self, testing = None ):
        """
        Supervised training maximising the joint probability of the symbol and
        state sequences. This is done via collecting frequencies of
        transitions between states, symbol observations while within each
        state and which states start a sentence. These frequency distributions
        are then normalised into probability estimates, which can be
        smoothed if desired.

        :return: the trained model
        :rtype: HiddenMarkovModelTagger
        :param labelled_sequences: the training data, a set of
            labelled sequences of observations
        :type labelled_sequences: list
        :param estimator: a function taking
            a FreqDist and a number of bins and returning a CProbDistI;
            otherwise a MLE estimate is used
        """




        #
        # known_symbols = set(self._symbols)
        # known_states = set(self._states)
        #
        #
        # outputs = ConditionalFreqDist( )
        #
        #
        # while True:
        #
        # labelled_sequences = yield
        #
        #     if labelled_sequences is None:
        #         break
        #
        #     print("TRAINING HMM")
        #
        #
        #     for sequence in labelled_sequences:
        #
        #
        #         for token in sequence:
        #             state = token[_TAG]
        #             symbol = token[_TEXT]
        #
        #             if state == symbol:
        #                 continue
        #
        #
        #             outputs[state][symbol] += 1
        #
        #
        #
        #             # update the state and symbol lists
        #             if state not in known_states:
        #                 self._states.append(state)
        #                 known_states.add(state)
        #
        #             if symbol not in known_symbols:
        #                 self._symbols.append(symbol)
        #                 known_symbols.add(symbol)
        #
        #
        #
        #
        # with open('PickledData/HMM_data/outputs_FIXED1.pickle','wb') as pklOutputs,\
        #     open('PickledData/HMM_data/symbols1.pickle','wb') as pklSymbols,\
        #     open('PickledData/HMM_data/states1.pickle','wb') as pklStates:
        #
        #     pickle.dump(outputs,pklOutputs,pickle.HIGHEST_PROTOCOL)
        #     pickle.dump(self._symbols,pklSymbols,pickle.HIGHEST_PROTOCOL)
        #     pickle.dump(self._states,pklStates,pickle.HIGHEST_PROTOCOL)
        #
        # print("FINISHED PICKLING HMM DATA")
        #
        # return




        with open( 'PickledData/HMM_data/transitionsBW_pruned.pickle', 'rb' ) as pklTransitions, \
                open( 'PickledData/HMM_data/outputs_FIXED1_final.pickle', 'rb' ) as pklOutputs, \
                open( 'PickledData/HMM_data/startingBW.pickle', 'rb' ) as pklStarting, \
                open( 'PickledData/HMM_data/symbols1.pickle', 'rb' ) as pklSymbols, \
                open( 'PickledData/HMM_data/states1.pickle', 'rb' ) as pklStates:

            transitions = pickle.load( pklTransitions )

            globalModelParameters.outputsModel = pickle.load( pklOutputs )
            starting = pickle.load( pklStarting )

            self._symbols = pickle.load( pklSymbols )
            self._states = pickle.load( pklStates )

        #space followed by space removed
        try:
            transitions[ ' ' ].pop( ' ' )
            starting.pop( ' ' )
        except KeyError:
            print( "no double spaces found" )
            pass


            #('Laplace', LaplaceProbDist),
            #('Lidstone_003', Lidstone_003),
            #('GoodTuring', SimpleGoodTuringProbDist),
            #('WittenBell', WittenBellProbDist),
            # ('Lidstone_07',Lidstone_07),
            #('Laplace', LaplaceProbDist),
            #('Lidstone_03', Lidstone_03),


        if testing is not None:
            estimators = OrderedDict( [
                                        ('ELEProbDist',ELEProbDist),
                                         ] )



            size_state_alphabet = 22765
            global size_output_alphabet
            size_output_alphabet = 219661

            #for name_estimator_output, estimator_output in estimators.items( ):

            for name_estimator_transition, estimator_transition in estimators.items( ):


                N_s = size_state_alphabet
                N_o = size_output_alphabet

                pi = estimator_transition( starting, N_s )

                A = ConditionalProbDist( transitions, estimator_transition, N_s )

                B = ConditionalProbDist( globalModelParameters.outputsModel, WittenBellProbDist, N_o, )

                yield (('O:', 'WittenBell',
                        'T:', name_estimator_transition,
                        'S:', name_estimator_transition),
                       HiddenMarkovModelTagger( self._symbols, self._states, A, B, pi ))





def _ninf_array( shape ):
    res = np.empty( shape, np.float64 )
    res.fill( -np.inf )
    return res


def logsumexp2( arr ):
    max_ = arr.max( )
    return np.log2( np.sum( 2 ** (arr - max_) ) ) + max_


def _log_add( *values ):
    """
    Adds the logged values, returning the logarithm of the addition.
    """
    x = max( values )
    if x > -np.inf:
        sum_diffs = 0
        for value in values:
            sum_diffs += 2 ** (value - x)
        return x + np.log2( sum_diffs )
    else:
        return x


def _create_hmm_tagger( states, symbols, A, B, pi ):
    def pd( values, samples ):
        d = dict( zip( samples, values ) )
        return DictionaryProbDist( d )


    def cpd( array, conditions, samples ):
        d = { }
        for values, condition in zip( array, conditions ):
            d[ condition ] = pd( values, samples )
        return DictionaryConditionalProbDist( d )


    A = cpd( A, states, states )
    B = cpd( B, states, symbols )
    pi = pd( pi, states )
    return HiddenMarkovModelTagger( symbols = symbols, states = states,
                                    transitions = A, outputs = B, priors = pi )


def _untag( sentences ):
    unlabeled = [ ]
    for sentence in sentences:
        unlabeled.append( [ (token[ _TEXT ], None) for token in sentence ] )
    return unlabeled


if __name__ == "__main__":
    pass

