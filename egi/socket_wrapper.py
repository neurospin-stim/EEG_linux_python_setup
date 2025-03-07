#!/usr/bin/python
# -*- coding: cp1251 -*-

import socket

'''     
import struct     

import math, time # for time in milliseconds     

import exceptions

class SocketException( exceptions.Exception ) :
    """ there is something wrong with our socket wrapper """

    pass
    
'''


class Socket:
    """ wrap the socket() class """

    def connect(self, str_address, port_no):
        """ connect to the given host at the specified port ) """

        #
        # todo: create our own exception to handle stuff properly
        #

        self._socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM  # IP_V4
        )
        self._socket.settimeout(2)
        try:
            self._socket.connect((str_address, port_no))
        except socket.error as e:
            return e
        except socket.timeout as e:
            return e
        else:
            ## self._connection = self._socket.makefile('rw', 0) # read and write, no internal buffer
            self._connection = self._socket.makefile(
                "rwb", 0
            )  # read and write, no internal buffer
            return None

    def disconnect(self):
        """ close the connection """

        self._connection.close()

        # is this also nessesary?
        self._socket.close()

        del self._connection
        del self._socket

    def write(self, data):
        """ write to the socket -- the socket must be opened """

        data = data.encode('ascii') if isinstance(data, str) else data
        self._connection.write(data)
        #self._connection.flush( data )

    def read(self, size=-1):
        """ read from the socket; warning -- it blocks on reading! """

        if size < 0:

            return self._connection.read()

        else:

            return self._connection.read(size)
