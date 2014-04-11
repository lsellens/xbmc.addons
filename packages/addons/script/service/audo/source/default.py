#
import xbmcaddon

__scriptname__ = "audo"
__author__     = "lsellens"
__url__        = "http://code.google.com/p/repository-lsellens/"
__addon__      = xbmcaddon.Addon(id='script.service.audo')

#Open settings dialog
if __name__ == '__main__':
    __addon__.openSettings()
