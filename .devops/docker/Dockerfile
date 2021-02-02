ARG version=master

FROM python:3-slim-buster
ARG version
WORKDIR /app
ENV PORT=5000
EXPOSE 5000
RUN apt-get update && apt-get install -y \
    build-essential \
    libldap2-dev \
    libsasl2-dev \
    ldap-utils
COPY ./.devops/docker/docker-entrypoint.sh  /
COPY ./.devops/docker/docker-entrypoint.d/* /docker-entrypoint.d/
COPY ./requirements.txt			    /app
RUN echo "${version}" > VERSION \
    && pip install -r requirements.txt \
COPY ./mavapa                               /app
RUN ls -laR
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD [ "gunicorn", "manage:run", "--workers=2", "--threads=4", "--worker-class=gthread", "--worker-tmp-dir", "/dev/shm", "-b", "0.0.0.0:5000", "--access-logfile=-", "--error-logfile=-" ]
