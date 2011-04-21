import socket
import threading
import SocketServer

class ThreadedUDPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        data = self.request[0].strip()
        f = open("log.txt", 'a')
        f.writelines(data + "\n")
        f.close()

class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass

if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = socket.gethostbyname(socket.gethostname()), 9999
    print "Hosting at IP: %s" % HOST
    server = ThreadedUDPServer((HOST, PORT), ThreadedUDPRequestHandler)
    ip, port = server.server_address
    server.serve_forever()