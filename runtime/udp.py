import socket, pickle, random
if not __name__ == "__main__":
    from .event import *

MIN_UDP_PORT = 10000
MAX_UDP_PORT = 20000
MAX_UDP_BUFSIZE = 200000
class UdpEndPoint:
    sender = None
    def __init__(self):
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bound = False
        while not bound:
            self._address = ('localhost',
                             random.randint(MIN_UDP_PORT, MAX_UDP_PORT))
            try:
                self._conn.bind(self._address)
                bound = True
            except socket.error:
                pass

    def send(self, data, src, timestamp = 0):
        if UdpEndPoint.sender == None:
            UdpEndPoint.sender = socket.socket(socket.AF_INET,
                                               socket.SOCK_DGRAM)
        bytedata = pickle.dumps((src, timestamp, data))
        if len(bytedata) > MAX_UDP_BUFSIZE:
            raise socket.error("Data size exceeded maximum buffer size.")
        if UdpEndPoint.sender.sendto(bytedata, self._address) != len(bytedata):
            raise socket.error()

    def recv(self, block, timeout = None):
        flags = 0
        if not block:
            flags = socket.MSG_DONTWAIT

        try:
            bytedata = self._conn.recv(MAX_UDP_BUFSIZE, flags)
            src, tstamp, data = pickle.loads(bytedata)
            if not isinstance(src, UdpEndPoint):
                raise TypeError()
            else:
                return (src, tstamp, data)
        except socket.error as e:
            return None

    def __getstate__(self):
        return ("UDP", self._address)

    def __setstate__(self, value):
        proto, self._address = value
        self._conn = None

    def __str__(self):
        return self._address.__str__()
    def __repr__(self):
        return str(self._address[1])

    def __hash__(self):
        return self._address.__hash__()

    def __eq__(self, obj):
        if not hasattr(obj, "_address"):
            return False
        return self._address == obj._address
    def __lt__(self, obj):
        return self._address < obj._address
    def __le__(self, obj):
        return self._address <= obj._address
    def __gt__(self, obj):
        return self._address > obj._address
    def __ge__(self, obj):
        return self._address >= obj._address
    def __ne__(self, obj):
        if not hasattr(obj, "_address"):
            return True
        return self._address != obj._address
