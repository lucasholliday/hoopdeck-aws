FROM python:3.12-alpine

# Install required system dependencies for matplotlib
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    python3-dev \
    freetype-dev \
    libpng-dev \
    jpeg-dev \
    zlib-dev

# Add bash and set up a non-root user
RUN apk add --no-cache bash
RUN echo "export HISTFILE=/dev/null" >> /etc/profile
RUN adduser -S user -G users -D

# Upgrade pip and install required Python packages
RUN pip3 install --upgrade pip
RUN pip3 install requests jsons matplotlib numpy pandas scipy

# -------------------------------------------------------

# FROM python:3.12.4-alpine3.20
# #
# # add bash to alpine Linux:
# #
# RUN apk update && apk upgrade
# RUN apk add --no-cache bash

# #
# # turn off history file creation:
# #
# RUN echo "export HISTFILE=/dev/null" >> /etc/profile
# #
# # add a user (with no pwd) so we don't run as root:
# #
# RUN adduser -S user -G users -D
# #
# # install any additional python packages we need:
# #
# RUN pip3 install requests
# RUN pip3 install jsons
# RUN pip3 install matplotlib

