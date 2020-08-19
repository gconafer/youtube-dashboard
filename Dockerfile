FROM python:3.7-slim-buster
LABEL maintainer="TEST"

ENV PYTHONUNBUFFERED 1
ENV PATH="/scripts:${PATH}"

RUN apt-get update \
  && apt-get -y install gcc postgresql \
  && apt-get clean
RUN pip install --upgrade pip

#RUN apk add build-base
#RUN apk add --update --no-cache postgresql-client jpeg-dev
#RUN apk add --update --no-cache --virtual .tmp-build-deps \
#      gcc libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev
#RUN apk add --update curl gcc g++ \
#    && rm -rf /var/cache/apk/*
#RUN apk add --no-cache --update \
#    python3 python3-dev gcc \
#    gfortran musl-dev g++ \
#    libffi-dev openssl-dev \
#    libxml2 libxml2-dev \
#    libxslt libxslt-dev \
#    libjpeg-turbo-dev zlib-dev
#RUN ln -s /usr/include/locale.h /usr/include/xlocale.h

ADD ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
#RUN apk del .tmp-build-deps

RUN mkdir /app
WORKDIR /app
COPY ./app /app
COPY ./scripts /scripts
RUN chmod +x /scripts/*

RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static
#RUN adduser -D user
#RUN chown -R user:user /vol/
#RUN chown -R user:user /app/templates
#RUN chmod -R 755 /vol/web
#USER user

CMD ["entrypoint.sh"]