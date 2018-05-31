__author__ = 'electopx@gmail.com'

import re
import sys
import time
import argparse
import threading
import http.client
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.request import Request
from pandas import Series, DataFrame
from urllib.error import URLError, HTTPError

http.client.HTTPConnection._http_vsn = 10
http.client.HTTPConnection._http_vsn_str = 'HTTP/1.0'

start = time.time()
num, maxnum = 0, 0
maxthreadsnum = 15	# If the performance of your PC is low, please adjust this value to 5 or less.
cu, du, url, prefix, path = '', '', '', '', ''
rdf = DataFrame(columns=('parent', 'link', 'code'))
df = DataFrame(columns=('parent', 'link', 'visited'))
userAgentString = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36"

def init():

    global maxthreadsnum
    global cu, du, url, prefix		# cu: current URL, du: domain URL
    parser = argparse.ArgumentParser()
    parser.add_argument("-T", "--target-url", help="Target URL to test")
    parser.add_argument("-M", "--max-thread", type=int, help="Maximum number of threads")
    args = parser.parse_args()
    if args.target_url:
        url = str(args.target_url)
        up = urlparse(url)
        if all([up.scheme, up.netloc]) and up.scheme.find('http')>=0:
            prefix = up.scheme + "://"
            du = up.netloc
            cu = du + up.path

        else:
            print ('[ERR] Please be sure to include "http://" or "https://" in the target URL.')
            return False
        
    else:
        print ('[ERR] Please input required target URL.')
        return False
    if args.max_thread:
        maxthreadsnum = int(args.max_thread)

    return True

# Deletion the last '/' of the target URL
def checkTail(str):
    return str.rstrip('/').rstrip()

def getCode(tu):
    global rdf		# rdf: data frame for final result
    global start, num
    code = ''
    status = False
    req = None
    html = None

    try:
        req = Request(tu)
        req.add_header('User-Agent', userAgentString)
        html = urlopen(req)
        code = str(html.status)
        print('\n[OK] The server could fulfill the request to\n%s' %tu)
        status = True
    except HTTPError as e:
        code = str(e.code)
        print('\n[ERR] HTTP Error: The server couldn\'t fulfill the request to\n%s' %tu)
    except URLError as e:
        code = e.reason
        print('\n[ERR] URL ERror: We failed to reach in\n%s\n+ %s' %(tu, code))

    parent = df.loc[df['link']==tu, 'parent'].item()
    rows = {'parent':parent, 'link': tu, 'code': code}
    rdf = rdf.append(rows, ignore_index=True)
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
    return (status, html)

def getLink(tu, visited):
    global df	# df: data frame
    global cu, maxnum, num	# maxnum: maximum number of data frame
    excludedfiles = '.ico.png.jpg.jpeg.gif.pdf.bmp.tif.svg.pic.rle.psd.pdd.raw.ai.eps.iff.fpx.frm.pcx.pct.pxr.sct.tga.vda.icb.vst'

    if visited:
        #print ('[OK] It\'s already visited to the URL below and skip.\n%s\n' %tu)
        return False

    if len(df.loc[df['link'] == tu]) > 0:
        df.loc[df['link'] == tu, 'visited'] = True
    else:
        num = num + 1
        rows = ["", tu, True, 0]
        df.loc[len(df)] = rows

    (status, html) = getCode(tu)
    if status == False:
        return False

    tokens = tu.split('/')
    lasttoken = tokens[-1]

    if lasttoken.find('#') >= 0 or lasttoken.find('?') >= 0 or lasttoken.find('%') >= 0 or excludedfiles.find(lasttoken[-4:]) >= 0:
        print ('+ This "%s" is skipped because it`s not the target of the getLink().' %lasttoken)
        return False
    else:
        try:
            soup = BeautifulSoup(html.read().decode('utf-8','ignore'), 'lxml')
        except Exception as e:
            print('+ %s' %str(e))

        for link in soup.findAll('a', attrs={'href': re.compile('^http|^/')}):
            nl = link.get('href')	# nl: new link
            nl = checkTail(nl)
            if nl.startswith("/"):
                if nl.find('//') < 0:
                    nl = prefix + du + nl
                else:
                    nl = prefix.replace('//', '') + nl
            if nl.find(cu) >= 0 and nl != tu:
                maxnum = maxnum + 1
                if len(df.loc[df['link'] == nl]) == 0:
                    rows = {'parent':tu, 'link':nl, 'visited':False}
                    df = df.append(rows, ignore_index=True)
                    num = num + 1
                    print ('+ Adding rows(%d):\n%s'%(num, rows))

        return True

def runMultithread(tu):

    global maxthreadsnum
    threadsnum = 0

    if len(df) == 0:
        getLink(tu, False)
        print ('First running with getLink()')

    threads = [threading.Thread(target=getLink, args=(durl[1], durl[2])) for durl in df.values]
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

    rdf.sort_values(by=['link', 'parent'], ascending=[True, True], inplace=True)
    rdf.drop_duplicates(subset=['link', 'parent'], inplace=True, keep='first')
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
