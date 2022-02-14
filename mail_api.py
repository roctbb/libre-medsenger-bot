import email
import imaplib
import uuid
from email.message import EmailMessage
from email.header import decode_header
from config import *
import re


def decode_body(part):
    try:
        body_data = part.get_payload(decode=True)
        charset = part.get_param("charset", "ASCII")
        return body_data.decode(charset, errors="replace")
    except:
        pass


def extract_code(text):
    regex = r"безопасности: (\d+)"
    codes = re.findall(regex, text)

    if codes:
        return codes[0]
    else:
        return None


def get_last_message():
    mail = imaplib.IMAP4_SSL(EMAIL_SERVER)
    mail.login(EMAIL, EMAIL_PASSWORD)
    mail.select('inbox')

    status, data = mail.search(None, 'ALL')

    mail_ids = []

    for block in data:
        mail_ids += block.split()

    mail_id = max(list(map(lambda x: int(x.decode('ascii')), mail_ids)))

    status, data = mail.fetch(str(mail_id), '(RFC822)')

    if status == 'OK':
        for response_part in data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1], _class=EmailMessage)
                return message

    return None


def get_code():
    message = get_last_message()
    for part in message.walk():
        if part.get_content_type() in ['text/plain']:
            text = decode_body(part)
            return extract_code(text)
