FROM ubuntu:latest

RUN export DEBIAN_FRONTEND=noninteractive \
 && apt-get update -y \
 && apt-get install -y --no-install-recommends openssh-server rsync

RUN mkdir /root/.ssh
RUN mkdir -p /var/run/sshd
RUN chmod 0755 /var/run/sshd
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config

RUN echo 'root:root' | chpasswd

EXPOSE 22

CMD    ["/usr/sbin/sshd", "-D"]
