import requests
import json
import datetime
import threading
from flask import Flask, jsonify, request
from flask import render_template
app = Flask(__name__)

def getIssuesContributions (author, dateFrom, dateUntil):
    
    try:
        datetime.datetime.strptime(dateFrom, '%Y-%m-%d')
        dateUntilObject = datetime.datetime.strptime(dateUntil, '%Y-%m-%d')
    except ValueError:
        print("Debug: getIssuesContributions: Error:Incorrect data format, should be YYYY-MM-DD")
        return
    
    url ='https://api.github.com/search/issues?q=""+author:"'+author+'"+type:"issue"+created:">='+dateFrom+'"+&sort=created&order=desc'
    print("Hitting url: "+url)
    r = requests.get(url, auth=(userName, password))
    rJson = r.json()
    
    ##Check if json contains "message" for errors, it yes, return
    if 'message' in rJson:
        print('Debug: getIssuesContributions: Error: '+rJson['message'])
        return

    for create in range (0,len(rJson['items'])):
        date = str(rJson['items'][create]['created_at']).split('T')[0]
        # print('IssueDate: '+date)
        if datetime.datetime.strptime(date, '%Y-%m-%d') <= dateUntilObject:
            issuesDatesMap[date] = issuesDatesMap.get(date, 0) + 1

def getPrContributions (author, dateFrom, dateUntil):
    #Date Format check
    try:
        datetime.datetime.strptime(dateFrom, '%Y-%m-%d')
        dateUntilObject = datetime.datetime.strptime(dateUntil, '%Y-%m-%d')
    except ValueError:
        print("Debug: getPrContributions: Error: Incorrect data format, should be YYYY-MM-DD")
        return

    url ='https://api.github.com/search/issues?q=""+author:"'+author+'"+type:"pr"+created:">='+dateFrom+'"+&sort=created&order=desc'
    print("Hitting url: "+url)
    r = requests.get(url, auth=(userName, password))
    rJson = r.json()

    ##Check if json contains "message" for errors, it yes, return
    if 'message' in rJson:
        print('Debug: getPrContributions: Error: '+rJson['message'])
        return
    
    for create in range (0,len(rJson['items'])):
        forkedFromRepo = requests.get(rJson['items'][create]['repository_url'], auth=(userName, password))
        forkedFromRepoJson = forkedFromRepo.json()
        if not forkedFromRepoJson['fork']:
            date = str(rJson['items'][create]['created_at']).split('T')[0]
            # print('PrDate: '+date)

            ##TODO: Add date check here
            if datetime.datetime.strptime(date, '%Y-%m-%d') <= dateUntilObject:
                prDatesMap[date] = prDatesMap.get(date, 0) + 1

def getRepos (user):
    # url = 'https://api.github.com/users/'+user+'/repos'
    url = 'https://api.github.com/user/repos'
    r = requests.get(url, auth=(userName, password))
    rJson = r.json()
    reposList = []
    
    ##Check if json contains "message" for errors, it yes, break
    if 'message' in rJson:
        print('Debug: getRepos: Error: '+rJson['message'])
        return

    for index in range (0,len(rJson)):
        ##Considering only master repositories
        if rJson[index]['fork'] == False: 
            # print(rJson[index]['name'])
            reposList.append(rJson[index]['name'])
    return reposList
    #print(rJson)

def getCommitsContributions (author, dateSince, dateUntil):

    #Date Format check
    try:
        dateFromObject = datetime.datetime.strptime(dateSince, '%Y-%m-%d')
        dateUntilObject =  datetime.datetime.strptime(dateUntil, '%Y-%m-%d')
    except ValueError:
        print("Debug: getCommitsContributions: Error: Incorrect data format, should be YYYY-MM-DD")
        return

    ## Getting all the master repos
    reposList = getRepos(author)

    ## Null check for reposList
    if reposList:
        for repoName in reposList:
            #Getting all commits on each repo
            url ='https://api.github.com/repos/'+author+'/'+repoName+'/commits'
            print('Hitting: '+url)
            r = requests.get(url, auth=(userName, password))
            rJson = r.json()
            # print(len(rJson))

            ##Check if json contains "message" for errors, if yes, return
            if 'message' in rJson:
                print('Debug: getCommitsContributions: Error: '+rJson['message'])
                return

            for eachCommit in range (0,len(rJson)):
                if rJson[eachCommit]['author']:
                    if rJson[eachCommit]['author']['login'] == author:
                        # print(rJson[eachCommit]['author']['login'])
                        date = str(rJson[eachCommit]['commit']['author']['date']).split('T')[0]
                        # print(date)
                        #TODO: Add date Until check
                        dateObject = datetime.datetime.strptime(date, '%Y-%m-%d')
                        if (dateObject >= dateFromObject and dateObject <= dateUntilObject):
                            commitDatesMap[date] = commitDatesMap.get(date, 0) + 1

def printDictContents():
    # To print contents while Debugging
    print("\nPrinting Issues Map")
    print(issuesDatesMap)

    print("\nPrinting Pr Map")
    print(prDatesMap)

    print("\nPrinting Commits Map")
    print(commitDatesMap)

def mergeAllDictionaries():
    ##Merging all the Maps
    for key in issuesDatesMap:
        datesMap[key] = issuesDatesMap.get(key, 0) + datesMap.get(key, 0)

    for key in prDatesMap:
        datesMap[key] = prDatesMap.get(key, 0) + datesMap.get(key, 0)

    for key in commitDatesMap:
        datesMap[key] = commitDatesMap.get(key, 0) + datesMap.get(key, 0)


@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/loginSuccess.html")
def loginSuccess():
    #return render_template('login.html')
    global userName
    global password
    userName = request.args.get('uname')
    password = request.args.get('psw')
    # print(userName)
    # print(password)
    return render_template('home.html')

@app.route("/")
def endPoint():
    # s = requests.session()
    global datesMap
    global issuesDatesMap
    global prDatesMap
    global commitDatesMap
    ## Clearing maps for each request
    issuesDatesMap = {}
    prDatesMap = {}
    commitDatesMap = {}
    datesMap = {}

    ##Enter the target user for contributions
    # getContributionsForUser = input('\nEnter the github handle of the User whose contributions you want to check\n')
    getContributionsForUser = request.args.get('toUser')

    ## Select one year mode or specific dates mode
    oneYearMode = '1'
    oneYearCheckbox = request.args.get('oneYearValue')
    if(oneYearCheckbox == 'date'):
        oneYearMode = '2'
    
    ## Input dates in case of Specific dates mode
    if (oneYearMode == '2'):
        inputDateFrom = request.args.get('datefrom')
        inputDateTo = request.args.get('dateto')
        dateFrom = inputDateFrom
        dateUntil = inputDateTo

    ##Calculating one year ago date
    todaysDate = datetime.datetime.now().date()
    if (oneYearMode == '1'):
        oneYearAgoDate = todaysDate - datetime.timedelta(365)
        dateFrom = str(oneYearAgoDate)
        dateUntil = str(todaysDate)

    print('Getting Contibutions from Date: ' + dateFrom + ' to Date: '+dateUntil)

    ##Get Number of Issues
    # print('Printing Issues:')
    #getIssuesContributions(getContributionsForUser, str(oneYearAgoDate))
    getIssuesThread = threading.Thread(target=getIssuesContributions, args=(getContributionsForUser, dateFrom, dateUntil))
    getIssuesThread.start()

    ##Get Number of Pull requests
    # print('\nPrinting Pull Requests:')
    #getPrContributions(getContributionsForUser, str(oneYearAgoDate))
    getPrThread = threading.Thread(target=getPrContributions, args=(getContributionsForUser, dateFrom, dateUntil))
    getPrThread.start()

    print('\n')
    #getCommitsContributions(getContributionsForUser,'','')
    getCommitsThread = threading.Thread(target=getCommitsContributions, args=(getContributionsForUser, dateFrom, dateUntil))
    getCommitsThread.start()

    ##Ensuring all the threads complete
    main_thread = threading.main_thread()
    for t in threading.enumerate():
        if t is main_thread:
            continue
        t.join()

    printDictContents()
    mergeAllDictionaries()

    print('\nPrinting Final Dates Map:')
    print(datesMap)

    print('\n')
    contributionsList = []
    for index in range(0, 365):
        date = todaysDate - datetime.timedelta(365-index)
        contributions = datesMap.get(str(date), 0)
        contributionsList.append(contributions)

    print(contributionsList)
    return jsonify(datesMap)


