FROM ubuntu:latest

RUN export DEBIAN_FRONTEND=noninteractive \
 && apt-get update -y \
 && apt-get install -y --no-install-recommends openssh-server

RUN mkdir /root/.ssh
RUN mkdir -p /var/run/sshd
RUN chmod 0755 /var/run/sshd

EXPOSE 22

CMD    ["/usr/sbin/sshd", "-D"]
