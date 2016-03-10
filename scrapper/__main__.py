import urllib
import logging
import socks
import requests
from requests.exceptions import ConnectionError
from .tor_proxy import TorProxy
from .spider import spider

class Scrapper(object):

    def __init__(self):
        self._proxy = TorProxy()

    def example_query(self):
        #self._proxy.change_exit_node()
        return urllib.request.urlopen(
            'https://www.atagar.com/echo.php'
        ).read()

    def request_example(self):
        self._proxy.change_exit_node()
        try:
            res = requests.get('https://www.atagar.com/echo.php')
        except ConnectionError:
            pass
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(ex)
            print(message)
        print(res.status_code)
        return res.text

    def start(self):
        self._proxy.start()

    def stop(self):
        self._proxy.stop()


if __name__ == '__main__':
    scrapper = Scrapper()

    try:
        scrapper.start()
        url = 'http://allinform.ru'
        #url = 'http://www.allinform.ru/moskva/cat606177.html'
        #url = 'http://www.allinform.ru/moskva/org5895895.html'
        spider(thread_number=10,
               new_proxy=scrapper._proxy.change_exit_node,
               url=url)

    except:
        logging.exception('Fatal :-(')

    finally:
        scrapper.stop()

