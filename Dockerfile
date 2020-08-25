FROM python:3.7-slim-buster
LABEL maintainer="TEST"

ENV PYTHONUNBUFFERED 1
ENV PATH="/scripts:${PATH}"

RUN apt-get update \
  && apt-get -y install gcc postgresql \
  && apt-get clean
RUN pip install --upgrade pip

ADD ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN mkdir /app
WORKDIR /app
COPY ./app /app
COPY ./scripts /scripts
RUN chmod +x /scripts/*

RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static

CMD ["entrypoint.sh"]