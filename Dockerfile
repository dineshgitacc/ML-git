FROM ubuntu:20.04

MAINTAINER Vinoth Vetrivel <vinoth.vetrivel@iopex.com>

# Application env variables
ENV ACCESS_TOKEN_URL localhost
ENV CLASSIFICATION_URL http://textclassification/api/
ENV CLIENT_ID 1
ENV PROJECT_ID 1
ENV UNSUPERVISED_CLASSIFICATION_URL http://bertclassification:8000/cluster_classifier/
ENV APP_URL http://nlp.iopex.com:8007
ENV BERT_UNSUPERVISED_CALLBACK_URL http://nlp.iopex.com:8007/analysis/cluster/classification/callback/
ENV DEFAULT_UNSUPERVISED_MODEL media/8bf940da-d1c9-40a5-9a43-f3a7e953ceed/model
ENV INTENT_CLASSIFICATION_SERVER http://bertintent:8000/
ENV BERT_INTENT_CALLBACK_URL http://nlp.iopex.com:8007/analysis/bert/intent/callback/
ENV HIERARCHICAL_CLUSTERING_URL http://hierarchical_clustering:8000/cluster_classifier/
ENV HIERARCHICAL_CLUSTERING_CALLBACK_URL http://nlp.iopex.com:8007/analysis/hierarchical_clustering/callback/
# Add a new user "iopex" with user id 3333
RUN useradd -ms /bin/bash -u 3333 iopex

# Install dependencies
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    vim \
    wget \
    curl \
    python3 \
    python3-dev \
    python3-pip \
    libmysqlclient-dev \
    libleptonica-dev \
    python3-unidecode \
    language-pack-en \
    nginx \
    python3-setuptools python3-opencv poppler-utils libssl-dev \
    python python-dev supervisor \
    gnupg2 \
    cron

WORKDIR /var/opt

ADD ./requirements.txt /var/opt/

RUN python3 -m pip install --upgrade pip && pip install -r requirements.txt

RUN rm -rf /var/opt/requirements.txt

# Change to non-root privilege
# USER iopex

ADD ./ /var/opt/

RUN rm -rf  logger

#RUN mkdir media

RUN mkdir logger

#RUN mv -f /var/opt/classification/settings.py.dist /var/opt/classification/settings.py

RUN export LC_ALL="en_US.UTF-8"

RUN export PYTHONIOENCODING=utf8

RUN mkdir -p /etc/uwsgi/sites

RUN mkdir /etc/uwsgi/vassals

RUN ln -s /var/opt/classification.ini /etc/uwsgi/vassals/

RUN mv -f /var/opt/nginx/default /etc/nginx/sites-available/

RUN echo "daemon off;" >> /etc/nginx/nginx.conf

# Change to executeable mode
RUN chmod a+x /var/opt/start.sh
RUN chmod a+x /var/opt/background.sh

# Add cron file
COPY classification-cron /etc/cron.d/classification-cron

EXPOSE 80

HEALTHCHECK CMD (pgrep -f nginx | pgrep -f background.sh) || exit 1

ENTRYPOINT ["./start.sh"]
