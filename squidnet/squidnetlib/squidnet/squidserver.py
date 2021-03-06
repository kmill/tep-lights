#!/usr/bin/env python
import socket, traceback
from threading import Thread
import signal
import thread
import os
import time

from squidnet import squidprotocol as s, sexp


class BroadcastServer(Thread) :
    def __init__(self, server_info) :
        Thread.__init__(self)
        self.server_info = server_info
        self.setDaemon(True)
        self.go = True
    def run(self) :
        print "Starting broadcast server."
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.s.bind(("", s.SQUIDNET_BROADCAST_PORT))
        self.s.settimeout(5)
        while self.go :
            try :
                message, address = self.s.recvfrom(4096 << 10)
                print "Got data from", address
                # Acknowledge it.
                xs = sexp.read_all(message)
                for x in xs :
                    if x == sexp.Symbol("info") :
                        print "Giving info"
                        self.s.sendto(sexp.write(self.server_info.get_sexp()), address)
                    else :
                        print "Ignoring"
            except socket.error :
                pass # just a timeout
            except :
                traceback.print_exc()
        self.s.close()
    def stop(self) :
        self.go = False

class HandlerServer(Thread) :
    def __init__(self, server_info) :
        Thread.__init__(self)
        self.server_info = server_info
        self.setDaemon(True)
        self.go = True
    def run(self) :
        print "Starting handler server."
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(("", self.server_info.port))
        self.s.settimeout(5)
        while self.go:
            try :
                message, address = self.s.recvfrom(8192 << 8)
                print "Got data from", address
                # Acknowledge it.
                xs = sexp.read_all(message)
                for x in xs :
                    # try to interpret it as a message!
                    print "Message:", x
                    print self.server_info.handle(x)
                    # we don't try to talk to the client.  Like a remote controller
            except socket.error :
                pass # just a timeout
            except :
                traceback.print_exc()
        self.s.close()
    def stop(self) :
        self.go = False

def run_server(server_info, daemon=False) :
    """Runs a server given a SquidServer object.  Make sure the host name
    and port are correct."""
    bs = BroadcastServer(server_info)
    hs = HandlerServer(server_info)
    bs.start()
    hs.start()
    if daemon:
        while True:
            time.sleep(60)
    else:
        try :
            while True:
                raw_input("Press Ctrl-C to quit.\n")
        except:
            print "Quitting within five seconds..."
            bs.stop()
            hs.stop()

class ShellRunner(object):
   def __init__(self) :
       self.lock = thread.allocate_lock()
       self.pids = ()

   def killpid(self, pid):
       try:
           os.kill(pid, signal.SIGINT)
       except OSError:
           try:
               os.kill(pid, signal.SIGKILL)
           except OSError:
               pass
           try:
               os.waitpid(pid, 0)
           except:
               pass

   def kill(self):
       self.lock.acquire()
       if self.pids:
           for pid in self.pids:
               self.killpid(pid)
       self.pids = ()
       self.lock.release()


   def spawn(self, path, args=None, *otherargs):
       if args is None:
           args = [path]
       programs = [(path, args)]
       for i in range(0, len(otherargs), 2):
           programs.append((otherargs[i], otherargs[i + 1]))

       self.lock.acquire()

       if self.pids:
           for pid in self.pids:
               self.killpid(pid)
           self.pids = ()

       self.pids = [os.spawnv(os.P_NOWAIT, path, args)
                    for (path, args) in programs]

       self.lock.release()

if __name__=="__main__" :
    def test_handler(args) :
        print "Got args: "+str(args)
    serv = s.SquidServer("kmill", "kmill.mit.edu", 2222, "Kyle's computer")
    d1 = s.SquidDevice("22-lights", "The lights in 22")
    serv.add_device(d1)
    d1.add_message(s.SquidMessage("set",
                                  "Set the lights to a color",
                                  [s.SquidArgument("color", s.SquidColorType(),
                                                   s.SquidValue(s.SquidColorType(),
                                                                [25, 25, 25]))],
                                  test_handler))
    d1.add_message(s.SquidMessage("stop",
                                  "Stops the lights",
                                  []))
    run_server(serv)
