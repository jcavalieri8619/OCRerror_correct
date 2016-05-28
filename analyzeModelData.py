__project__ = 'OCRErrorCorrectpy3'
__author__ = 'jcavalie'
__email__ = "Jcavalieri8619@gmail.com"
__date__ = '1/11/15'


import pickle


def effectOfHMMsource():

    with open('./PickledData/firstModelData.pickle','rb') as pkl:
        dataDict=pickle.load(pkl)


    data = list(dataDict.values())

    print(type(data))
    print(type(data[0]))

    data_count=0

    correctCount=0
    origCorrect=0

    for pair in data[0]:

        intendedWrd,candidateLst = pair

        if intendedWrd.count(' ')  > 0:
            continue

        data_count +=1

        origLst=candidateLst.copy()


        for candidateDct in origLst:

            candidateDct['totalProb'] -= candidateDct['HMMsource']

        origLst.sort(key=lambda x:x['totalProb'], reverse=True)

        if origLst[0]['candidate'] == intendedWrd:
            correctCount+=1

        if candidateLst[0]['candidate'] == intendedWrd:
            origCorrect+=1

    print("orig accuracy:",origCorrect/data_count)
    print("no HMMsource accuracy:",correctCount/data_count)


if __name__=='__main__':

    print("starting")
    effectOfHMMsource()
    print("finished")

