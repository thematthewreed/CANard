from canard import can
from canard.hw import socketcan
import sys

dev = socketcan.SocketCanDev(sys.argv[1])
dev.start()
count = 0
while True:
    count = count + 1
    frame = dev.recv()
    dev.send(frame)
    print("%d: %s" % (count, str(frame)))
