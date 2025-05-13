# To build image for this dockerfile use this command:
#   docker build -t terrabrasilis/general-fires-data-task:vx.y -f docker-env/Dockerfile --no-cache .
#
# To run without compose and without shell terminal use this command:
#   docker run -d --rm --name terrabrasilis_fires_scripts terrabrasilis/general-fires-data-task:vx.y
#   docker run -d --rm --name terrabrasilis_fires_scripts -v $PWD:/logs -v $PWD:/data/files terrabrasilis/general-fires-data-task:vx.y
#
#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM ubuntu:20.04

LABEL "br.inpe.dpi"="INPE/DPI-TerraBrasilis" \
br.inpe.dpi.terrabrasilis="script-tasks" \
author="Andre Carvalho" \
author.email="andre.carvalho@inpe.br" \
description="Scripts for daily get data of fire focuses."
#-------------Application Specific Stuff ----------------------------------------------------

RUN apt-get -o Acquire::ForceIPv4=true update \
    && DEBIAN_FRONTEND=noninteractive \
    TZ=America/Sao_Paulo \
    apt-get install -y \
    cron \
    python3-pip \
    postgis \
    zip \
    && rm -rf /var/lib/apt/lists/*

# define the timezone to run cron
ENV TZ=America/Sao_Paulo
# define the install path env var
ENV INSTALL_PATH /usr/local
# the data directory for put generated files 
ENV SHARED_DIR $INSTALL_PATH/data
# the scripts directory
ENV SCRIPT_DIR $INSTALL_PATH/src

# used inside container to read the config files from default location
# /usr/local/data/config
ENV DOCKER_ENV True

# create directories
RUN mkdir -p ${SHARED_DIR} \
    && mkdir -p ${SCRIPT_DIR}

# Install environment scripts
# ------------------------------------------------------
ADD docker-env/exec_daily.sh $INSTALL_PATH/
ADD docker-env/daily.cron /etc/cron.d/daily-cron
ADD docker-env/docker-entrypoint.sh $INSTALL_PATH/bin/docker-entrypoint.sh
ADD docker-env/requirements.txt $INSTALL_PATH/
RUN pip3 install -r $INSTALL_PATH/requirements.txt

# Install main scripts
# ------------------------------------------------------
COPY src/ $SCRIPT_DIR/
RUN chmod +x $SCRIPT_DIR/*.sh \
    && chmod +x $INSTALL_PATH/*.sh \
    && chmod 0644 /etc/cron.d/daily-cron \
    && crontab -l | { cat; cat /etc/cron.d/daily-cron; } | crontab - \
    && chmod +x $INSTALL_PATH/bin/*.sh \
    && ln -s usr/local/bin/docker-entrypoint.sh / # backwards compat

# expose shared dir
VOLUME ["${SHARED_DIR}"]

ENTRYPOINT [ "/docker-entrypoint.sh" ]