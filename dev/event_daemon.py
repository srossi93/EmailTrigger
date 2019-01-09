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

import os
import sys
import logging
import logging.handlers
import time

from daemon import Daemon
from email_trigger import EmailTrigger
from secret import password, username, imap_ssl_host, imap_ssl_port, filter_criteria

class EventDaemon(Daemon):
    def __init__(self, pidfile, stdin=os.devnull,
                 stdout=os.devnull, stderr=os.devnull,
                 home_dir='.', umask=0o22, verbose=1,
                 use_gevent=False, use_eventlet=False, printer_name='tinee'):
        super(EventDaemon, self).__init__(pidfile, stdin, stdout,
                                          stderr, home_dir, umask,
                                          verbose, use_gevent, use_eventlet)

        self.email_trigger = EmailTrigger(username, password, imap_ssl_host, imap_ssl_port,
                                          filter_criteria[printer_name], printer_name)

    def run(self):
        while(1):
            self.email_trigger.sync()
            time.sleep(5)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Please, specify an action and a printer. Available: start|stop|restart|info printer_name')
        sys.exit()

    printer_name = sys.argv[2]

    stdout_handler = logging.StreamHandler(sys.stdout)
    rotating_handler = logging.handlers.TimedRotatingFileHandler('./log/event-trigger-%s.log' % printer_name,
                                                                 when="h",
                                                                 interval=1,
                                                                 backupCount=5)
    handlers = [stdout_handler, rotating_handler]

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s %(levelname)s] %(message)s',
        handlers=handlers)
    logger = logging.getLogger()

    pidfile_path = '~/.etp-daemon-%s.pidfile' % printer_name
    event_daemon = EventDaemon(os.path.expanduser(pidfile_path))

    #   event_daemon.run()

    if sys.argv[1] == 'start':
        event_daemon.start()
        sys.exit()
    if sys.argv[1] == 'stop':
        event_daemon.stop()
        sys.exit()
    if sys.argv[1] == 'restart':
        event_daemon.restart()
        sys.exit()
    if sys.argv[1] == 'info':
        event_daemon.is_running()
        sys.exit()


    logger.fatal('Unknown action. Available: start|stop|restart')


