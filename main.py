__author__ = 'electopx@gmail.com'

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
num, maxnum = 0, 0
maxthreadsnum = 15	# If the performance of your PC is low, please adjust this value to 5 or less.
cu, du, url, prefix, path = '', '', '', '', ''
rdf = DataFrame(columns=('link', 'code'))
df = DataFrame(columns=('link', 'visited'))

def init():

    global maxthreadsnum
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
        elif args[i].upper() == '-M':	# -M: Maximun number of threads
            data = str(args[i+1])
            maxthreadsnum = int(data)

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

def getCode(tu):

    global rdf		# rdf: data frame for final result
    global start, num
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
        print('\n[ERR] URL ERror: We failed to reach in\n%s\n+ %s' %(tu, code))

    rows = [tu, code]
    rdf.loc[len(rdf)] = rows
    counts = len(rdf)

    end = time.time()
    cs = end - start
    cm = cs // 60
    cs = "{0:.1f}".format(cs % 60)

    if counts == 1:
        print ('+ Searching target URL: %d(min) %s(sec)' %(cm, cs))
    else:
        sv = "{0:.1f}".format((counts * 100) / num) + '%'
        print ('+ Searching %s(%d/%d, %d): %d(min) %s(sec)' %(sv, counts, num, maxnum, cm, cs))

    return status

def getLink(tu, visited):

    global df	# df: data frame
    global cu, maxnum, num	# maxnum: maximum # of data frame
    excludedfiles = '.ico.png.jpg.jpeg.gif.pdf.bmp.tif.svg.pic.rle.psd.pdd.raw.ai.eps.iff.fpx.frm.pcx.pct.pxr.sct.tga.vda.icb.vst'

    if visited:
        #print ('[OK] It\'s already visited to the URL below and skip.\n%s\n' %tu)
        return False

    if len(df.loc[df['link'] == tu]) > 0:
        df.loc[df['link'] == tu, 'visited'] = True
    else:
        num = num + 1
        rows = [tu, True]
        df.loc[len(df)] = rows

    status = getCode(tu)
    if status == False:
        return False

    tokens = tu.split('/')
    lasttoken = tokens[len(tokens) - 1]
    if lasttoken.find('#') > 0 or lasttoken.find('?') > 0 or lasttoken.find('%') > 0 or excludedfiles.find(lasttoken[-4:]) > 0:
        print ('+ This "%s" is skipped because it`s not the target of the getLink().' %lasttoken)
        return False
    else:
        html = urlopen(tu)
        soup = BeautifulSoup(html, 'lxml')
        for link in soup.findAll('a', attrs={'href': re.compile('^http')}):
            nl = link.get('href')	# nl: new link
            nl = checkTail(nl)
            if nl.find(cu) >= 0 and nl != tu:
                maxnum = maxnum + 1
                if len(df.loc[df['link'] == nl]) == 0:
                    rows = [nl, False]
                    df.loc[num] = rows
                    num = num + 1
                    print ('+ Adding rows(%d):\n%s'%(num, rows))
        for link in soup.findAll('a', attrs={'href': re.compile('^/')}):
            nl = link.get('href')
            if nl.find('//') < 0:
                nl = prefix + du + nl
            else:
                nl = prefix.replace('//', '') + nl
            nl = checkTail(nl)
            if nl.find(cu) >= 0 and nl != tu:
                maxnum = maxnum + 1
                if len(df.loc[df['link'] == nl]) == 0:
                    rows = [nl, False]
                    df.loc[num] = rows
                    num = num + 1
                    print ('+ Adding rows(%d):\n%s' %(num, rows))
        return True

def runMultithread(tu):

    global maxthreadsnum
    threadsnum = 0

    if len(df) == 0:
        getLink(tu, False)
        print ('First running with getLink()')

    threads = [threading.Thread(target=getLink, args=(durl[0], durl[1])) for durl in df.values]
    for thread in threads:
        threadsnum = threading.active_count()
        while threadsnum > maxthreadsnum:
            time.sleep(0.5)
            threadsnum = threading.active_count()
            print ('+ Waiting 0.5 seconds to prevent threading overflow.')
        try:
            thread.start()
        except:
            print ('[ERR] Caught an exception of "thread.start()".')
    for thread in threads:
        try:
            thread.join()
        except:
            print ('[ERR] Caught an exception of "thread.join()".')

def result(tu, cm, cs):

    global rdf, df, path, num

    #rdf.sort_values(by=['code', 'link'], ascending=[False, True], inplace=True)
    rdf.sort_values(by='link', ascending=True, inplace=True)
    rdf.drop_duplicates(subset='link', inplace=True, keep='first')
    rdf.index = range(len(rdf))
    count = num
    num = len(rdf)
    print ('+ updating the total number of links from %d to %d' %(count, num))

    print ('[OK] Result')
    print (rdf.to_string())
    #print (df.to_string())

    target = tu.replace('://','_').replace('/','_')
    path = datetime.now().strftime('%Y-%m-%d_%H-%M_')
    path = path + '_' + cm + '(min)' + cs + '(sec)_' + target + '.csv'
    rdf.to_csv(path, header=True, index=True)
    #df.to_csv('df_' + path, header=True, index=True)

    return len(rdf)

if __name__ == "__main__":

    if init():
        while len(df) == 0 or len(df.loc[df['visited'] == 0]) > 0:
            runMultithread(url)
        end = time.time()
        cs = end - start
        cm = str(int(cs // 60))
        cs = "{0:.1f}".format(cs % 60)
        dnum = result(url, cm, cs)
        print ('\n[OK] The total number of links is %d.' %maxnum)
        print ('[OK] Mission complete: The number of links excluding duplication is %d.' %dnum)
        print ('[OK] The total running time is %s(min) %s(sec).' %(cm, cs))
        print ('[OK] Please check the result file. (./%s)' %path)
    else:
        print ('[ERR] Initialization faliure')
