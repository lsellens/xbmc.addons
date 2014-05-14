#
import xbmc
import xbmcaddon

__scriptname__ = "audo"
__author__     = "lsellens"
__url__        = "http://code.google.com/p/repository-lsellens/"
__addon__      = xbmcaddon.Addon(id='script.service.audo')
__addonpath__  = __addon__.getAddonInfo('path')
__start__      = xbmc.translatePath(__addonpath__ + '/resources/audo.py')
__stop__       = xbmc.translatePath(__addonpath__ + '/resources/audo.stop.py')

if __name__ == '__main__':

    # Shutdown audo
    try:
        xbmc.executebuiltin('XBMC.RunScript(%s)' % __stop__, True)
    except Exception, e:
        xbmc.log('audo: could not execute shutdown script:', level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

    #Open settings dialog
    __addon__.openSettings()

    # Restart audo
    try:
        xbmc.executebuiltin('XBMC.RunScript(%s)' % __start__, True)
    except Exception, e:
        xbmc.log('audo: could not execute launch script:', level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)