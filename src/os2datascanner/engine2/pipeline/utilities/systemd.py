import systemd.daemon
if systemd.daemon.booted():
    from systemd.daemon import notify as sd_notify
else:
    def sd_notify(status):
        return False


def notify_ready():
    sd_notify("READY=1")


def notify_reloading():
    sd_notify("RELOADING=1")


def notify_stopping():
    sd_notify("STOPPING=1")


def notify_status(msg):
    sd_notify("STATUS={0}".format(msg))


def notify_watchdog():
    sd_notify("WATCHDOG=1")
