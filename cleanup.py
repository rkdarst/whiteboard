# Richard Darst, April 2009

import os
import sys

if len(sys.argv) > 1:   maxSize = int(sys.argv[1])
else:                   maxSize = 50

for fileName in os.listdir("data/"):
    fileName = "data/"+fileName
    size = os.stat(fileName).st_size
    if size < maxSize:
        print size
        print file(fileName).read()
        if size == 0:
            os.unlink(fileName)
