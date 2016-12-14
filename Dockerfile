FROM python:2-alpine

RUN pip install ecscli

ADD main.py /main/

CMD ["/usr/local/bin/python", "/main/main.py"]

