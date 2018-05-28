import re
import sys
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen
from pandas import Series, DataFrame
from enchant.checker import SpellChecker

inputname, outputname, logname = '', '', ''

def cleanhtml(text):

    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, ' ', text)

    return cleantext

def unescape(text):

    text = text.replace('&amp;', '&').replace('&quot;', '"').replace('&apos;', "'").replace('&lt;', '<').replace('&gt;', '>')

    return text

def init():

    global inputname, outputname, logname
    args = sys.argv[0:]
    optionLen = len(args)

    if len(args) <= 1:
        print ('[ERR] There is no option.')
        return False

    for i in range(optionLen-1):
        if args[i].upper() == '-I':	# -I: input file name
            data = str(args[i+1])
            inputname = data
        elif args[i].upper() == '-O':	# -O: output file name
            data = str(args[i+1])
            outputname = data
        elif args[i].upper() == '-L':	# -L: log file name
            data = str(args[i+1])
            logname = data

    if inputname == '' and outputname == '' and logname == '':
        print ('[ERR] Please enter names for the input, output and log file.')
        return False
    elif inputname == '' or inputname.find('.csv') < 0:
        print ('[ERR] Please enter name for the input file and be sure to include ".csv" in input file name.')
        return False
    elif outputname == '' or outputname.find('.csv') < 0:
        print ('[ERR] Please enter name for the output file and be sure to include ".csv" in input file name.')
        return False
    elif logname == '' or logname.find('.log') < 0:
        print ('[ERR] Please enter name for the log file name and be sure to include ".log" in log file name.')
        return False

    return True

if __name__ == '__main__':

    count = 0
    text, output = '', ''
    chkr = SpellChecker("en_US")
    result = DataFrame(columns=('misspelling', 'url', 'num'))
    excludedwords = 'www,href,http,https,html,br'

    if init():
        f = open(logname, 'w')
        df = pd.read_csv(inputname)
        print (df.to_string())

        for link in df['link']:
            html = urlopen(link)
            soup = BeautifulSoup(html, 'lxml')
            output = output + '\n* ' + link
            print ('* %s' %link)
            for text in soup.findAll('p'):
                text = unescape(" ".join(cleanhtml(str(text)).split()))
                output = output + '\n + ' + text
                print (' + %s' %text)
                chkr.set_text(text)
                for err in chkr:
                    if excludedwords.find(str(err.word)) < 0:
                        count = count + 1
                        adding = '[ERR] (' + str(count) + ') ' + str(err.word)
                        print ('%s' %adding)
                        output = output + '\n' + adding
                        rows = [str(err.word), link, -1]
                        result.loc[len(result)] = rows

        result.sort_values(by=['misspelling', 'url'], ascending=[True, True], inplace=True)
        result.index = range(len(result))
        print (result.to_string())
        f.write(output)
        f.close()

        result.loc[result['misspelling'] == 'AWS', 'num'] = len(result.loc[result['misspelling'] == 'AWS'])
        result.to_csv(outputname, header=True, index=True)
    else:
        print ('[ERR] Initialization faliure')
