from enchant.checker import SpellChecker
import pandas as pd
from pandas import Series, DataFrame
from bs4 import BeautifulSoup
from urllib.request import urlopen
import misspellings_lib as misspellings

text = ''
output = ''
chkr = SpellChecker("en_US")
result = DataFrame(columns=('misspelling', 'URL', 'num'))
excludedwords = 'www,href,http,https,html,br'

f = open('target.txt', 'w')
df = pd.read_csv('1.csv')
print (df.to_string())

for link in df['link']:
    html = urlopen(link)
    soup = BeautifulSoup(html, 'lxml')
    for text in soup.findAll('p'):
        text = str(text)
        chkr.set_text(text)
        for err in chkr:
#             output = output + '\n' + '[ERR] ' + str(err.word) + '@' + link
            if excludedwords.find(str(err.word)) < 0:
                output = output + '\n' + '[ERR] ' + str(err.word) + '@' + text
                rows = [str(err.word), link, -1]
                result.loc[len(result)] = rows
                print ('%s' %output)

result.sort_values(by=['misspelling', 'URL'], ascending=[True, True], inplace=True)
#result.drop_duplicates(subset='misspelling', inplace=True, keep='first')
result.index = range(len(result))
print (result.to_string())
f.write(output)
f.close()
result.loc[result['misspelling'] == 'AWS', 'num'] = len(result.loc[result['misspelling'] == 'AWS'])
result.to_csv('./result.csv', header=True, index=True)
