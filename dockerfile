FROM debian
ADD * ./
COPY libsodium-1.0.10.tar.gz ./libsodium-1.0.10.tar.gz

RUN apt-get update
RUN apt-get -y install ffmpeg python3 rsync python3-distutils sudo git tar build-essential ssh aria2 screen ssh make gcc sudo vim wget curl proxychains locales

#for download git repostory
RUN apt-get -y install git ssh
RUN mkdir ~/.ssh/
RUN touch ~/.ssh/authorized_keys
RUN touch ~/.ssh/known_hosts
RUN ssh-keyscan -t rsa github.com > ~/.ssh/known_hosts
RUN mv ./id_rsa ~/.ssh/
RUN mv ./id_rsa.pub ~/.ssh/
RUN chmod 600 ~/.ssh/id_rsa
# RUN git clone git@github.com:qinbatista/Config_YoutubeList.git
# RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
# RUN chmod a+rx /usr/local/bin/yt-dlp
#install youtube-dl
RUN python3 get-pip.py
RUN pip3 install youtube-dl instagram-scraper pytz

#echo yourpublickey>>~/.ssh/authorized_keys
#install ssr
RUN chmod +x ./ssr
RUN mv ./ssr /usr/local/sbin/
# RUN ssr install
#set config
COPY config.json /root/.local/share/shadowsocksr/config.json
COPY sshd_config /root/ssh/sshd_config
COPY proxychains.conf /etc/proxychains.conf
#build libsodium-1.0.10
RUN tar xzvf ./libsodium-1.0.10.tar.gz
RUN ./libsodium-1.0.10/configure
RUN make -j8 && make install
RUN echo /usr/local/lib > /etc/ld.so.conf.d/usr_local_lib.conf
RUN ldconfig
RUN chmod 600 ~/.ssh/id_rsa
#set for aria2
RUN mkdir ~/.aria2
RUN touch ~/.aria2/aria2.sessions
RUN touch ~/.aria2/aria2.log
RUN mv ./aria2.conf ~/.aria2/aria2.conf
RUN ls
VOLUME [ "/download"]
WORKDIR /
EXPOSE 10005
CMD ["python3","/tcp_dl_server.py"]
