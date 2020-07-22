#email testing imports
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
import smtplib
import time
import os


#email testing function: why is date not included in function inputs?
def send_email(fro, to, subject, text, files=[]):
    msg = MIMEMultipart()
    msg['From'] = fro
    msg['To'] = " ,".join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text)) #?
    for file in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(file, "rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' %os.path.basename(file))
        msg.attach(part)
    server_name = "mail.dnr.wa.gov" #The mail server is specific to DNR
    # The machine you run the script from MUST be behind the DNR firewall
    smtp = smtplib.SMTP(server_name)
    smtp.ehlo()
    smtp.sendmail(fro, to, msg.as_string())
    smtp.close()