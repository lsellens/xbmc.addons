# Initializes and launches Couchpotato V2, Sickbeard and Headphones

import os
import sys
import shutil
import subprocess
import hashlib
import signal
from xml.dom.minidom import parseString
import logging
import traceback
import platform

logging.basicConfig(filename='/var/log/sickpotatohead.log',
                    filemode='w',
                    format='%(asctime)s SickPotatoHead: %(message)s',
                    level=logging.WARNING)

# helper functions
# ----------------

def createDir(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)

def getAddonSetting(doc,id):
    for element in doc.getElementsByTagName('setting'):
        if element.getAttribute('id')==id:
            return element.getAttribute('value')


# define some things that we're gonna need, mainly paths
# ------------------------------------------------------

# addon
pAddon                        = os.path.expanduser('/storage/.xbmc/addons/service.downloadmanager.SickPotatoHead')
pAddonHome                    = os.path.expanduser('/storage/.xbmc/userdata/addon_data/service.downloadmanager.SickPotatoHead')

# settings
pDefaultSuiteSettings         = os.path.join(pAddon, 'settings-default.xml')
pSuiteSettings                = os.path.join(pAddonHome, 'settings.xml')
pXbmcSettings                 = '/storage/.xbmc/userdata/guisettings.xml'
pSickBeardSettings            = os.path.join(pAddonHome, 'sickbeard.ini')
pCouchPotatoServerSettings    = os.path.join(pAddonHome, 'couchpotatoserver.ini')
pHeadphonesSettings           = os.path.join(pAddonHome, 'headphones.ini')
pTransmission_Addon_Settings  ='/storage/.xbmc/userdata/addon_data/service.downloadmanager.transmission/settings.xml'

# directories
pSickPotatoHeadComplete       = '/storage/downloads'
pSickPotatoHeadCompleteMov    = '/storage/downloads/movies'
pSickPotatoHeadWatchDir       = '/storage/downloads/watch'

# service commands
sickBeard                     = ['python', os.path.join(pAddon, 'SickBeard/SickBeard.py'),
                                 '--daemon', '--datadir', pAddonHome, '--config', pSickBeardSettings]
couchPotatoServer             = ['python', os.path.join(pAddon, 'CouchPotatoServer/CouchPotato.py'),
                                 '--daemon', '--pid_file', os.path.join(pAddonHome, 'couchpotato.pid'), '--config_file', pCouchPotatoServerSettings]
headphones                    = ['python', os.path.join(pAddon, 'Headphones/Headphones.py'),
                                 '-d', '--datadir', pAddonHome, '--config', pHeadphonesSettings]

# create directories and settings if missing
# -----------------------------------------------

sbfirstLaunch = not os.path.exists(pSickBeardSettings)
cpfirstLaunch = not os.path.exists(pCouchPotatoServerSettings)
hpfirstLaunch = not os.path.exists(pHeadphonesSettings)
if sbfirstLaunch or cpfirstLaunch or hpfirstLaunch:
    createDir(pAddonHome)
    createDir(pSickPotatoHeadComplete)
    createDir(pSickPotatoHeadCompleteMov)
    createDir(pSickPotatoHeadWatchDir)

# create the settings file if missing
if not os.path.exists(pSuiteSettings):
    shutil.copy(pDefaultSuiteSettings, pSuiteSettings)

# read addon and xbmc settings
# ----------------------------

# Transmission-Daemon
if os.path.exists(pTransmission_Addon_Settings):
    fTransmission_Addon_Settings = open(pTransmission_Addon_Settings, 'r')
    data = fTransmission_Addon_Settings.read()
    fTransmission_Addon_Settings.close
    transmission_addon_settings = parseString(data)
    transuser                          = getAddonSetting(transmission_addon_settings, 'TRANSMISSION_USER')
    transpwd                           = getAddonSetting(transmission_addon_settings, 'TRANSMISSION_PWD')
    transauth                          = getAddonSetting(transmission_addon_settings, 'TRANSMISSION_AUTH')
else:
    transauth                          = 'false'

# SickPotatoHead-Suite
fSuiteSettings = open(pSuiteSettings, 'r')
data = fSuiteSettings.read()
fSuiteSettings.close
suiteSettings = parseString(data)
user                          = getAddonSetting(suiteSettings, 'SICKPOTATOHEAD_USER')
pwd                           = getAddonSetting(suiteSettings, 'SICKPOTATOHEAD_PWD')
host                          = getAddonSetting(suiteSettings, 'SICKPOTATOHEAD_IP')
sickbeard_launch              = getAddonSetting(suiteSettings, 'SICKBEARD_LAUNCH')
couchpotato_launch            = getAddonSetting(suiteSettings, 'COUCHPOTATO_LAUNCH')
headphones_launch             = getAddonSetting(suiteSettings, 'HEADPHONES_LAUNCH')

# merge defaults
fDefaultSuiteSettings         = open(pDefaultSuiteSettings, 'r')
data = fDefaultSuiteSettings.read()
fDefaultSuiteSettings.close
DefaultSuiteSettings = parseString(data)
if not sickbeard_launch:
    sickbeard_launch          = getAddonSetting(DefaultSuiteSettings, 'SICKBEARD_LAUNCH')
if not couchpotato_launch:
    couchpotato_launch        = getAddonSetting(DefaultSuiteSettings, 'COUCHPOTATO_LAUNCH')
if not headphones_launch:
    headphones_launch         = getAddonSetting(DefaultSuiteSettings, 'HEADPHONES_LAUNCH')

# XBMC
fXbmcSettings                 = open(pXbmcSettings, 'r')
data                          = fXbmcSettings.read()
fXbmcSettings.close
xbmcSettings                  = parseString(data)
xbmcServices                  = xbmcSettings.getElementsByTagName('services')[0]
xbmcPort                      = xbmcServices.getElementsByTagName('webserverport')[0].firstChild.data
try:
    xbmcUser                      = xbmcServices.getElementsByTagName('webserverusername')[0].firstChild.data
except:
    xbmcUser                      = ''
try:
    xbmcPwd                       = xbmcServices.getElementsByTagName('webserverpassword')[0].firstChild.data
except:
    xbmcPwd                       = ''

# prepare execution environment
# -----------------------------
signal.signal(signal.SIGCHLD, signal.SIG_DFL)
pPylib                        = os.path.join(pAddon, 'pylib')
if "true" in sickbeard_launch:
    pnamemapper                   = os.path.join(pPylib, 'Cheetah/_namemapper.so')
    if not os.path.exists(pnamemapper):
        try:
            parch                         = platform.machine()
            if parch.startswith('arm'):
                parch = 'arm'
            pmultiarch                    = os.path.join(pPylib, 'multiarch/_namemapper.so.' + parch)
            shutil.copy(pmultiarch, pnamemapper)
            logging.debug('Copied _namemapper.so for ' + parch)
        except Exception,e:
            logging.error('Error Copying _namemapper.so for ' + parch)
            logging.exception(e)
        
os.environ['PYTHONPATH']      = str(os.environ.get('PYTHONPATH')) + ':' + pPylib
sys.path.append(pPylib)
from configobj import ConfigObj

# SickBeard start
try:
    # write SickBeard settings
    # ------------------------
    sickBeardConfig = ConfigObj(pSickBeardSettings,create_empty=True)
    defaultConfig = ConfigObj()
    defaultConfig['General'] = {}
    defaultConfig['General']['launch_browser']      = '0'
    defaultConfig['General']['version_notify']      = '0'
    defaultConfig['General']['web_port']            = '8082'
    defaultConfig['General']['web_host']            = host
    defaultConfig['General']['web_username']        = user
    defaultConfig['General']['web_password']        = pwd
    defaultConfig['General']['cache_dir']           = pAddonHome + '/sbcache'
    defaultConfig['General']['log_dir']             = pAddonHome + '/logs'
    defaultConfig['XBMC'] = {}
    defaultConfig['XBMC']['use_xbmc']               = '1'
    defaultConfig['XBMC']['xbmc_host']              = '127.0.0.1:' + xbmcPort
    defaultConfig['XBMC']['xbmc_username']          = xbmcUser
    defaultConfig['XBMC']['xbmc_password']          = xbmcPwd

    if sbfirstLaunch:
        defaultConfig['General']['tv_download_dir']       = pSickPotatoHeadComplete
        defaultConfig['General']['metadata_xbmc']         = '0|0|0|0|0|0'
        defaultConfig['General']['keep_processed_dir']    = '0'
        defaultConfig['General']['use_banner']            = '1'
        defaultConfig['General']['rename_episodes']       = '1'
        defaultConfig['General']['naming_ep_name']        = '0'
        defaultConfig['General']['naming_use_periods']    = '1'
        defaultConfig['General']['naming_sep_type']       = '1'
        defaultConfig['General']['naming_ep_type']        = '1'
        defaultConfig['General']['root_dirs']             = '0|/storage/tvshows'
        defaultConfig['Blackhole'] = {}
        defaultConfig['Blackhole']['torrent_dir']         = pSickPotatoHeadWatchDir
        defaultConfig['EZRSS'] = {}
        defaultConfig['EZRSS']['ezrss']                   = '1'
        defaultConfig['Womble'] = {}
        defaultConfig['Womble']['womble']                 = '0'
        defaultConfig['XBMC']['xbmc_notify_ondownload']   = '1'
        defaultConfig['XBMC']['xbmc_notify_onsnatch']     = '1'
        defaultConfig['XBMC']['xbmc_update_library']      = '1'
        defaultConfig['XBMC']['xbmc_update_full']         = '1'

    sickBeardConfig.merge(defaultConfig)
    sickBeardConfig.write()

    # launch SickBeard
    # ----------------
    if "true" in sickbeard_launch:
        subprocess.call(sickBeard,close_fds=True)
except Exception,e:
    logging.exception(e)
    print 'SickBeard: exception occurred:', e
    print traceback.format_exc()
# SickBeard end

# CouchPotatoServer start
try:
    # empty password hack
    if pwd == '':
        md5pwd = ''
    else:
        #convert password to md5
        md5pwd =  hashlib.md5(str(pwd)).hexdigest()

    # write CouchPotatoServer settings
    # --------------------------
    couchPotatoServerConfig = ConfigObj(pCouchPotatoServerSettings,create_empty=True, list_values=False)
    defaultConfig = ConfigObj()
    defaultConfig['core'] = {}
    defaultConfig['core']['username']               = user
    defaultConfig['core']['password']               = md5pwd
    defaultConfig['core']['port']                   = '8083'
    defaultConfig['core']['launch_browser']         = '0'
    defaultConfig['core']['host']                   = host
    defaultConfig['core']['data_dir']               = pAddonHome
    defaultConfig['core']['show_wizard']            = '0'
    defaultConfig['core']['debug']                  = '0'
    defaultConfig['core']['development']            = '0'
    defaultConfig['updater'] = {}
    defaultConfig['updater']['enabled']             = '0'
    defaultConfig['updater']['notification']        = '0'
    defaultConfig['updater']['automatic']           = '0'
    defaultConfig['xbmc'] = {}
    defaultConfig['xbmc']['enabled']                = '1'
    defaultConfig['xbmc']['host']                   = '127.0.0.1:' + xbmcPort
    defaultConfig['xbmc']['username']               = xbmcUser
    defaultConfig['xbmc']['password']               = xbmcPwd

    if 'true' in transauth:
        defaultConfig['transmission'] = {}
        defaultConfig['transmission']['username']         = transuser
        defaultConfig['transmission']['password']         = transpwd
        defaultConfig['transmission']['directory']        = pSickPotatoHeadCompleteMov
        defaultConfig['transmission']['host']             = '127.0.0.1:9091'

    if cpfirstLaunch:
        defaultConfig['xbmc']['xbmc_update_library']      = '1'
        defaultConfig['xbmc']['xbmc_update_full']         = '1'
        defaultConfig['xbmc']['xbmc_notify_onsnatch']     = '1'
        defaultConfig['xbmc']['xbmc_notify_ondownload']   = '1'
        defaultConfig['blackhole'] = {}
        defaultConfig['blackhole']['directory']           = pSickPotatoHeadWatchDir
        defaultConfig['blackhole']['use_for']             = 'torrent'
        defaultConfig['blackhole']['enabled']             = '0'
        defaultConfig['Renamer'] = {}
        defaultConfig['Renamer']['enabled']               = '0'
        defaultConfig['Renamer']['from']                  = pSickPotatoHeadCompleteMov
        defaultConfig['Renamer']['separator']             = '.'
        defaultConfig['Renamer']['cleanup']               = '0'
        defaultConfig['nzbindex'] = {}
        defaultConfig['nzbindex']['enabled']              = '0'
        defaultConfig['mysterbin'] = {}
        defaultConfig['mysterbin']['enabled']             = '0'
        defaultConfig['core']['permission_folder']        = '0644'
        defaultConfig['core']['permission_file']          = '0644'
        defaultConfig['searcher'] = {}
        defaultConfig['searcher']['preferred_method']     = 'torrent'

    couchPotatoServerConfig.merge(defaultConfig)
    couchPotatoServerConfig.write()

    # launch CouchPotatoServer
    # ------------------
    if "true" in couchpotato_launch:
        subprocess.call(couchPotatoServer,close_fds=True)
except Exception,e:
    logging.exception(e)
    print 'CouchPotatoServer: exception occurred:', e
    print traceback.format_exc()
# CouchPotatoServer end

# Headphones start
try:
    # write Headphones settings
    # -------------------------
    headphonesConfig = ConfigObj(pHeadphonesSettings,create_empty=True)
    defaultConfig = ConfigObj()
    defaultConfig['General'] = {}
    defaultConfig['General']['launch_browser']            = '0'
    defaultConfig['General']['http_port']                 = '8084'
    defaultConfig['General']['http_host']                 = host
    defaultConfig['General']['http_username']             = user
    defaultConfig['General']['http_password']             = pwd
    defaultConfig['General']['check_github']              = '0'
    defaultConfig['General']['check_github_on_startup']   = '0'
    defaultConfig['General']['cache_dir']                 = pAddonHome + '/hpcache'
    defaultConfig['General']['log_dir']                   = pAddonHome + '/logs'
    defaultConfig['XBMC'] = {}
    defaultConfig['XBMC']['xbmc_enabled']                 = '1'
    defaultConfig['XBMC']['xbmc_host']                    = '127.0.0.1:' + xbmcPort
    defaultConfig['XBMC']['xbmc_username']                = xbmcUser
    defaultConfig['XBMC']['xbmc_password']                = xbmcPwd

    if hpfirstLaunch:
        defaultConfig['XBMC']['xbmc_update']                  = '1'
        defaultConfig['XBMC']['xbmc_notify']                  = '1'
        defaultConfig['General']['torrentblackhole_dir']      = pSickPotatoHeadWatchDir
        defaultConfig['General']['download_torrent_dir']      = pSickPotatoHeadComplete
        defaultConfig['General']['move_files']                = '0'
        defaultConfig['General']['rename_files']              = '1'
        defaultConfig['General']['folder_permissions']        = '0644'

    headphonesConfig.merge(defaultConfig)
    headphonesConfig.write()

    # launch Headphones
    # -----------------
    if "true" in headphones_launch:
        subprocess.call(headphones,close_fds=True)
except Exception,e:
    logging.exception(e)
    print 'Headphones: exception occurred:', e
    print traceback.format_exc()
# Headphones end
