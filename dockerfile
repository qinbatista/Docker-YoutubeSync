FROM debian:10-slim
ADD * ./

RUN apt-get update
RUN apt-get -y install ffmpeg python3 rsync python3-distutils sudo git tar build-essential ssh aria2 screen  make gcc  vim wget curl proxychains locales

#for download git repostory
RUN apt-get -y install git ssh
RUN mkdir ~/.ssh/
RUN touch ~/.ssh/authorized_keys
RUN touch ~/.ssh/known_hosts
RUN ssh-keyscan -t rsa github.com > ~/.ssh/known_hosts
RUN mv ./id_rsa ~/.ssh/
RUN mv ./id_rsa.pub ~/.ssh/
RUN chmod 600 ~/.ssh/id_rsa

VOLUME [ "/download"]
WORKDIR /

EXPOSE 10005
CMD ["python3","/tcp_dl_server.py"]
