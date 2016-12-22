#!/usr/local/bin/python
"""
Python script to collect daily events from ECS and mail them and/or upload
them to an S3 bucket for auditing purposes.
"""

import os
import yaml
import schedule
import ecscli
from datetime import datetime, time, timedelta, date
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



print "Hello World!"

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
collector.run()
