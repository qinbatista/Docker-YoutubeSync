FROM debian:10-slim
ADD * ./

ARG aws_key
ARG aws_secret

ARG rsa
ARG rsa_public

RUN apt-get update
RUN apt-get -y install ffmpeg python3 python3-pip unzip rsync python3-distutils sudo git tar build-essential ssh aria2 screen  make gcc  vim wget curl proxychains locales

#write RSA key
RUN touch id_rsa
RUN echo -----BEGIN OPENSSH PRIVATE KEY----- >> id_rsa
RUN echo ${rsa} >> id_rsa
RUN echo -----END OPENSSH PRIVATE KEY----- >> id_rsa
RUN echo ${rsa_public} > id_rsa.pub


#for config NAS
RUN mkdir ~/.ssh/
RUN touch ~/.ssh/authorized_keys
RUN touch ~/.ssh/known_hosts
RUN mv ./id_rsa ~/.ssh/
RUN mv ./id_rsa.pub ~/.ssh/
RUN chmod 600 ~/.ssh/id_rsa
# config github download
RUN ssh-keyscan -t rsa github.com > ~/.ssh/known_hosts

#install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install
RUN aws configure set aws_access_key_id ${aws_key}
RUN aws configure set aws_secret_access_key ${aws_secret}
RUN aws configure set default.region us-west-2
RUN aws configure set region us-west-2 --profile testing

#write aws key to file
RUN echo ${aws_key} > aws_key.txt
RUN echo ${aws_secret} > aws_secret.txt



VOLUME [ "/download"]
WORKDIR /

EXPOSE 10005
CMD ["python3","/YoutubeSync.py"]
