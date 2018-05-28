# LinkCollector
---------------------------------------------------
*※ This guidance is based on Python 3.6.*
1. Prerequisites
* 9 Libraries
  * re: https://docs.python.org/3.6/library/re.html
  * sys: https://docs.python.org/3/library/sys.html?highlight=sys#module-sys
  * time: https://docs.python.org/3/library/time.html?highlight=time#module-time
  * threading: https://docs.python.org/3/library/threading.html?highlight=threading#module-threading
  * bs4
  ```
  sudo apt-get install python3-bs4
  pip3 install beautifulsoup4
  ```
  * urllib.request, urllib.error
  ```
  pip3 install urllib3
  ```
  * pandas: https://pandas.pydata.org/pandas-docs/stable/install.html
2. How to use
* e.g.: python main.py -t https://developer.tizen.org -m 20
* argument 1(-t or -T): Target URL
* argument 2(-m or -M): Maximun number of threads
3. Expected value
* All links including to the target URL and sub folders
4. Sample
* Please check the result file in the result folder
---------------------------------------------------
