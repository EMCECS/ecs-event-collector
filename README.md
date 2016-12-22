# Description
This project contains a Python script that will run periodically to fetch ECS audit events and email and/or upload them to S3.  By default it will generate a report at 1:00am every day in the local time zone.  Thus, *it's important that the local linux system be in the timezone you would like to generate the report!*

# Configuration
The application reads its configuration information from /etc/ecs-event-collector/config.yaml.  This is a standard YAML formatted file that contains the following properties.

## Required
The following properties are required:

* hostname: the IP address or hostname of a ECS node or load balancer to connect to and access the management API
* username: the username to run the commands as.  Should be a "System Monitor" user.
* password: the password for the user.  On first execution, the password will be obfuscated and written back to the file so it's not in plain text.

## Optional
The following properties are optional:

* port: The port to connect to for accessing the management APIs.  Defaults to 4443.
* starttime: the offset from midnight in the local timezone to run in minutes.  Defaults to 60 (i.e. run at 1:00am local time)
* period: the period in minutes to generate the report for.  Defaults to 1440 (1 day)
* startoffset: the report generation time offset from starttime.  Defaults to -60 (i.e. report will generate from midnight yesterday to midnight today).
* format: The output format: JSON, XML, or HTML.  Defaults to HTML.
* mailto: If specified, a YAML array of email addresses to send the report to.
* mailserver: If specified, the mail server to use for sending email.  Defaults to localhost.
* subject: If specified, the subject of the email.  Defaults to `ECS Audit Event Report for yyyy-MM-dd`.
* s3bucket: If specified, upload the report to the given S3 bucket.
* s3endpoint: The S3 endpoint to connect to. 
* s3accesskey: The S3 access key (user)
* s3secretkey: The S3 secret key.  On first execution, the secret key will be obfuscated and written back to the file so it's not in plain text.
* s3prefix: If specified, the prefix in the bucket to upload the reports to.

# Building

# Running
The preferred method is to execute the application as a docker container.  However, it may also be run locally.
## Docker
To execute the application as a Docker container, first create the config file.  When you launch the container, you will then map the parent directory into the docker container as a virtual volume, e.g.

```
# vi /root/ecs-event-collector/config.yaml
# docker run -d emccorp/ecs-event-collector -v /root/ecs-event-collector:/etc/ecs-event-collector:rw 
```
## Locally
```
# mkdir /etc/ecs-event-collector
# vi /root/ecs-event-collector/config.yaml
# nohup python main.py &
```

# Sample configuration

