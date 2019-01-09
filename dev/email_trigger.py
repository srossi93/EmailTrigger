# Copyright (C) 2018   Simone Rossi <simone.rossi@eurecom.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import sys
import imaplib
import logging
import email
import time
import subprocess

from itertools import chain

def search_string(uid_max, criteria):
    """
        Produce search string in IMAP format:
        e.g. (FROM "me@gmail.com" SUBJECT "abcde" BODY "123456789" UID 9999:*)
    """
    c = list(map(lambda t: (t[0], '"'+str(t[1])+'"'), criteria.items())) + [('UID', '%d:*' % (uid_max+1))]
    return '(%s)' % ' '.join(chain(*c))



class EmailTrigger(object):
    def __init__(self, username, password, imap_ssl_host, imap_ssl_port, filter_criteria, printer_name):
        self.username = username
        self.password = password
        self.imap_ssl_host = imap_ssl_host
        self.imap_ssl_port = imap_ssl_port
        self.filter_criteria = filter_criteria
        self.delete_attachments_local = False

        self.printer_name = printer_name

        self._server = imaplib.IMAP4_SSL(self.imap_ssl_host, self.imap_ssl_port)
        self._logger = logging.getLogger(__name__)
        self._uid_max = 0

        self.login()

        uids = self.get_filtered_uids()
        self._uid_max = max(uids)
        self.logout()

    def login(self):
        self._server = imaplib.IMAP4_SSL(self.imap_ssl_host, self.imap_ssl_port)
        self._server.login(self.username, self.password)
        self._logger.debug('Server status: %s' % self._server.state)
        self._server.select('INBOX')

    def logout(self):
        if self._server.state == 'AUTH':
            self._server.logout()
        del self._server

    def get_filtered_uids(self):
        _, data = self._server.uid('search', None, search_string(self._uid_max, self.filter_criteria))
        uids = list(filter(lambda x: x > self._uid_max, [int(s) for s in data[0].split()]))
        return uids

    def sync(self):
        try:
            self.login()
            uids = self.get_filtered_uids()
            if len(uids) > 0:
                self._logger.info('%d new messages (UIDs = %s)' % (len(uids), ', '.join(map(str, uids))))
                self._process_new_emails(uids)
                self._uid_max = max(uids)
            self.logout()
        except KeyboardInterrupt:
            self._logger.warning('User kill. Exiting now...')
            sys.exit()




    def _process_new_emails(self, uids):
        for uid in uids:
            self._logger.info('Processing email UID %d' % uid)
            result, data = self._server.uid('fetch', str(uid), '(RFC822)')  # fetch entire message
            msg = email.message_from_bytes(data[0][1])

            payloads = self.get_payloads(msg, [])
            attachments = list(filter(lambda p: p.get_content_type() == 'application/octet-stream', payloads))
            filenames = self._save_attachments(attachments)
            self._process_attachments(filenames)

            if self.delete_attachments_local:
                self._delete_attachments(filenames)

    # ************* Private Methods *****************

    def get_payloads(self, msg, list_of_payloads):
        for payload in msg.get_payload():
            self._logger.info('New payload of type %s' % payload.get_content_type())
            if payload.get_content_type() == 'multipart/alternative':
                self.get_payloads(payload, list_of_payloads)
            else:
                list_of_payloads.append(payload)
        return list_of_payloads

    def _save_attachments(self, attachments):
        filenames = []
        for i, attach in enumerate(attachments):
            filename = 'attach-%02d.pdf' % i
            self._logger.info('Saving attachments %d in file %s' % (i, filename))
            with open(filename, 'wb') as fl:
                fl.write(attach.get_payload(decode=True))
            filenames.append(filename)
        return filenames

    def _process_attachments(self, filenames):
        for filename in filenames:
            self._logger.info('Processing file %s' % filename)
            command = ('lp -d %s -o sides=two-sided-long-edge %s' % (self.printer_name, filename)).split(' ')
            subprocess.Popen(command, stdout=None)

        time.sleep(1)
        while subprocess.run(['lpstat'], stdout=subprocess.PIPE,).stdout.decode('utf-8') != '':
            self._logger.info('Waiting for job to complete')
            time.sleep(1.5)

    def _delete_attachments(self, filenames):
        import os
        for filename in filenames:
            self._logger.info('Deleting file %s' % filename)
            os.remove(filename)

