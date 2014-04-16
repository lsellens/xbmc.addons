#
import subprocess
import xbmc
import xbmcaddon
import urllib2
import socket
import time
import datetime
import sys

__scriptname__ = "audo"
__author__     = "lsellens"
__url__        = "http://code.google.com/p/repository-lsellens/"
__addon__      = xbmcaddon.Addon(id='script.service.audo')
__cwd__        = __addon__.getAddonInfo('path')
__addondir__   = __addon__.getAddonInfo('profile')
__start__      = xbmc.translatePath(__cwd__ + '/bin/audo.py')
__stop__       = xbmc.translatePath(__cwd__ + '/bin/audo.stop')

checkInterval  = 240
timeout        = 20
wake_times     = ['01:00', '03:00', '05:00', '07:00', '09:00', '11:00', '13:00', '15:00', '17:00', '19:00', '21:00',
                  '23:00']
idleTimer      = 0

# Launch audo

try:
    xbmc.executebuiltin('XBMC.RunScript(%s)' % __start__, True)
except Exception, e:
    xbmc.log('audo: could execute script:', level=xbmc.LOGERROR)
    xbmc.log(str(e), level=xbmc.LOGERROR)

# check for launching sabnzbd
sabNzbdLaunch = (__addon__.getSetting('SABNZBD_LAUNCH').lower() == 'true')

sys.path.append(xbmc.translatePath(__cwd__ + '/resources/lib'))
from configobj import ConfigObj

if sabNzbdLaunch:
    # SABnzbd addresses and api key
    sabNzbdConfigFile = (xbmc.translatePath(__addondir__ + '/sabnzbd.ini'))
    sabConfiguration  = ConfigObj(sabNzbdConfigFile)
    sabNzbdAddress    = "localhost:8081"
    sabNzbdApiKey     = sabConfiguration['misc']['api_key']
    sabNzbdQueue      = ('http://' + sabNzbdAddress + '/api?mode=queue&output=xml&apikey=' + sabNzbdApiKey)
    sabNzbdHistory    = ('http://' + sabNzbdAddress + '/api?mode=history&output=xml&apikey=' + sabNzbdApiKey)
    sabNzbdQueueKeywords = ['<status>Downloading</status>', '<status>Fetching</status>', '<priority>Force</priority>']
    sabNzbdHistoryKeywords = ['<status>Repairing</status>', '<status>Verifying</status>', '<status>Extracting</status>']

    # start checking SABnzbd for activity and prevent sleeping if necessary
    socket.setdefaulttimeout(timeout)

    # perform some initial checks and log essential settings
    shouldKeepAwake = (__addon__.getSetting('SABNZBD_KEEP_AWAKE').lower() == 'true')
    wakePeriodically = (__addon__.getSetting('SABNZBD_PERIODIC_WAKE').lower() == 'true')
    wakeHourIdx = int(__addon__.getSetting('SABNZBD_WAKE_AT'))
    if shouldKeepAwake:
        xbmc.log('audo: will prevent idle sleep/shutdown while downloading')
    if wakePeriodically:
        xbmc.log('audo: will try to wake system daily at ' + wake_times[wakeHourIdx])


while not xbmc.abortRequested:

    if sabNzbdLaunch:
        # reread setting in case it has changed
        shouldKeepAwake = (__addon__.getSetting('SABNZBD_KEEP_AWAKE').lower() == 'true')
        wakePeriodically = (__addon__.getSetting('SABNZBD_PERIODIC_WAKE').lower() == 'true')
        wakeHourIdx = int(__addon__.getSetting('SABNZBD_WAKE_AT'))

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
            open("/sys/class/rtc/rtc0/wakealarm", "w").write("0")
            open("/sys/class/rtc/rtc0/wakealarm", "w").write(str(secondsSinceEpoch))

    time.sleep(0.250)

subprocess.Popen(__stop__, shell=True, close_fds=True)
