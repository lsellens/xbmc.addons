#
import xbmc
import xbmcaddon

__scriptname__ = "audo"
__author__     = "lsellens"
__url__        = "http://code.google.com/p/repository-lsellens/"
__addon__      = xbmcaddon.Addon(id='script.service.audo')
__cwd__        = __addon__.getAddonInfo('path')
__addondir__   = __addon__.getAddonInfo('profile')
__start__      = xbmc.translatePath(__cwd__ + '/bin/audo.py')
__stop__       = xbmc.translatePath(__cwd__ + '/bin/audo.stop') 

#Open settings dialog
if __name__ == '__main__':
    __addon__.openSettings()
