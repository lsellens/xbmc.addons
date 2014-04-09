#
import xbmc
import xbmcaddon
import time
import subprocess

__scriptname__ = "SickPotatoHead"
__author__     = "lsellens"
__url__        = "http://code.google.com/p/repository-lsellens/"
__settings__   = xbmcaddon.Addon(id='service.downloadmanager.SickPotatoHead')
__cwd__        = __settings__.getAddonInfo('path')
__start__      = xbmc.translatePath(__cwd__ + '/bin/SickPotatoHead.py')
__stop__       = xbmc.translatePath(__cwd__ + '/bin/SickPotatoHead.stop')

subprocess.call(['python', __start__])

while not xbmc.abortRequested:
    time.sleep(0.250)

subprocess.Popen(__stop__, shell=True, close_fds=True)
