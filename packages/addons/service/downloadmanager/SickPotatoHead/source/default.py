#
import os
import xbmc
import xbmcaddon

__scriptname__ = "SickPotatoHead"
__author__     = "lsellens"
__url__        = "http://dl.dropbox.com/u/42265484/repository.SickPotatoHead/repo"
__settings__   = xbmcaddon.Addon(id='service.downloadmanager.SickPotatoHead')
__cwd__        = __settings__.getAddonInfo('path')
__start__      = xbmc.translatePath(os.path.join(__cwd__, 'bin', "SickPotatoHead.py"))
__stop__       = xbmc.translatePath(os.path.join(__cwd__, 'bin', "SickPotatoHead.stop"))

#Open settings dialog
if __name__ == '__main__':
    __settings__.openSettings()
