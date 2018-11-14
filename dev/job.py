
import time
from itertools import chain
import email
import imaplib
import logging
import sys

from secret import password, username, imap_ssl_host, imap_ssl_port


stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [stdout_handler]

logging.basicConfig(
    level=logging.INFO, 
    format='[%(asctime)s %(levelname)s] %(message)s',
    handlers=handlers)

logger = logging.getLogger(__name__)

# Restrict mail search. Be very specific.
# Machine should be very selective to receive messages.
criteria = {
    'FROM':    'rossi@eurecom.fr',
#    'SUBJECT': 'SPECIAL SUBJECT LINE',
#    'BODY':    'SECRET SIGNATURE',
}


def search_string(uid_max, criteria):
    c = list(map(lambda t: (t[0], '"'+str(t[1])+'"'), criteria.items())) + [('UID', '%d:*' % (uid_max+1))]
    return '(%s)' % ' '.join(chain(*c))
    # Produce search string in IMAP format:
    #   e.g. (FROM "me@gmail.com" SUBJECT "abcde" BODY "123456789" UID 9999:*)


def get_first_text_block(msg):
    type = msg.get_content_maintype()

    if type == 'multipart':
        for part in msg.get_payload():
            if part.get_content_maintype() == 'text':
                return part.get_payload()
    elif type == 'text':
        return msg.get_payload()


def get_payloads(msg, list_of_payloads):
    for payload in msg.get_payload():
        logger.info('New payload of type %s' % payload.get_content_type())
        if payload.get_content_type() == 'multipart/alternative':
            get_payloads(payload, list_of_payloads)
        else:
            list_of_payloads.append(payload)
    return list_of_payloads


def process_new_email(uids, server):
    for uid in uids:
        logger.info('Processing email UID %d' % uid)
        result, data = server.uid('fetch', str(uid), '(RFC822)')  # fetch entire message
        msg = email.message_from_bytes(data[0][1])

        payloads = get_payloads(msg, [])

        attachments = list(filter(lambda p: p.get_content_type() == 'application/octet-stream', payloads))

        filenames = save_attachments(attachments)

        process_attachments(filenames)

        delete_attachments(filenames)




def save_attachments(attachments):
    filenames = []
    for i, attach in enumerate(attachments):
        filename = 'attach-%02d.pdf' % i
        logger.info('Saving attachments %d in file %s' % (i, filename))
        with open(filename, 'wb') as fl:
            fl.write(attach.get_payload(decode=True))
        filenames.append(filename)
    return filenames

def process_attachments(filenames):
    import subprocess
    for filename in filenames:
        logger.info('Processing file %s' % filename)
        lpr = subprocess.Popen(["/bin/echo", filename], stdin=subprocess.PIPE)


def delete_attachments(filenames):
    import os
    for filename in filenames:
        logger.info('Deleting file %s' % filename)
        os.remove(filename)


def main():
    uid_max = 0
    server = imaplib.IMAP4_SSL(imap_ssl_host, imap_ssl_port)
    server.login(username, password)
    logger.info('Server status: %s' % server.state)
    server.select('INBOX')

    _, data = server.uid('search', None, search_string(uid_max, criteria))

    uids = [int(s) for s in data[0].split()]
    if uids:
        uid_max = max(uids)
        # Initialize `uid_max`. Any UID less than or equal to `uid_max` will be ignored subsequently.

    server.logout()
    logger.info('Server status: %s' % server.state)

    # Keep checking messages ...
    try:
        while 1:
            # Have to login/logout each time because that's the only way to get fresh results.

            server = imaplib.IMAP4_SSL(imap_ssl_host, imap_ssl_port)
            server.login(username, password)
            logger.info('Server status: %s' % server.state)
            server.select('INBOX')

            # Search mails that match the criteria
            result, data = server.uid('search', None, search_string(uid_max, criteria))

            # Get only new message id
            uids = list(filter(lambda x: x > uid_max, [int(s) for s in data[0].split()]))

            if len(uids) > 0:
                logger.info('%d new messages (UIDs = %s)' % (len(uids), ', '.join(map(str, uids))))
                process_new_email(uids, server)
                uid_max = max(uids)

            server.logout()
            logger.info('Server status: %s' % server.state)
            time.sleep(5)

    except KeyboardInterrupt:
        logger.warning('User kill. Exiting now...')
        if server.state == 'AUTH':
            server.logout()



if __name__ == '__main__':
    main()