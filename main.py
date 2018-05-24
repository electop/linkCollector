import re
import sys
import time
import threading
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.request import urlopen
from pandas import Series, DataFrame
from urllib.error import URLError, HTTPError

start = time.time()
num, maxnum, count = 1, 0, 0
cu, du, url, prefix, path = '', '', '', '', ''
df = DataFrame(columns=('link', 'visited'))
rdf = DataFrame(columns=('link', 'code'))

def init():

    global cu, du, url, prefix		# cu: current URL, du: domain URL
    args = sys.argv[0:]
    optionLen = len(args)

    if (len(args) <= 1):
        print ('[ERR] There is no option.')
        return False

    for i in range(optionLen-1):
        if args[i].upper() == '-T':	# -T: Target URL
            data = str(args[i+1])
            url = data
            break

    if (url == ''):
        print ('[ERR] Please input required target URL.')
        return False
    elif url.find('http://') >= 0:
        prefix = 'http://'
        cu = url.replace('http://', '')
    elif url.find('https://') >= 0:
        prefix = 'https://'
        cu = url.replace('https://', '')
    else:
        print ('[ERR] Please be sure to include "http://" or "https://" in the target URL.')
        return False

    tokens = url.split('/')
    du = tokens[2]

    return True

# Deletion the last '/' of the target URL
def checkTail(str):

    if str[len(str) - 1] == '/':
        return str.rstrip('/')
    else:
        return str

def indicator(counts):

    global start

    end = time.time()
    cs = end - start
    cm = cs // 60
    cs = "{0:.1f}".format(cs % 60)
    if counts == 1:
        print ('+ Searching target URL: %d(min) %s(sec)' %(cm, cs))
    else:
        nums = len(df)
        sv = "{0:.1f}".format((counts * 100) / nums) + '%'
        print ('+ Searching %s(%d/%d): %d(min) %s(sec)' %(sv, counts, nums, cm, cs))

    return True

def getCode(tu):

    global rdf, count	# rdf: data frame for final result, count: # data frame excluding duplication
    code = ''
    status = False

    try:
        code = str(urlopen(tu).getcode())
        print('\n[OK] The server could fulfill the request to\n%s' %tu)
        status = True
    except HTTPError as e:
        code = str(e.code)
        print('\n[ERR] HTTP Error: The server couldn\'t fulfill the request to\n%s' %tu)
    except URLError as e:
        code = e.reason
        print('\n[ERR] URL ERror: We failed to reach\n%s\n+ %s' %(tu, code))

    count = count + 1
    rows = [tu, code]
    rdf.loc[len(rdf)] = rows
    indicator(count)

    return status

def getLink(tu, visited):

    global df, maxnum	# df: data frame, maxnum: maximum # of data frame

    if visited == 1:
        return False
    elif getCode(tu):
        rows = [tu, 1]
        df.loc[len(df)] = rows
        html = urlopen(tu)
        soup = BeautifulSoup(html, 'lxml')
        for link in soup.findAll('a', attrs={'href': re.compile('^http')}):
            nl = link.get('href')	# nl: new link
            nl = checkTail(nl)
            if nl.find(cu) > 0 and nl != tu:
                maxnum += 1
                rows = [nl, 0]
                df.loc[len(df)] = rows
                #print ('+ Adding rows:\n', rows)
        for link in soup.findAll('a', attrs={'href': re.compile('^/')}):
            nl = link.get('href')
            if nl.find('//') != 0:
                nl = prefix + du + nl
            else:
                nl = prefix.replace('//', '') + nl
            nl = checkTail(nl)
            if nl.find(cu) > 0:
                maxnum += 1
                rows = [nl, 0]
                df.loc[len(df)] = rows
                #print ('+ Adding rows:\n', rows)
        df.sort_values(by=['visited', 'link'], ascending=[False, True], inplace=True)
        df.drop_duplicates(subset='link', inplace=True, keep='first')
        df.index = range(len(df))
        #num = len(df)
        return True
    else:
        rows = [tu, 1]
        df.loc[len(df)] = rows
        return False

def runMutithread(tu):

    threadingnum = 0

    if len(df) == 0:
        getLink(tu, 0)

    threads = [threading.Thread(target=getLink, args=(durl[0], durl[1])) for durl in df.values]
    for thread in threads:
        threadingnum = threading.active_count()
        while threadingnum > 5:
            time.sleep(0.5)
            threadingnum = threading.active_count()
            print ('+ Waiting 0.5 seconds to prevent threading overflow.')
        thread.start()
    for thread in threads:
        thread.join()

def result(tu):

    global df, path

    rdf.sort_values(by='link', ascending=True, inplace=True)
    rdf.drop_duplicates(subset='link', inplace=True, keep='first')
    rdf.index = range(len(rdf))
    print ('[OK] Result')
    print (rdf)
    target = tu.replace('://','_').replace('/','_')
    path = datetime.now().strftime('%Y-%m-%d_%H-%M_') + target + '.csv'
    rdf.to_csv(path, header=True, index=True)

    return len(rdf)

if __name__ == "__main__":

    if init():
        while count == 0 or count < len(df):
            runMutithread(url)
        dnum = result(url)
        end = time.time()
        cs = end - start
        cm = cs // 60
        cs = "{0:.1f}".format(cs % 60)
        print ('\n[OK] The total number of links is %d.' %maxnum)
        print ('[OK] Mission complete: The number of links excluding duplication is %d.' %dnum)
        print ('[OK] The total running time is %d(min) %s(sec).' %(cm, cs))
        print ('[OK] Please check the result file. (./%s)' %path)
    else:
        print ('[ERR] Initialization faliure')
