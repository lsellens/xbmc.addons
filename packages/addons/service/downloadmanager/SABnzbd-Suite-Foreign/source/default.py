#
import os
import xbmc
import xbmcaddon

__scriptname__ = "SABnzbd Suite Foreign"
__author__     = "OpenELEC"
__url__        = "http://www.openelec.tv"
__settings__   = xbmcaddon.Addon(id='service.downloadmanager.SABnzbd-Suite-Foreign')
__cwd__        = __settings__.getAddonInfo('path')
__start__      = xbmc.translatePath( os.path.join( __cwd__, 'bin', "SABnzbd-Suite.py") )
__stop__       = xbmc.translatePath( os.path.join( __cwd__, 'bin', "SABnzbd-Suite.stop") )

#Open settings dialog
if __name__ == '__main__':
    __settings__.openSettings()
