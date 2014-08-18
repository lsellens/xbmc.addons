# Initializes and launches SABnzbd, Couchpotato, Sickbeard and Headphones
from xml.dom.minidom import parseString
from lib.configobj import ConfigObj
import os
import subprocess
import urllib2
import hashlib
import platform
import xbmc
import xbmcaddon
import xbmcvfs

# helper functions
# ----------------


def create_dir(dirname):
    if not xbmcvfs.exists(dirname):
        xbmcvfs.mkdirs(dirname)
        xbmc.log('AUDO: Created directory ' + dirname, level=xbmc.LOGDEBUG)

# define some things that we're gonna need, mainly paths
# ------------------------------------------------------

# addon
__addon__             = xbmcaddon.Addon(id='script.service.audo')
__addonpath__         = xbmc.translatePath(__addon__.getAddonInfo('path'))
__addonhome__         = xbmc.translatePath(__addon__.getAddonInfo('profile'))

# settings
pDefaultSuiteSettings = xbmc.translatePath(__addonpath__ + '/settings-default.xml')
pSuiteSettings        = xbmc.translatePath(__addonhome__ + 'settings.xml')
pXbmcSettings         = '/storage/.xbmc/userdata/guisettings.xml'
pSabNzbdSettings      = xbmc.translatePath(__addonhome__ + 'sabnzbd.ini')
pSickBeardSettings    = xbmc.translatePath(__addonhome__ + 'sickbeard.ini')
pCouchPotatoServerSettings  = xbmc.translatePath(__addonhome__ + 'couchpotatoserver.ini')
pHeadphonesSettings   = xbmc.translatePath(__addonhome__ + 'headphones.ini')

# directories
pSabNzbdComplete      = '/storage/downloads'
pSabNzbdWatchDir      = '/storage/downloads/watch'
pSabNzbdCompleteTV    = '/storage/downloads/tvshows'
pSabNzbdCompleteMov   = '/storage/downloads/movies'
pSabNzbdCompleteMusic = '/storage/downloads/music'
pSabNzbdIncomplete    = '/storage/downloads/incomplete'
pSickBeardTvScripts   = xbmc.translatePath(__addonpath__ + '/resources/SickBeard/autoProcessTV')
pSabNzbdScripts       = xbmc.translatePath(__addonhome__ + 'scripts')

# pylib
pPylib                = xbmc.translatePath(__addonpath__ + '/resources/lib')

# service commands
sabnzbd               = ['python', xbmc.translatePath(__addonpath__ + '/resources/SABnzbd/SABnzbd.py'),
                         '-d', '-f', pSabNzbdSettings, '-l 0']
sickBeard             = ['python', xbmc.translatePath(__addonpath__ + '/resources/SickBeard/SickBeard.py'),
                         '--daemon', '--datadir', __addonhome__, '--config', pSickBeardSettings]
couchPotatoServer     = ['python', xbmc.translatePath(__addonpath__ + '/resources/CouchPotatoServer/CouchPotato.py'),
                         '--daemon', '--pid_file', xbmc.translatePath(__addonhome__ + 'couchpotato.pid'),
                         '--config_file', pCouchPotatoServerSettings]
headphones            = ['python', xbmc.translatePath(__addonpath__ + '/resources/Headphones/Headphones.py'),
                         '-d', '--datadir', __addonhome__, '--config', pHeadphonesSettings]

# Other stuff
sabNzbdHost           = 'localhost:8081'

# create directories and settings on first launch
# -----------------------------------------------

firstLaunch = not xbmcvfs.exists(pSabNzbdSettings)
sbfirstLaunch = not xbmcvfs.exists(pSickBeardSettings)
cpfirstLaunch = not xbmcvfs.exists(pCouchPotatoServerSettings)
hpfirstLaunch = not xbmcvfs.exists(pHeadphonesSettings)

xbmc.log('AUDO: Creating directories if missing', level=xbmc.LOGDEBUG)
create_dir(__addonhome__)
create_dir(pSabNzbdComplete)
create_dir(pSabNzbdWatchDir)
create_dir(pSabNzbdCompleteTV)
create_dir(pSabNzbdCompleteMov)
create_dir(pSabNzbdCompleteMusic)
create_dir(pSabNzbdIncomplete)
create_dir(pSabNzbdScripts)

if not xbmcvfs.exists(xbmc.translatePath(pSabNzbdScripts + '/sabToSickBeard.py')):
    xbmcvfs.copy(xbmc.translatePath(pSickBeardTvScripts + '/sabToSickBeard.py'), pSabNzbdScripts + '/sabToSickBeard.py')
if not xbmcvfs.exists(xbmc.translatePath(pSabNzbdScripts + '/autoProcessTV.py')):
    xbmcvfs.copy(xbmc.translatePath(pSickBeardTvScripts + '/autoProcessTV.py'), pSabNzbdScripts + '/autoProcessTV.py')

# the settings file already exists if the user set settings before the first launch
if not xbmcvfs.exists(pSuiteSettings):
    xbmcvfs.copy(pDefaultSuiteSettings, pSuiteSettings)

# read addon and xbmc settings
# ----------------------------

# Transmission-Daemon
transauth = False
# work around for frodo crash will fix this later
if xbmcvfs.exists('/storage/.xbmc/addons/service.downloadmanager.transmission/default.py'):
    try:
        transmissionaddon = xbmcaddon.Addon(id='service.downloadmanager.transmission')
        transauth = (transmissionaddon.getSetting('TRANSMISSION_AUTH').lower() == 'true')

        if transauth:
            xbmc.log('AUDO: Transmission Authentication Enabled', level=xbmc.LOGDEBUG)
            transuser = (transmissionaddon.getSetting('TRANSMISSION_USER').decode('utf-8'))
            if transuser == '':
                transuser = None
            transpwd = (transmissionaddon.getSetting('TRANSMISSION_PWD').decode('utf-8'))
            if transpwd == '':
                transpwd = None
        else:
            xbmc.log('AUDO: Transmission Authentication Not Enabled', level=xbmc.LOGDEBUG)

    except Exception, e:
        xbmc.log('AUDO: Transmission Settings are not present', level=xbmc.LOGNOTICE)
        xbmc.log(str(e), level=xbmc.LOGNOTICE)
        pass

# audo
user = (__addon__.getSetting('SABNZBD_USER').decode('utf-8'))
pwd = (__addon__.getSetting('SABNZBD_PWD').decode('utf-8'))
host = (__addon__.getSetting('SABNZBD_IP'))
sabnzbd_launch = (__addon__.getSetting('SABNZBD_LAUNCH').lower() == 'true')
sickbeard_launch = (__addon__.getSetting('SICKBEARD_LAUNCH').lower() == 'true')
couchpotato_launch = (__addon__.getSetting('COUCHPOTATO_LAUNCH').lower() == 'true')
headphones_launch = (__addon__.getSetting('HEADPHONES_LAUNCH').lower() == 'true')

# XBMC
fXbmcSettings = open(pXbmcSettings, 'r')
data = fXbmcSettings.read()
fXbmcSettings.close()
xbmcSettings = parseString(data)
xbmcServices = xbmcSettings.getElementsByTagName('services')[0]
xbmcPort         = xbmcServices.getElementsByTagName('webserverport')[0].firstChild.data
try:
    xbmcUser     = xbmcServices.getElementsByTagName('webserverusername')[0].firstChild.data
except StandardError:
    xbmcUser = ''
try:
    xbmcPwd      = xbmcServices.getElementsByTagName('webserverpassword')[0].firstChild.data
except StandardError:
    xbmcPwd = ''

# prepare execution environment
# -----------------------------
parch                         = platform.machine()
pnamemapper                   = xbmc.translatePath(pPylib + '/Cheetah/_namemapper.so')
pssl                          = xbmc.translatePath(pPylib + '/OpenSSL/SSL.so')
prand                         = xbmc.translatePath(pPylib + '/OpenSSL/rand.so')
pcrypto                       = xbmc.translatePath(pPylib + '/OpenSSL/crypto.so')
petree                        = xbmc.translatePath(pPylib + '/lxml/etree.so')
pobjectify                    = xbmc.translatePath(pPylib + '/lxml/objectify.so')
pyenc                         = xbmc.translatePath(pPylib + '/_yenc.so')
ppar2                         = xbmc.translatePath(__addonpath__ + '/bin/par2')
punrar                        = xbmc.translatePath(__addonpath__ + '/bin/unrar')
punzip                        = xbmc.translatePath(__addonpath__ + '/bin/unzip')

xbmc.log('AUDO: ' + parch + ' architecture detected', level=xbmc.LOGDEBUG)

if parch.startswith('arm'):
    parch = 'arm'

if not xbmcvfs.exists(pnamemapper):
    try:
        fnamemapper                   = xbmc.translatePath(pPylib + '/multiarch/_namemapper.so.' + parch)
        xbmcvfs.copy(fnamemapper, pnamemapper)
        xbmc.log('AUDO: Copied _namemapper.so for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('AUDO: Error Copying _namemapper.so for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

if not xbmcvfs.exists(pssl):
    try:
        fssl                          = xbmc.translatePath(pPylib + '/multiarch/SSL.so.' + parch)
        xbmcvfs.copy(fssl, pssl)
        xbmc.log('AUDO: Copied SSL.so for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('AUDO: Error Copying SSL.so for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

if not xbmcvfs.exists(prand):
    try:
        frand                         = xbmc.translatePath(pPylib + '/multiarch/rand.so.' + parch)
        xbmcvfs.copy(frand, prand)
        xbmc.log('AUDO: Copied rand.so for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('AUDO: Error Copying rand.so for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

if not xbmcvfs.exists(pcrypto):
    try:
        fcrypto                       = xbmc.translatePath(pPylib + '/multiarch/crypto.so.' + parch)
        xbmcvfs.copy(fcrypto, pcrypto)
        xbmc.log('AUDO: Copied crypto.so for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('AUDO: Error Copying crypto.so for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

if not xbmcvfs.exists(petree):
    try:
        fetree                        = xbmc.translatePath(pPylib + '/multiarch/etree.so.' + parch)
        xbmcvfs.copy(fetree, petree)
        xbmc.log('AUDO: Copied etree.so for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('AUDO: Error Copying etree.so for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

if not xbmcvfs.exists(pobjectify):
    try:
        fobjectify                    = xbmc.translatePath(pPylib + '/multiarch/objectify.so.' + parch)
        xbmcvfs.copy(fobjectify, pobjectify)
        xbmc.log('AUDO: Copied objectify.so for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('AUDO: Error Copying objectify.so for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

if not xbmcvfs.exists(pyenc):
    try:
        fyenc                         = xbmc.translatePath(pPylib + '/multiarch/_yenc.so.' + parch)
        xbmcvfs.copy(fyenc, pyenc)
        xbmc.log('AUDO: Copied _yenc.so for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('AUDO: Error Copying _yenc.so for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

if not xbmcvfs.exists(ppar2):
    try:
        fpar2                         = xbmc.translatePath(pPylib + '/multiarch/par2.' + parch)
        xbmcvfs.copy(fpar2, ppar2)
        os.chmod(ppar2, 0755)
        xbmc.log('AUDO: Copied par2 for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('AUDO: Error Copying par2 for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

if not xbmcvfs.exists(punrar):
    try:
        funrar                        = xbmc.translatePath(pPylib + '/multiarch/unrar.' + parch)
        xbmcvfs.copy(funrar, punrar)
        os.chmod(punrar, 0755)
        xbmc.log('AUDO: Copied unrar for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('AUDO: Error Copying unrar for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

if not xbmcvfs.exists(punzip):
    try:
        funzip                        = xbmc.translatePath(pPylib + '/multiarch/unzip.' + parch)
        xbmcvfs.copy(funzip, punzip)
        os.chmod(punzip, 0755)
        xbmc.log('AUDO: Copied unzip for ' + parch, level=xbmc.LOGDEBUG)
    except Exception, e:
        xbmc.log('AUDO: Error Copying unzip for ' + parch, level=xbmc.LOGERROR)
        xbmc.log(str(e), level=xbmc.LOGERROR)

os.environ['PYTHONPATH'] = str(os.environ.get('PYTHONPATH')) + ':' + pPylib

# SABnzbd start
try:
    # write SABnzbd settings
    # ----------------------
    sabNzbdConfig = ConfigObj(pSabNzbdSettings, create_empty=True)
    defaultConfig = ConfigObj()
    defaultConfig['misc'] = {}
    defaultConfig['misc']['disable_api_key']   = '0'
    defaultConfig['misc']['check_new_rel']     = '0'
    defaultConfig['misc']['auto_browser']      = '0'
    defaultConfig['misc']['username']          = user
    defaultConfig['misc']['password']          = pwd
    defaultConfig['misc']['port']              = '8081'
    defaultConfig['misc']['https_port']        = '9081'
    defaultConfig['misc']['https_cert']        = 'server.cert'
    defaultConfig['misc']['https_key']         = 'server.key'
    defaultConfig['misc']['host']              = host
    defaultConfig['misc']['web_dir']           = 'Plush'
    defaultConfig['misc']['web_dir2']          = 'Plush'
    defaultConfig['misc']['web_color']         = 'gold'
    defaultConfig['misc']['web_color2']        = 'gold'
    defaultConfig['misc']['log_dir']           = 'logs'
    defaultConfig['misc']['admin_dir']         = 'admin'
    defaultConfig['misc']['nzb_backup_dir']    = 'backup'
    defaultConfig['misc']['script_dir']        = 'scripts'

    if firstLaunch:
        defaultConfig['misc']['download_dir']  = pSabNzbdIncomplete
        defaultConfig['misc']['complete_dir']  = pSabNzbdComplete
        servers = {}
        servers['localhost'] = {}
        servers['localhost']['host']           = 'localhost'
        servers['localhost']['port']           = '119'
        servers['localhost']['enable']         = '0'
        categories = {}
        categories['tv'] = {}
        categories['tv']['name']               = 'tv'
        categories['tv']['script']             = 'sabToSickBeard.py'
        categories['tv']['priority']           = '-100'
        categories['movies'] = {}
        categories['movies']['name']           = 'movies'
        categories['movies']['dir']            = 'movies'
        categories['movies']['priority']       = '-100'
        categories['music'] = {}
        categories['music']['name']            = 'music'
        categories['music']['dir']             = 'music'
        categories['music']['priority']        = '-100'
        defaultConfig['servers'] = servers
        defaultConfig['categories'] = categories

    sabNzbdConfig.merge(defaultConfig)
    sabNzbdConfig.write()

    # also keep the autoProcessTV config up to date
    autoProcessConfig = ConfigObj(xbmc.translatePath(pSabNzbdScripts + '/autoProcessTV.cfg'), create_empty=True)
    defaultConfig = ConfigObj()
    defaultConfig['SickBeard'] = {}
    defaultConfig['SickBeard']['host']         = 'localhost'
    defaultConfig['SickBeard']['port']         = '8082'
    defaultConfig['SickBeard']['username']     = user
    defaultConfig['SickBeard']['password']     = pwd
    autoProcessConfig.merge(defaultConfig)
    autoProcessConfig.write()

    # launch SABnzbd and get the API key
    # ----------------------------------
    if firstLaunch or sabnzbd_launch:
        xbmc.log('AUDO: Launching SABnzbd...', level=xbmc.LOGDEBUG)
        subprocess.call(sabnzbd, close_fds=True)
        xbmc.log('AUDO: ...done', level=xbmc.LOGDEBUG)

        # SABnzbd will only complete the .ini file when we first access the web interface
        if firstLaunch:
            try:
                if not (user and pwd):
                    urllib2.urlopen('http://' + sabNzbdHost)
                else:
                    urllib2.urlopen('http://' + sabNzbdHost + '/api?mode=queue&output=xml&ma_username=' + user +
                                    '&ma_password=' + pwd)
            except Exception, e:
                xbmc.log('AUDO: SABnzbd exception occurred', level=xbmc.LOGERROR)
                xbmc.log(str(e), level=xbmc.LOGERROR)

        sabNzbdConfig.reload()
        sabNzbdApiKey = sabNzbdConfig['misc']['api_key']

        if firstLaunch and not sabnzbd_launch:
            urllib2.urlopen('http://' + sabNzbdHost + '/api?mode=shutdown&apikey=' + sabNzbdApiKey)
            xbmc.log('AUDO: Shutting SABnzbd down...', level=xbmc.LOGDEBUG)

except Exception, e:
    xbmc.log('AUDO: SABnzbd exception occurred', level=xbmc.LOGERROR)
    xbmc.log(str(e), level=xbmc.LOGERROR)
# SABnzbd end

# SickBeard start
try:
    # write SickBeard settings
    # ------------------------
    sickBeardConfig = ConfigObj(pSickBeardSettings, create_empty=True)
    defaultConfig = ConfigObj()
    defaultConfig['General'] = {}
    defaultConfig['General']['launch_browser'] = '0'
    defaultConfig['General']['version_notify'] = '0'
    defaultConfig['General']['use_api']        = '1'
    defaultConfig['General']['web_port']       = '8082'
    defaultConfig['General']['web_host']       = host
    defaultConfig['General']['web_username']   = user
    defaultConfig['General']['web_password']   = pwd
    defaultConfig['General']['cache_dir']      = __addonhome__ + 'sbcache'
    defaultConfig['General']['log_dir']        = __addonhome__ + 'logs'
    defaultConfig['SABnzbd'] = {}
    defaultConfig['XBMC'] = {}
    defaultConfig['XBMC']['use_xbmc']          = '1'
    defaultConfig['XBMC']['xbmc_host']         = 'localhost:' + xbmcPort
    defaultConfig['XBMC']['xbmc_username']     = xbmcUser
    defaultConfig['XBMC']['xbmc_password']     = xbmcPwd

    if sabnzbd_launch:
        defaultConfig['SABnzbd']['sab_username']   = user
        defaultConfig['SABnzbd']['sab_password']   = pwd
        defaultConfig['SABnzbd']['sab_apikey']     = sabNzbdApiKey
        defaultConfig['SABnzbd']['sab_host']       = 'http://' + sabNzbdHost + '/'

    if transauth:
        defaultConfig['TORRENT'] = {}
        defaultConfig['TORRENT']['torrent_username']         = transuser
        defaultConfig['TORRENT']['torrent_password']         = transpwd
        defaultConfig['TORRENT']['torrent_path']             = pSabNzbdCompleteTV
        defaultConfig['TORRENT']['torrent_host']             = 'http://localhost:9091/'

    if sbfirstLaunch:
        defaultConfig['General']['tv_download_dir']       = pSabNzbdComplete
        defaultConfig['General']['metadata_xbmc_12plus']  = '0|0|0|0|0|0|0|0|0|0'
        defaultConfig['General']['nzb_method']            = 'sabnzbd'
        defaultConfig['General']['keep_processed_dir']    = '0'
        defaultConfig['General']['use_banner']            = '1'
        defaultConfig['General']['rename_episodes']       = '1'
        defaultConfig['General']['naming_ep_name']        = '0'
        defaultConfig['General']['naming_use_periods']    = '1'
        defaultConfig['General']['naming_sep_type']       = '1'
        defaultConfig['General']['naming_ep_type']        = '1'
        defaultConfig['General']['root_dirs']             = '0|/storage/tvshows'
        defaultConfig['General']['naming_custom_abd']     = '0'
        defaultConfig['General']['naming_abd_pattern']    = '%SN - %A-D - %EN'
        defaultConfig['Blackhole'] = {}
        defaultConfig['Blackhole']['torrent_dir']         = pSabNzbdWatchDir
        defaultConfig['SABnzbd']['sab_category']          = 'tv'
        # workaround: on first launch, sick beard will always add 
        # 'http://' and trailing '/' on its own
        defaultConfig['SABnzbd']['sab_host']              = sabNzbdHost
        defaultConfig['XBMC']['xbmc_notify_ondownload']   = '1'
        defaultConfig['XBMC']['xbmc_update_library']      = '1'
        defaultConfig['XBMC']['xbmc_update_full']         = '1'

    sickBeardConfig.merge(defaultConfig)
    sickBeardConfig.write()

    # launch SickBeard
    # ----------------
    if sickbeard_launch:
        xbmc.log('AUDO: Launching SickBeard...', level=xbmc.LOGDEBUG)
        subprocess.call(sickBeard, close_fds=True)
        xbmc.log('AUDO: ...done', level=xbmc.LOGDEBUG)
except Exception, e:
    xbmc.log('AUDO: SickBeard exception occurred', level=xbmc.LOGERROR)
    xbmc.log(str(e), level=xbmc.LOGERROR)
# SickBeard end

# CouchPotatoServer start
try:
    # empty password hack
    if pwd == '':
        md5pwd = ''
    else:
        #convert password to md5
        md5pwd = hashlib.md5(str(pwd)).hexdigest()

    # write CouchPotatoServer settings
    # --------------------------
    couchPotatoServerConfig = ConfigObj(pCouchPotatoServerSettings, create_empty=True, list_values=False)
    defaultConfig = ConfigObj()
    defaultConfig['core'] = {}
    defaultConfig['core']['username']            = user
    defaultConfig['core']['password']            = md5pwd
    defaultConfig['core']['port']                = '8083'
    defaultConfig['core']['launch_browser']      = '0'
    defaultConfig['core']['host']                = host
    defaultConfig['core']['data_dir']            = __addonhome__
    defaultConfig['core']['show_wizard']         = '0'
    defaultConfig['core']['debug']               = '0'
    defaultConfig['core']['development']         = '0'
    defaultConfig['updater'] = {}
    defaultConfig['updater']['enabled']          = '0'
    defaultConfig['updater']['notification']     = '0'
    defaultConfig['updater']['automatic']        = '0'
    defaultConfig['xbmc'] = {}
    defaultConfig['xbmc']['enabled']             = '1'
    defaultConfig['xbmc']['host']                = 'localhost:' + xbmcPort
    defaultConfig['xbmc']['username']            = xbmcUser
    defaultConfig['xbmc']['password']            = xbmcPwd
    defaultConfig['Sabnzbd'] = {}

    if sabnzbd_launch:
        defaultConfig['Sabnzbd']['username']     = user
        defaultConfig['Sabnzbd']['password']     = pwd
        defaultConfig['Sabnzbd']['api_key']      = sabNzbdApiKey
        defaultConfig['Sabnzbd']['host']         = sabNzbdHost

    if transauth:
        defaultConfig['transmission'] = {}
        defaultConfig['transmission']['username']         = transuser
        defaultConfig['transmission']['password']         = transpwd
        defaultConfig['transmission']['directory']        = pSabNzbdCompleteMov
        defaultConfig['transmission']['host']             = 'localhost:9091'

    if cpfirstLaunch:
        defaultConfig['xbmc']['xbmc_update_library']      = '1'
        defaultConfig['xbmc']['xbmc_update_full']         = '1'
        defaultConfig['xbmc']['xbmc_notify_onsnatch']     = '1'
        defaultConfig['xbmc']['xbmc_notify_ondownload']   = '1'
        defaultConfig['blackhole'] = {}
        defaultConfig['blackhole']['directory']           = pSabNzbdWatchDir
        defaultConfig['blackhole']['use_for']             = 'both'
        defaultConfig['blackhole']['enabled']             = '0'
        defaultConfig['Sabnzbd']['category']              = 'movies'
        defaultConfig['Sabnzbd']['pp_directory']          = pSabNzbdCompleteMov
        defaultConfig['renamer'] = {}
        defaultConfig['renamer']['enabled']               = '1'
        defaultConfig['renamer']['from']                  = pSabNzbdCompleteMov
        defaultConfig['renamer']['to']                    = '/storage/videos'
        defaultConfig['renamer']['separator']             = '.'
        defaultConfig['renamer']['cleanup']               = '0'
        defaultConfig['core']['permission_folder']        = '0644'
        defaultConfig['core']['permission_file']          = '0644'

    couchPotatoServerConfig.merge(defaultConfig)
    couchPotatoServerConfig.write()

    # launch CouchPotatoServer
    # ------------------
    if couchpotato_launch:
        xbmc.log('AUDO: Launching CouchPotatoServer...', level=xbmc.LOGDEBUG)
        subprocess.call(couchPotatoServer, close_fds=True)
        xbmc.log('AUDO: ...done', level=xbmc.LOGDEBUG)
except Exception, e:
    xbmc.log('AUDO: CouchPotatoServer exception occurred', level=xbmc.LOGERROR)
    xbmc.log(str(e), level=xbmc.LOGERROR)
# CouchPotatoServer end

# Headphones start
try:
    # write Headphones settings
    # -------------------------
    headphonesConfig = ConfigObj(pHeadphonesSettings, create_empty=True)
    defaultConfig = ConfigObj()
    defaultConfig['General'] = {}
    defaultConfig['General']['launch_browser']            = '0'
    defaultConfig['General']['api_enabled']               = '1'
    defaultConfig['General']['http_port']                 = '8084'
    defaultConfig['General']['http_host']                 = host
    defaultConfig['General']['http_username']             = user
    defaultConfig['General']['http_password']             = pwd
    defaultConfig['General']['check_github']              = '0'
    defaultConfig['General']['check_github_on_startup']   = '0'
    defaultConfig['General']['cache_dir']                 = __addonhome__ + 'hpcache'
    defaultConfig['General']['log_dir']                   = __addonhome__ + 'logs'
    defaultConfig['XBMC'] = {}
    defaultConfig['XBMC']['xbmc_enabled']                 = '1'
    defaultConfig['XBMC']['xbmc_host']                    = 'localhost:' + xbmcPort
    defaultConfig['XBMC']['xbmc_username']                = xbmcUser
    defaultConfig['XBMC']['xbmc_password']                = xbmcPwd
    defaultConfig['SABnzbd'] = {}

    if sabnzbd_launch:
        defaultConfig['SABnzbd']['sab_apikey']         = sabNzbdApiKey
        defaultConfig['SABnzbd']['sab_host']           = sabNzbdHost
        defaultConfig['SABnzbd']['sab_username']       = user
        defaultConfig['SABnzbd']['sab_password']       = pwd

    if transauth:
        defaultConfig['Transmission'] = {}
        defaultConfig['Transmission']['transmission_username'] = transuser
        defaultConfig['Transmission']['transmission_password'] = transpwd
        defaultConfig['Transmission']['transmission_host']     = 'http://localhost:9091'

    if hpfirstLaunch:
        defaultConfig['SABnzbd']['sab_category']               = 'music'
        defaultConfig['XBMC']['xbmc_update']                   = '1'
        defaultConfig['XBMC']['xbmc_notify']                   = '1'
        defaultConfig['General']['music_dir']                  = '/storage/music'
        defaultConfig['General']['destination_dir']            = '/storage/music'
        defaultConfig['General']['torrentblackhole_dir']       = pSabNzbdWatchDir
        defaultConfig['General']['download_dir']               = pSabNzbdCompleteMusic
        defaultConfig['General']['move_files']                 = '1'
        defaultConfig['General']['rename_files']               = '1'
        defaultConfig['General']['folder_permissions']         = '0644'

    headphonesConfig.merge(defaultConfig)
    headphonesConfig.write()

    # launch Headphones
    # -----------------
    if headphones_launch:
        xbmc.log('AUDO: Launching Headphones...', level=xbmc.LOGDEBUG)
        subprocess.call(headphones, close_fds=True)
        xbmc.log('AUDO: ...done', level=xbmc.LOGDEBUG)
except Exception, e:
    xbmc.log('AUDO: Headphones exception occurred', level=xbmc.LOGERROR)
    xbmc.log(str(e), level=xbmc.LOGERROR)
# Headphones end
