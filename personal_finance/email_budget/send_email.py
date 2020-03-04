import smtplib
import imghdr
from email.message import EmailMessage
import os

SEND_TO = 'richwolff12@gmail.com,dmpalladino@gmail.com'


def send_email(subject, ImgFileName):
    # Create the container email message.
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = os.getenv('MINT_MFA_IMAP_ACCOUNT')
    msg['To'] = SEND_TO

    with open(ImgFileName, 'rb') as fp:
        img_data = fp.read()
        msg.add_attachment(
            img_data,
            maintype='image',
            subtype=imghdr.what(None, img_data),
            filename=ImgFileName.split('/')[1]
        )
        
    # Send the email via our own SMTP server.
    with smtplib.SMTP("smtp.gmail.com", 587,) as s:
        s.starttls()
        s.login(os.getenv('MINT_MFA_IMAP_ACCOUNT'), os.getenv('MINT_MFA_IMAP_PWD'))
        s.send_message(msg)
