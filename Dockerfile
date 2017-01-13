FROM python:3.5
MAINTAINER Mike Graves <mgraves@mit.edu>

COPY minecart /minecart/mincart
COPY requirements.* /minecart/
COPY LICENSE /minecart/
COPY setup.* /minecart/

RUN python3.5 -m pip install -r /minecart/requirements.txt
RUN python3.5 -m pip install /minecart/

ENTRYPOINT ["minecart"]
CMD ["--help"]
