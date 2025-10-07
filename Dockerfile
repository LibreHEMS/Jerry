FROM registry.access.redhat.com/ubi9/ubi:latest AS base


ENV container=oci
ENV USER=default

USER root

# Check for package update
RUN dnf -y update-minimal --security --sec-severity=Important --sec-severity=Critical && \
    # Install git, nano 
    dnf install unzip nano git -y; \
    # clear cache
    dnf clean all



# Dev target
FROM base AS dev
COPY .devcontainer/devtools.sh /tmp/devtools.sh
RUN  /tmp/devtools.sh
USER default

# install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh


# DEPLOYMENT EXAMPLE:
#-----------------------------

# Prod target
FROM base

## Make App folder, copy project into container
WORKDIR /app
## REPLACE: replace this COPY statement with project specific files/folders
COPY . . 

## Run Jerry
USER default
CMD [ "uv run main.py" ]