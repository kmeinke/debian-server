FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies and Salt repo
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    lsb-release \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://packages.broadcom.com/artifactory/api/security/keypair/SaltProjectKey/public | gpg --dearmor -o /etc/apt/keyrings/salt-archive-keyring.gpg \
    && printf 'Types: deb\nURIs: https://packages.broadcom.com/artifactory/saltproject-deb\nSuites: stable\nComponents: main\nSigned-By: /etc/apt/keyrings/salt-archive-keyring.gpg\n' > /etc/apt/sources.list.d/salt.sources \
    && apt-get update \
    && apt-get install -y salt-minion openssh-client iproute2 bash-completion systemd systemd-sysv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Masterless minion configuration
RUN mkdir -p /etc/salt/minion.d
COPY salt/minion.d/local.conf /etc/salt/minion.d/local.conf

# State and pillar mount points
RUN mkdir -p /srv/salt /srv/pillar

STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
