#!/usr/bin/env python
# Richard Darst, May 2009

import sys
sys.path[0:0] = 'mobwrite/daemon/lib', 'mobwrite/daemon'
import mobwrite_core
import mobwrite_daemon
del sys.path[0:2]

mobwrite_daemon.MAX_VIEWS = 100
mobwrite_daemon.STORAGE_MODE = mobwrite_daemon.FILE
mobwrite_daemon.LOCAL_PORT = 30711 # adjust

mobwrite_core.MAX_CHARS = 30000
mobwrite_core.TIMEOUT_TEXT = mobwrite_core.datetime.timedelta(days=31)
mobwrite_core.LOG.setLevel(mobwrite_core.logging.DEBUG)

# this is from __main__ in mobwrite_daemon
mobwrite_core.logging.basicConfig()
mobwrite_daemon.main()
mobwrite_core.logging.shutdown()


