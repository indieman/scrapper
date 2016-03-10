import logging
import pycountry
import socket
import socks
import stem.process
from stem import Signal
from stem.control import Controller


logging.getLogger('stem').setLevel('WARN')


def getaddrinfo(*args):
    return [(
        socket.AF_INET,
        socket.SOCK_STREAM,
        6,
        '',
        (args[0], args[1])
    )]


class TorProxy(object):

    SOCKS_PORT = 7000

    def __init__(self):
        self._tor_process = None
        self._tor_controller = None

        self._default_socket = socket.socket
        self._default_getaddrinfo = socket.getaddrinfo
        socks.setdefaultproxy(
            socks.PROXY_TYPE_SOCKS5, '127.0.0.1', TorProxy.SOCKS_PORT
        )
        self._proxy_on()

    def change_exit_node(self):
        self._proxy_off()
        self._tor_controller = Controller.from_port(port=9051)
        self._tor_controller.authenticate()
        self._tor_controller.signal(Signal.NEWNYM)
        self._proxy_on()

    def start(self):
        logging.info('Starting TOR...')
        countries = [c.alpha2.lower() for c in pycountry.countries]
        countries = ['{%s}' % c for c in countries]
        countries = str(','.join(countries))
        self._tor_process = stem.process.launch_tor_with_config(
            config={
                'ControlPort': '9051',
                'SocksPort': str(TorProxy.SOCKS_PORT),
                'ExitNodes': countries,
            },
        )
        logging.info('TOR proxy started.')

    def stop(self):
        if self._tor_process:
            self._tor_process.kill()
        logging.info('TOR proxy stopped.')

    def _proxy_on(self):
        socket.socket = socks.socksocket
        socket.getaddrinfo = getaddrinfo

    def _proxy_off(self):
        socket.socket = self._default_socket
        socket.getaddrinfo = self._default_getaddrinfo

