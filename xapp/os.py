from __future__ import absolute_import

import os
import psutil
import subprocess

### SESSION DETECTION

SESSION_CINNAMON = "Cinnamon"
SESSION_MATE = "MATE"
SESSION_XFCE = "XFCE"
SESSION_KDE = "KDE"
SESSION_GNOME = "GNOME"
SESSION_UNKNOWN = ""

def get_current_desktop():

    session = os.getenv("XDG_CURRENT_DESKTOP", SESSION_UNKNOWN)

    for name in (SESSION_CINNAMON, SESSION_MATE, SESSION_XFCE, SESSION_KDE):
        if session.lower() == name.lower():
            return name

    if session == "X-Cinnamon":
        return SESSION_CINNAMON

    return SESSION_UNKNOWN

def is_desktop_cinnamon():
    return get_current_desktop() == SESSION_CINNAMON

def is_desktop_mate():
    return get_current_desktop() == SESSION_MATE

def is_desktop_xfce():
    return get_current_desktop() == SESSION_XFCE

def is_desktop_kde():
    return get_current_desktop() == SESSION_KDE

def is_desktop_gnome():
    return get_current_desktop() == SESSION_GNOME

def is_live_session():
    is_live_session = False
    if os.access("/proc/cmdline", os.R_OK):
        cmdline = subprocess.check_output("cat /proc/cmdline", shell = True).decode("utf-8")
        for keyword in ["boot=casper", "boot=live"]:
            if keyword in cmdline:
                is_live_session = True
                break
    return is_live_session

def is_guest_session():
    home_path = os.path.expanduser("~")
    if "/tmp/guest" in home_path:
        return True
    else:
        return False

### PROCESS DETECTION

def is_process_running(process_name):
    for pid in psutil.pids():
        p = psutil.Process(pid)
        if p.name() == process_name:
            return True
    return False

### POLKIT SUPPORT

def is_polkit_running():

    # Check that pkexec is present
    if not os.path.exists("/usr/bin/pkexec"):
        return False

    # Check that the polkit agent is running
    if is_desktop_kde() and is_process_running("polkit-kde-authentication-agent-1"):
        return True
    if is_desktop_mate() and is_process_running("polkit-mate-authentication-agent-1"):
        return True
    elif is_process_running("polkit-gnome-authentication-agent-1"):
        return True
    elif is_process_running("polkitd"):
        return True
    else:
        return False

def pkexec(command):
    if not isinstance(command, list):
        command = command.split(" ")

    subprocess.call(["/usr/bin/pkexec"] + command)

### Run as root

def run_with_admin_privs(command, message=None, icon=None, support_pkexec=False):
    if not isinstance(command, list):
        command = command.split(" ")

    if is_polkit_running() and support_pkexec:
        pkexec(command)
        return True
    elif os.path.exists("/usr/bin/gksu"):
        commands = ["gksu"]
        if message is not None:
            commands = commands + ["--message", "<b>%s</b>" % message]
        commands = commands + command
        subprocess.Popen(commands)
        return True
    elif os.path.exists("/usr/bin/kdesudo"):
        commands = ["kdesudo", "-d"]
        if icon is not None:
            commands = commands + ["-i", icon]
        if message is not None:
            commands = commands + ["--comment", "<b>%s</b>" % message]
        commands = commands + command
        subprocess.Popen(commands)
        return True
    # Finally use pkexec if we have nothing else - it will work, but the executed program
    # may not be properly localized.
    elif is_polkit_running():
        pkexec(command)
        return True
    else:
        return False

### NETWORK PROXY

PROXY_SCHEMA = "org.gnome.system.proxy"

def _build_proxy_url(parent_settings, scheme):
    child = parent_settings.get_child(scheme)
    host = child.get_string("host")

    if not host:
        return None

    port = child.get_int("port")

    user = ""
    password = ""

    if scheme == "http" and child.get_boolean("use-authentication"):
        user = child.get_string("authentication-user")
        password = child.get_string("authentication-password")

    url = "" if "://" in host else "http://"

    if user:
        if password:
            url += "%s:%s@" % (user, password)
        else:
            url += "%s@" % user

    url += host

    if port > 0:
        url += ":%d" % port

    return url

def _maybe_set_env(name, value):
    if value is None:
        return
    if os.environ.get(name) or os.environ.get(name.upper()):
        return
    os.environ[name] = value

def add_network_proxy_to_env():
    """Read system proxy config from GSettings and populate http_proxy,
    https_proxy and no_proxy in os.environ so that requests, urllib, etc.
    use the configured proxy.

    Existing values are preserved - if http_proxy or HTTP_PROXY is already
    set, it is not overwritten. Should be called early in startup, before
    any networking happens."""
    from gi.repository import Gio
    source = Gio.SettingsSchemaSource.get_default()
    if source is None or source.lookup(PROXY_SCHEMA, True) is None:
        return

    settings = Gio.Settings.new(PROXY_SCHEMA)
    if settings.get_string("mode") != "manual":
        return

    _maybe_set_env("http_proxy", _build_proxy_url(settings, "http"))
    _maybe_set_env("https_proxy", _build_proxy_url(settings, "https"))

    if not os.environ.get("no_proxy") and not os.environ.get("NO_PROXY"):
        ignore_hosts = settings.get_strv("ignore-hosts")
        if ignore_hosts:
            os.environ["no_proxy"] = ",".join(ignore_hosts)
