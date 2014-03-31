#
import os
import xbmc
import xbmcaddon

__scriptname__ = "audo"
__author__     = "lsellens"
__url__        = "http://code.google.com/p/repository-lsellens/"
__settings__   = xbmcaddon.Addon(id='service.downloadmanager.audo')
__cwd__        = __settings__.getAddonInfo('path')
__start__      = xbmc.translatePath(os.path.join(__cwd__, 'bin', "audo.py"))
__stop__       = xbmc.translatePath(os.path.join(__cwd__, 'bin', "audo.stop"))

#Open settings dialog
if __name__ == '__main__':
    __settings__.openSettings()
