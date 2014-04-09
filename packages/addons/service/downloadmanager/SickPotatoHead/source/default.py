#
import xbmcaddon

__scriptname__ = "SickPotatoHead"
__author__     = "lsellens"
__url__        = "http://code.google.com/p/repository-lsellens/"
__settings__   = xbmcaddon.Addon(id='service.downloadmanager.SickPotatoHead')

#Open settings dialog
if __name__ == '__main__':
    __settings__.openSettings()
