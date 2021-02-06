# Use an official Python runtime as a parent image
FROM python:3.9.1-buster
RUN apt-get update && apt-get install -y \
    gosu \
 && rm -rf /var/lib/apt/lists/*

# Set the working directory to /opt/application
WORKDIR /opt/application

# create application user
RUN useradd --create-home application

RUN chown -R application /opt/application
RUN mkdir /opt/rundir
RUN chown -R application /opt/rundir
RUN mkdir /opt/venv
RUN chown -R application /opt/venv
# Copy the current directory contents into the container at /opt/application
COPY requirements-docs.txt /tmp/requirements-docs.txt

# change to non-root user
USER application

RUN python -m venv /opt/venv
# Install any needed packages specified in requirements.txt
RUN /opt/venv/bin/pip install --upgrade pip==21.0.1 setuptools
RUN /opt/venv/bin/pip install --disable-pip-version-check --trusted-host pypi.python.org -r /tmp/requirements-docs.txt --no-cache-dir
# make application scripts visible
ENV PATH /opt/venv/bin:$PATH
# expose build tag to application
ARG TAG
ENV TAG=$TAG
# Copy the current directory contents into the container at /opt/application
COPY --chown=application . /opt/application
USER application
# install the app
# https://thekev.in/blog/2016-11-18-python-in-docker/index.html
# https://jbhannah.net/articles/python-docker-disappearing-egg-info
ENV PYTHONPATH=/opt/application:
RUN cd /opt/application; /opt/venv/bin/pip install -e .[test,lint]
# Make port 6543 available to the world outside this container
VOLUME /opt/application
VOLUME /opt/rundir
USER root
COPY docker/docker-entrypoint.sh /opt/docker-entrypoint.sh
COPY docker/entrypoint.d /opt/entrypoint.d
WORKDIR /opt/rundir
ENTRYPOINT ["/opt/docker-entrypoint.sh"]
# Run application when the container launches
CMD ["echo", "No command"]
