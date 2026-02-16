FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive

# Install minimal packages for salt-ssh target
RUN apt-get update && apt-get install -y \
    openssh-server \
    python3 \
    iproute2 \
    bash-completion \
    systemd \
    systemd-sysv \
    sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure sshd
RUN mkdir -p /run/sshd

# Bootstrap admin user for salt-ssh access
RUN useradd -m -s /bin/bash -G sudo admin \
    && passwd -l admin \
    && mkdir -p /home/admin/.ssh \
    && echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFVU9t1TkiOP9hbOSBe4SY+Itw/ChNqRXHb1HT2OcIwX admin' > /home/admin/.ssh/authorized_keys \
    && chmod 700 /home/admin/.ssh \
    && chmod 600 /home/admin/.ssh/authorized_keys \
    && chown -R admin:admin /home/admin/.ssh

# NOPASSWD sudo for admin (salt-ssh needs this)
RUN echo 'admin ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/admin \
    && chmod 440 /etc/sudoers.d/admin

EXPOSE 22

STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
