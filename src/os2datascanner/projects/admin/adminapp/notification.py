import structlog

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from django.template import loader

from .models.scannerjobs.scanner_model import Scanner, ScanStatus

logger = structlog.get_logger(__name__)

GIGABYTE = 1073741824
MEGABYTE = 1048576


def send_mail_upon_completion(scanner: Scanner, scan_status: ScanStatus):
    """
    Send a mail to scannerjob responsible when a scannerjob has finished.
    """
    txt_mail_template = loader.get_template("mail/finished_scannerjob.txt")
    html_mail_template = loader.get_template("mail/finished_scannerjob.html")

    # Find suitable user to notify.
    username = scan_status.scan_tag.get("user")
    user = User.objects.filter(username=username).first() if username else None
    email = user.email if user else scanner.organization.contact_email

    context = create_context(scanner, scan_status, user)
    logger.info(f"Created context for info mail: {context}")

    msg = create_msg(context, user, email,
                     txt_mail_template, html_mail_template)

    send_msg(msg)


def create_context(scanner: Scanner, scan_status: ScanStatus, user: User):
    """
    Creates a context dict for the finished scannerjob ready for rendering.
    """
    context = {
        "admin_login_url": settings.SITE_URL,
        "institution": settings.NOTIFICATION_INSTITUTION,
        "full_name": user.get_full_name() or user.username if user else "",
        "total_objects": scan_status.total_objects,
        "scanner_name": scanner.name,
        "object_size": get_formatted_object_size(scan_status),
        "completion_time": get_scanner_time(scan_status)
    }

    return context


def get_scanner_time(scan_status: ScanStatus):
    """
    Calculates and formats the total runtime for the scannerjob.
    """
    total_time = scan_status.last_modified - scan_status.start_time

    hours = round(total_time.total_seconds() // 3600)
    minutes = round((total_time.total_seconds() % 3600) // 60)
    seconds = round((total_time.total_seconds() % 3600) % 60)

    return str(hours) + "t" + str(minutes) + "m" + str(seconds) + "s"


def get_formatted_object_size(scan_status: ScanStatus):
    """
    Calculates the total size of all scanned objects for a scannerjob in gigabytes (GB).
    """
    gigabytes = round(scan_status.scanned_size / GIGABYTE, 2)
    return str(gigabytes) + "GB"


def create_msg(context, user, email, txt_mail_template, html_mail_template):
    """
    Creates an mail message from templates together with user and context data.
    """
    msg = EmailMultiAlternatives(
        "Dit OS2datascanner-scan er kørt færdigt.",
        txt_mail_template.render(context),
        settings.DEFAULT_FROM_EMAIL,
        [email])
    msg.attach_alternative(html_mail_template.render(context), "text/html")
    return msg


def send_msg(msg):
    """
    Tries to send an email message and logs the result.
    """
    try:
        msg.send()
        logger.info("Info mail sent successfully.")
    except Exception as ex:
        logger.info(f"Could not send mail. Error: {ex}.")
