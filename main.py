#!/usr/local/bin/python
"""
Python script to collect daily events from ECS and mail them and/or upload
them to an S3 bucket for auditing purposes.
"""

import os
import yaml

CONFIG_FILE="/etc/ecs-event-collector/config.yaml"
CONFIG_HOST="hostname"
CONFIG_USER="username"
CONFIG_PASS="password"
CONFIG_PORT="port"
CONFIG_STARTTIME="starttime"
CONFIG_PERIOD="period"
CONFIG_STARTOFFSET="startoffset"
CONFIG_FORMAT="format"
CONFIG_MAILTO="mailto"
CONFIG_MAILSERVER="mailserver"
CONFIG_SUBJECT="subject"
CONFIG_S3BUCKET="s3bucket"
CONFIG_S3ENDPOINT="s3endpoint"
CONFIG_S3ACCESSKEY="s3accesskey"
CONFIG_S3SECRETKEY="s3secretkey"
CONFIG_S3PREFIX="s3prefix"

FORMAT_JSON="JSON"
FORMAT_HTML="HTML"
FORMAT_XML="XML"

class EcsEventCollector:
    def __init__(self):
        # Set up some defaults
        self.use_s3 = False
        self.use_mail = False
        self.host = ''
        self.user = ''
        self.password = ''
        self.port = 4443
        self.starttime

print "Hello World!"

# Read settings -- must be mapped into /etc/ecs-event-collector/config.yaml

if not os.path.exists(CONFIG_FILE):
    print "FATAL: config file does not exist: %s" % CONFIG_FILE
    exit(1)

# parse as YAML file
stream = file(CONFIG_FILE, 'r')
config = yaml.load(stream)

# Check for required settings
for prop in [CONFIG_HOST, CONFIG_USER, CONFIG_PASS]:
    if not hasattr(config, prop):
        print "FATAL: config missing required property %s" % prop
        exit(2)



