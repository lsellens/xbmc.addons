#
import os
import xbmc
import xbmcaddon

__scriptname__ = "nfs-server"
__author__     = "lsellens"
__url__        = "https://code.google.com/p/repository-lsellens/"
__settings__   = xbmcaddon.Addon(id='service.filesystem.nfs-server')
__cwd__        = __settings__.getAddonInfo('path')
__start__      = xbmc.translatePath( os.path.join( __cwd__, 'bin', "nfs-server.py") )
__stop__       = xbmc.translatePath( os.path.join( __cwd__, 'bin', "nfs-server.stop") )

#Open settings dialog
if __name__ == '__main__':
    __settings__.openSettings()
