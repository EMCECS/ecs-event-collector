#!/usr/local/bin/python
"""
Python script to collect daily events from ECS and mail them and/or upload
them to an S3 bucket for auditing purposes.
"""

import os
import sys
import yaml
import schedule
import ecscli
from requests import Request, Session
import pytz
import tzlocal
from datetime import datetime, time, timedelta, date, tzinfo
from time import sleep

CONFIG_FILE = "/etc/ecs-event-collector/config.yaml"
CONFIG_HOST = "hostname"
CONFIG_USER = "username"
CONFIG_PASS = "password"
CONFIG_PORT = "port"
CONFIG_STARTTIME = "starttime"
CONFIG_PERIOD = "period"
CONFIG_STARTOFFSET = "startoffset"
CONFIG_FORMAT = "format"
CONFIG_MAILTO = "mailto"
CONFIG_MAILSERVER = "mailserver"
CONFIG_SUBJECT = "subject"
CONFIG_S3BUCKET = "s3bucket"
CONFIG_S3ENDPOINT = "s3endpoint"
CONFIG_S3ACCESSKEY = "s3accesskey"
CONFIG_S3SECRETKEY = "s3secretkey"
CONFIG_S3PREFIX = "s3prefix"

FORMAT_JSON="JSON"
FORMAT_HTML="HTML"
FORMAT_XML="XML"


class EcsEventCollector:
    def __init__(self):
        # Set up some defaults
        self.use_s3 = False
        self.use_mail = False
        self.host = None 
        self.user = None 
        self.password = None 
        self.port = 4443
        self.starttime = 60
        self.startoffset = -60
        self.period = 1440
        self.report_format = FORMAT_HTML
        self.mailto = None
        self.mailserver = None
        self.subject = None
        self.s3bucket = None
        self.s3endpoint = None
        self.s3accesskey = None
        self.s3secretkey = None
        self.s3prefix = ''

    def run(self):
        # Compute start time
        t = time(hour=0, minute=0)
        soff = timedelta(minutes=self.starttime)
        t = datetime.combine(date.today(), t) + soff

        now = datetime.now()

        soff = t - now
        if soff.total_seconds() < 0:
            # We missed the window.  Wait until the next day.
            soff = soff + timedelta(days=1)

        print "First start is in %s" % soff

        # Wait for first iteration
        sleep(soff.total_seconds())

        job = schedule.every(self.period).minutes.do(self.job)

        # Do the first run
        schedule.run_all()

        while True:
            print "Next run at %s" % job.next_run
            sleep(schedule.idle_seconds()+1)
            schedule.run_pending()

    def job(self):
        print "Job running..."

        data_format = self.report_format
        if FORMAT_HTML == self.report_format:
            # We will use XSLT to generate the report, so get the data in XML format
            data_format = FORMAT_XML

        # get local timezone
        local_tz = tzlocal.get_localzone()

        # Midnight in current TZ.
        today_ts = datetime.combine(datetime.today(), time())
        today_ts = local_tz.localize(today_ts)
        end_ts = self.format_iso_datetime(today_ts)
        start_ts = self.format_iso_datetime(today_ts - timedelta(days=1))

        print "Generating report from %s to %s" % (start_ts, end_ts)

        data = self.get_data(start_ts, end_ts, data_format)

    def format_iso_datetime(self, dt):
        dt = dt.astimezone(pytz.utc)
        formatted = dt.isoformat()
        # Make +00:00 into 'Z'
        return formatted.replace("+00:00", "Z")

    def get_data(self, start_ts, end_ts, data_format):
        session = Session()
        token = self.login(session)
        print "Got token %s" % token

        url = "https://%s:%d/vdc/events" % (self.host, self.port)
        params = {'start_time': start_ts, 'end_time': end_ts}
        headers = {"X-SDS-AUTH-TOKEN": token}
        if data_format == 'XML':
            headers['Accept'] = "application/xml"
        else:
            headers['Accept'] = "application/json"
        request = Request('GET', url, params=params, headers=headers)

        print "Request: %s" % request

        response = self.retry_request(session, request.prepare())

        print "Response: %s" % response.text

        # TODO: handle pagination for lots of events.

        try:
            self.logout(session, token)
        except Exception as e:
            # Ignore
            print "Error logging out (ignored): %s" % e.message

    def login(self, session):
        url = "https://%s:%d/login" % (self.host, self.port)
        request = Request('GET', url, auth=(self.user, self.password))
        response = self.retry_request(session, request.prepare())

        return response.headers["X-SDS-AUTH-TOKEN"]

    def retry_request(self, session, request, max_retries=3):
        while max_retries > 0:
            response = session.send(request, timeout=300, verify=False)
            if response.status_code < 299:
                return response
            else:
                print "HTTP %d: %s" % (response.status_code, response.reason)
                max_retries -= 1

        raise Exception("Failed to execute %s, max retries exceeded." % request)

    def logout(self, session, token):
        url = "https://%s:%d/logout" % (self.host, self.port)
        headers = {"X-SDS-AUTH-TOKEN": token}
        request = Request('GET', url, headers=headers)

        self.retry_request(session, request.prepare())

# Read settings -- must be mapped into /etc/ecs-event-collector/config.yaml

if not os.path.exists(CONFIG_FILE):
    raise Exception("FATAL: config file does not exist: %s" % CONFIG_FILE)

# parse as YAML file
stream = file(CONFIG_FILE, 'r')
config = yaml.load(stream)

# Check for required settings
for prop in [CONFIG_HOST, CONFIG_USER, CONFIG_PASS]:
    if not config.has_key(prop):
        raise Exception("FATAL: config missing required property %s" % prop)

# Load config
collector = EcsEventCollector()

collector.host = config[CONFIG_HOST]
collector.user = config[CONFIG_USER]
collector.password = config[CONFIG_PASS]

if CONFIG_PORT in config:
    collector.port = int(config[CONFIG_PORT])

if CONFIG_FORMAT in config:
    collector.report_format = config[CONFIG_FORMAT]
    # todo: validate enum

if CONFIG_MAILTO in config:
    # email requested
    collector.use_mail = True
    collector.mailto = config[CONFIG_MAILTO]
    if CONFIG_MAILSERVER in config:
        collector.mailserver = config[CONFIG_MAILSERVER]
    if CONFIG_SUBJECT in config:
        collector.subject = config[CONFIG_SUBJECT]

if CONFIG_S3BUCKET in config:
    # S3 upload requested
    collector.use_s3 = True
    if CONFIG_S3ACCESSKEY not in config:
        raise Exception("S3 bucket specified for upload but configuration key %s missing" % CONFIG_S3ACCESSKEY)
    collector.s3accesskey = config[CONFIG_S3ACCESSKEY]
    if CONFIG_S3SECRETKEY not in config:
        raise Exception("S3 bucket specified for upload but configuration key %s missing" % CONFIG_S3SECRETKEY)
    collector.s3secretkey = config[CONFIG_S3SECRETKEY]
    if CONFIG_S3ENDPOINT not in config:
        raise Exception("S3 bucket specified for upload but configuration key %s missing" % CONFIG_S3ENDPOINT)
    collector.s3endpoint = config[CONFIG_S3ENDPOINT]
    if CONFIG_S3PREFIX in config:
        collector.s3prefix = config[CONFIG_S3PREFIX]

if CONFIG_STARTTIME in config:
    collector.starttime = int(config[CONFIG_STARTTIME])

if CONFIG_STARTOFFSET in config:
    collector.startoffset = int(config[CONFIG_STARTOFFSET])

if CONFIG_PERIOD in config:
    collector.period = int(config[CONFIG_PERIOD])

# Make sure they at least configured one of email or S3.
if not (collector.use_s3 or collector.use_mail):
    raise Exception("You need to configure at least one destination: email or S3!")

# Go!
if len(sys.argv) > 1 and sys.argv[1] == "test":
    # Test mode... just run once and exit.
    collector.job()
else:
    collector.run()
