__author__ = 'jcavalie'


def determineErrWindows( alignedChars, ErrStats, ErrStats_lock ):
    '''

    @param alignedSource:
    @type alignedSource: list
    @param alignedTarget:
    @type alignedTarget: list
    @return:
    @rtype: tuple
    '''

    OBSERVED = 0
    HIDDEN = 1

    win_start = 0
    win_stop = 0
    error_windows = list( )
    win_flag = False

    errorLength = 0

    for itr, alignment in enumerate( alignedChars ):

        if alignment[ OBSERVED ]:
            errorLength += 1

        if alignment[ OBSERVED ] != alignment[ HIDDEN ] and win_flag == False:
            win_start = itr
            win_flag = True

        elif win_flag == True and alignment[ OBSERVED ] == alignment[ HIDDEN ]:
            win_stop = itr
            error_windows.append( (win_start, win_stop - 1) )
            win_flag = False

    else:
        if win_flag == True:
            win_stop = itr
            error_windows.append( (win_start, win_stop) )


    #if consecutive windows separated by single char
    #then create new window spanning entire range;
    #remove both old windows

    mod_error_wins=[]
    tobe_removed=[]
    for indx,win in enumerate(error_windows):

        if not indx:
            continue

        if len(mod_error_wins) and (mod_error_wins[-1][1]-win[0]) == -2:

            new_win=(mod_error_wins[-1][0],win[1])
            mod_error_wins.pop()
            tobe_removed.append(win)
            mod_error_wins.append(new_win)

        elif (error_windows[indx-1][1]-win[0]) == -2:

            new_win=(error_windows[indx-1][0],win[1])
            mod_error_wins.append(new_win)
            tobe_removed.append(win)
            tobe_removed.append(error_windows[indx-1])


    for item in tobe_removed:
        error_windows.remove(item)

    error_windows.extend(mod_error_wins)

    error_windows.sort(key=lambda arg:arg[0])




    if ErrStats:
        with ErrStats_lock:
            # length of tuple is number of error windows and each tuple value represents length of that window
            ErrStats.updateDistribution( 'errorLen_sizeErrorWins', errorLength,
                                         tuple( list(
                                             map( lambda window: window[ 1 ] - window[ 0 ] + 1, error_windows ) ) ) )

            totalEditDist = 0
            for win in error_windows:
                errWinSize = win[ 1 ] - win[ 0 ] + 1
                ErrStats.updateDistribution( 'sizeErrorWins', errWinSize )
                totalEditDist += errWinSize
            else:
                ErrStats.updateDistribution( 'editDist_numErrorWins', totalEditDist, len( error_windows ) )

            ErrStats.updateDistribution( 'numErrorWins', len( error_windows ) )

    return alignedChars, error_windows