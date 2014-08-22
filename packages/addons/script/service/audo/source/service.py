#
from resources.lib.configobj import ConfigObj
import xbmc
import xbmcaddon
import xbmcvfs
import urllib2
import socket
import time
import datetime

__scriptname__ = "audo"
__author__     = "lsellens"
__url__        = "http://code.google.com/p/repository-lsellens/"
__addon__      = xbmcaddon.Addon(id='script.service.audo')
__addonpath__  = __addon__.getAddonInfo('path')
__addonhome__  = __addon__.getAddonInfo('profile')
__start__      = xbmc.translatePath(__addonpath__ + '/resources/audo.py')
__stop__       = xbmc.translatePath(__addonpath__ + '/resources/audo.stop.py')

checkInterval  = 240
timeout        = 20
wake_times     = ['01:00', '03:00', '05:00', '07:00', '09:00', '11:00', '13:00', '15:00', '17:00', '19:00', '21:00',
                  '23:00']
idleTimer      = 0

# check if an update occurred
if xbmcvfs.exists(xbmc.translatePath(__addonpath__ + '/justupdated')):
    xbmcvfs.delete(xbmc.translatePath(__addonpath__ + '/justupdated'))
    xbmc.log('audo: update occurred since last run:', level=xbmc.LOGDEBUG)

# Launch audo
try:
    xbmc.executebuiltin('XBMC.RunScript(%s)' % __start__, True)
except Exception, e:
    xbmc.log('audo: could not execute launch script:', level=xbmc.LOGERROR)
    xbmc.log(str(e), level=xbmc.LOGERROR)

# start checking SABnzbd for activity and prevent sleeping if necessary
socket.setdefaulttimeout(timeout)

# perform some initial checks and log essential settings
shouldKeepAwake = (__addon__.getSetting('SABNZBD_KEEP_AWAKE').lower() == 'true')
wakePeriodically = (__addon__.getSetting('PERIODIC_WAKE').lower() == 'true')
wakeHourIdx = int(__addon__.getSetting('WAKE_AT'))
if shouldKeepAwake:
    xbmc.log('audo: will prevent idle sleep/shutdown while downloading')
if wakePeriodically:
    xbmc.log('audo: will try to wake system daily at ' + wake_times[wakeHourIdx])

# SABnzbd addresses and api key
sabNzbdConfigFile = (xbmc.translatePath(__addonhome__ + 'sabnzbd.ini'))
while not xbmcvfs.exists(sabNzbdConfigFile):
    time.sleep(5)
else:
    sabConfiguration  = ConfigObj(sabNzbdConfigFile)
    sabNzbdAddress    = "localhost:8081"
    sabNzbdApiKey     = sabConfiguration['misc']['api_key']
    sabNzbdQueue      = ('http://' + sabNzbdAddress + '/api?mode=queue&output=xml&apikey=' + sabNzbdApiKey)
    sabNzbdHistory    = ('http://' + sabNzbdAddress + '/api?mode=history&output=xml&apikey=' + sabNzbdApiKey)
    sabNzbdQueueKeywords = ['<status>Downloading</status>', '<status>Fetching</status>', '<priority>Force</priority>']
    sabNzbdHistoryKeywords = ['<status>Repairing</status>', '<status>Verifying</status>', '<status>Extracting</status>']

while not xbmc.abortRequested:
    #restart service after an update
    if xbmcvfs.exists(xbmc.translatePath(__addonpath__ + '/justupdated')):
        xbmc.log('audo: update occurred. attempting to restart:', level=xbmc.LOGDEBUG)
        try:
            xbmc.executebuiltin('XBMC.RunScript(%s)' % __stop__, True)
        except Exception, e:
            xbmc.log('audo: could not execute shutdown script after update:', level=xbmc.LOGERROR)
            xbmc.log(str(e), level=xbmc.LOGERROR)

        xbmcvfs.delete(xbmc.translatePath(__addonpath__ + '/justupdated'))
        time.sleep(10)

        try:
            xbmc.executebuiltin('XBMC.RunScript(%s)' % __start__, True)
        except Exception, e:
            xbmc.log('audo: could not execute launch script after update:', level=xbmc.LOGERROR)
            xbmc.log(str(e), level=xbmc.LOGERROR)
        
    # reread setting in case it has changed
    shouldKeepAwake = (__addon__.getSetting('SABNZBD_KEEP_AWAKE').lower() == 'true')
    wakePeriodically = (__addon__.getSetting('PERIODIC_WAKE').lower() == 'true')
    wakeHourIdx = int(__addon__.getSetting('WAKE_AT'))

    # check if SABnzbd is downloading
    if shouldKeepAwake:
        idleTimer += 1
        # check SABnzbd every ~60s (240 cycles)
        if idleTimer == checkInterval:
            sabIsActive = False
            idleTimer = 0
            req = urllib2.Request(sabNzbdQueue)
            try:
                handle = urllib2.urlopen(req)
            except IOError, e:
                xbmc.log('audo: could not determine SABnzbds queue status:', level=xbmc.LOGERROR)
                xbmc.log(str(e), level=xbmc.LOGERROR)
            else:
                queue = handle.read()
                handle.close()
                if any(x in queue for x in sabNzbdQueueKeywords):
                    sabIsActive = True

            req = urllib2.Request(sabNzbdHistory)
            try:
                handle = urllib2.urlopen(req)
            except IOError, e:
                xbmc.log('audo: could not determine SABnzbds history status:', level=xbmc.LOGERROR)
                xbmc.log(str(e), level=xbmc.LOGERROR)
            else:
                history = handle.read()
                handle.close()
                if any(x in history for x in sabNzbdHistoryKeywords):
                    sabIsActive = True

            # reset idle timer if queue is downloading/reparing/verifying/extracting
            if sabIsActive:
                xbmc.executebuiltin('InhibitIdleShutdown(true)')
                xbmc.log('audo: preventing sleep', level=xbmc.LOGDEBUG)
            else:
                xbmc.executebuiltin('InhibitIdleShutdown(false)')
                xbmc.log('audo: not preventing sleep', level=xbmc.LOGDEBUG)

        # calculate and set the time to wake up at (if any)
    if wakePeriodically:
        wakeHour = wakeHourIdx * 2 + 1
        timeOfDay = datetime.time(hour=wakeHour)
        now = datetime.datetime.now()
        wakeTime = now.combine(now.date(), timeOfDay)
        if now.time() > timeOfDay:
            wakeTime += datetime.timedelta(days=1)
        secondsSinceEpoch = time.mktime(wakeTime.timetuple())
        try:
            open("/sys/class/rtc/rtc0/wakealarm", "w").write("0")
            open("/sys/class/rtc/rtc0/wakealarm", "w").write(str(secondsSinceEpoch))
        except IOError, e:
            xbmc.log('audo: could not write /sys/class/rtc/rtc0/wakealarm ', level=xbmc.LOGERROR)
            xbmc.log(str(e), level=xbmc.LOGERROR)
    else:
        try:
            open("/sys/class/rtc/rtc0/wakealarm", "w").close()
        except IOError, e:
            xbmc.log('audo: could not write /sys/class/rtc/rtc0/wakealarm ', level=xbmc.LOGERROR)
            xbmc.log(str(e), level=xbmc.LOGDEBUG)

    time.sleep(0.250)

# Shutdown audo
try:
    xbmc.executebuiltin('XBMC.RunScript(%s)' % __stop__, True)
except Exception, e:
    xbmc.log('audo: could not execute shutdown script:', level=xbmc.LOGERROR)
    xbmc.log(str(e), level=xbmc.LOGERROR)
