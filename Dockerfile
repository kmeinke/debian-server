FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies and Salt repo
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    lsb-release \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://packages.broadcom.com/artifactory/api/security/keypair/SaltProjectKey/public | gpg --dearmor -o /etc/apt/keyrings/salt-archive-keyring.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/salt-archive-keyring.gpg] https://packages.broadcom.com/artifactory/saltproject-deb stable main" > /etc/apt/sources.list.d/salt.list \
    && apt-get update \
    && apt-get install -y salt-minion \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Masterless minion configuration
RUN mkdir -p /etc/salt/minion.d
COPY salt/minion.d/local.conf /etc/salt/minion.d/local.conf

# State and pillar mount points
RUN mkdir -p /srv/salt /srv/pillar

CMD ["salt-call", "--local", "state.highstate", "test=True"]
