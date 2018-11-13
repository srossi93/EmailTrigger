
import time
from itertools import chain
import email
import imaplib
import logging
import sys


stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [stdout_handler]

logging.basicConfig(
    level=logging.INFO, 
    format='[%(asctime)s %(levelname)s] %(message)s',
    handlers=handlers)

logger = logging.getLogger(__name__)

imap_ssl_host = 'log.eiuf.com'  # imap.mail.yahoo.com
imap_ssl_port = 993
username = 'asd09!09df'
password = 'QnckLNF2910Q?223#1'

# Restrict mail search. Be very specific.
# Machine should be very selective to receive messages.
criteria = {
    'FROM':    'rossi@eurecom.fr',
#    'SUBJECT': 'SPECIAL SUBJECT LINE',
#    'BODY':    'SECRET SIGNATURE',
}
uid_max = 0


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
# I don't like using IDLE because Yahoo does not support it.
try:
    while 1:
        # Have to login/logout each time because that's the only way to get fresh results.

        server = imaplib.IMAP4_SSL(imap_ssl_host, imap_ssl_port)
        server.login(username, password)
        logger.info('Server status: %s' % server.state)
        server.select('INBOX')

        result, data = server.uid('search', None, search_string(uid_max, criteria))

        uids = list(filter(lambda x: x > uid_max, [int(s) for s in data[0].split()]))
        logger.info('New message ids: %s' % str(uids))


        for uid in uids:
            # Have to check again because Gmail sometimes does not obey UID criterion.
            if uid > uid_max:
                result, data = server.uid('fetch', str(uid), '(RFC822)')  # fetch entire message
                msg = email.message_from_bytes(data[0][1])
                
                uid_max = uid
            
                print(msg)

                #text = get_first_text_block(msg)
                #print('New message :::::::::::::::::::::')
                #print(text)

        server.logout()
        logger.info('Server status: %s' % server.state)
        time.sleep(5)

except KeyboardInterrupt:
    logger.warning('User kill. Exiting now...')
    if server.state == 'AUTH':
        server.logout()