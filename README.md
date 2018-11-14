# Email Trigger

For some bullshit network security - in some offices/labs even simple printing to 
b/w or colored printers might become a complete **nightmare**.
Indeed this was my case. Printing is only permitted from desktop computers inside
a particular "protected" subnetwork. What if you a using a laptop? What if you want
print your presentation from your smartphone before a keynote? You're screwed! You
should send the document to youself, power on a **10 years old desktop** 
(wait from 1 to 5 minutes), login, download the document, print and 
go back to your audience (hoping that someone will still be there).

With this simple script, all this waste of time is gone! You just need the desktop 
to be powered on and to have `python3` installed (**no** additional packages are required). 
This script simply spawns a daemon that will continuously check your email inbox for 
new document to print. 

## Configuration
Before running the daemon you will need to create a configuration file under `./dev/secrets.py`.
It has to define a couple of variables, as follows

```python 
username = 'username'
password = 'password'
imap_ssl_host = 'mail.google.com'
imap_ssl_port = 993
filter_criteria = {
    'FROM': 'trump@whitehouse.gov', 
    'SUBJECT': 'print',
}
```

The `filter_criteria` dictionary is used to filter your inbox for new email. If an email match these
criteria, the full message will be downloaded and its `pdf` attachments will be printed.

## Usage 

To start the daemon (once started, you can safely close the terminal - logs will be 
stored in `./dev/logs/`):
```bash
> python3 dev/event_daemon.py start
[2018-11-14 16:32:30,513 INFO] Starting...
[2018-11-14 16:32:30,551 INFO] Daemon started with pid 2723
```

To stop the daemon:
```bash
> python3 dev/event_daemon.py stop
[2018-11-14 16:32:32,013 INFO] Stopping...
[2018-11-14 16:32:32,151 INFO] Daemon with pid 2723 is stopped
```

To restart the daemon (it will stop and than start again):
```bash
> python3 dev/event_daemon.py restart
[2018-11-14 16:32:32,013 INFO] Stopping...
[2018-11-14 16:32:32,151 INFO] Daemon with pid 2723 is stopped
[2018-11-14 16:32:32,513 INFO] Starting...
[2018-11-14 16:32:32,551 INFO] Daemon started with pid 2763
```

To inspect its state:
```bash
> python3 event_daemon.py info
[2018-11-14 16:40:08,547 INFO] Daemon is running with pid 16297
```
