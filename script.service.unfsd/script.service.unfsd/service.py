import xbmc
import xbmcvfs
import xbmcaddon
from os import system


class MyMonitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
    
    def onSettingsChanged(self):
        writeexports()


# addon
__addon__ = xbmcaddon.Addon(id='script.service.unfsd')
__addonpath__ = xbmc.translatePath(__addon__.getAddonInfo('path'))
__addonhome__ = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__scriptname__ = "unfs3"
__author__ = "lsellens"
__url__ = "http://lsellens.openelec.tv"



def writeexports():
    shares = __addon__.getSetting("SHARES")
    file = xbmcvfs.File(xbmc.translatePath(__addonhome__ + 'exports'), 'w')
    for i in range(0, int(shares)):
        exec('folder{0} = __addon__.getSetting("SHARE_FOLDER{0}")'.format(i))
        exec('permission{0} = __addon__.getSetting("PERMISSION{0}")'.format(i))
        xbmc.log('unfs: folder0 ' + folder0, level=xbmc.LOGDEBUG)
        file.write('{0} ({1},insecure,anonuid=0,anongid=0,all_squash)\n'.format(eval('folder{0}'.format(i)), eval('permission{0}'.format(i))))
    file.close()
    system("systemctl reload script.service.unfsd.service")


if not xbmcvfs.exists(xbmc.translatePath(__addonhome__ + 'exports')):
    writeexports()

monitor = MyMonitor()
while not monitor.abortRequested():
    if monitor.waitForAbort():
        break

