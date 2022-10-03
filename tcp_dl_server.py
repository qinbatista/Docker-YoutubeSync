# -*- coding: utf-8 -*-
import asyncio
from distutils.log import Log
from logging import exception
from math import fabs
import sys
import ssl
import json
import os
from datetime import datetime
import threading
import subprocess
import time
from subprocess import Popen, PIPE
import urllib.request
import urllib.parse
from pathlib import Path
from socket import *
import datetime
import shutil
import platform


class QinServer:
    def __init__(self, host: str = "", port: int = 10005):
        self._host = host
        self._port = port
        self._tool_package = "yt-dlp"  # "youtube-dl"

        self._password = "lukseun1"
        self._exclude_files = [
            "ssl_cert",
            "tcp_dl_client.py",
            "tcp_dl_server.py",
            ".DS_Store",
        ]
        self.__folder_name_list = []
        os.system("cat  ~/.ssh/id_rsa.pub")
        os.system(
            'rsync -avz --progress -e "ssh -o stricthostkeychecking=no -p 10022" /download root@cq.qinyupeng.com:~/'
        )
        if platform.system() == "Darwin":
            os.system("git clone https://github.com/qinbatista/Config_YoutubeList.git")
            self._cache_folder = "/Users/qin/Desktop/download/deliveried"
            self._root_folder = "/Users/qin/Desktop/download"
            self.__file_path = "/Users/qin/Desktop/download/logs.txt"
            config_file = open("./Config_YoutubeList/config.json")
            self._crt = "/Users/qin/qinProject/DockerProject/05_download/mycert.crt"
            self._key = ("/Users/qin/qinProject/DockerProject/05_download/rsa_private.key")
        else:
            os.system(f"rm -rf /download/*")
            os.system("git clone git@github.com:qinbatista/Config_YoutubeList.git")
            self._cache_folder = "/download/deliveried"
            self._root_folder = "/download"
            self.__file_path = "/download/logs.txt"
            config_file = open("./Config_YoutubeList/config.json")
            self._crt = "/mycert.crt"
            self._key = "/rsa_private.key"
        self._storage_server_ip = "cq.qinyupeng.com"
        self._storage_server_port = 10022
        self._request_server_port = "10015"
        if not os.path.exists(self._root_folder):
            os.makedirs(self._root_folder)
        if not os.path.exists(self._cache_folder):
            os.makedirs(self._cache_folder)
        self.__downloading_list = []
        data = json.load(config_file)
        self.mapping_table = data
        p = subprocess.Popen(
            "python3 -m pip install --upgrade pip", universal_newlines=True, shell=True
        )
        p.wait()
        p = subprocess.Popen(
            "pip3 install " + self._tool_package + " --upgrade",
            universal_newlines=True,
            shell=True,
        )
        p.wait()

    def start_server(self):
        SERVER_ADDRESS = (self._host, self._port)
        event_loop = asyncio.get_event_loop()
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.check_hostname = False
        ssl_context.load_cert_chain(self._crt, self._key, password=self._password)
        factory = asyncio.start_server(self.__echo, *SERVER_ADDRESS, ssl=ssl_context)
        server = event_loop.run_until_complete(factory)
        # print('starting up on {} port {}'.format(*SERVER_ADDRESS))
        try:
            event_loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.close()
            event_loop.run_until_complete(server.wait_closed())
            # print('closing event loop')
            event_loop.close()

    def __thread_download(self, command):
        thread1 = threading.Thread(target=self.__command, name="t1", args=(command, ""))
        thread1.start()

    def __command(self, command, args):
        # and then check the response...
        if self.__isServerOpening(self._storage_server_ip, self._storage_server_port):
            # print("Chongqing server is opening")
            # download files
            os.chdir("/")
            if not os.path.exists(self._root_folder):
                os.makedirs(self._root_folder)
            if not os.path.exists(self._cache_folder):
                os.makedirs(self._cache_folder)

            def current_milli_time():
                return int(round(time.time() * 1000))

            task_id = str(current_milli_time())
            os.mkdir(f"{self._root_folder}/{task_id}")
            if os.path.exists(f"{self._root_folder}/{task_id}"):
                os.chdir(f"{self._root_folder}/{task_id}")
            # print("command:"+command)
            path_to_output_file_downloading = (
                f"{self._root_folder}/{task_id}/downloading_log.txt"
            )
            path_to_output_file_syncing = f"{self._root_folder}/{task_id}/sync_log.txt"
            myoutput_downloading = open(path_to_output_file_downloading, "w+")
            myoutput_syncing = open(path_to_output_file_syncing, "w+")
            p = subprocess.Popen(
                command,
                stdout=myoutput_downloading,
                stderr=myoutput_downloading,
                universal_newlines=True,
                shell=True,
            )
            p.wait()
            # print("downloaded all files, start sync files")

            p = subprocess.Popen(
                f'rsync -avz --progress -e "ssh -p {self._storage_server_port}" {self._root_folder}/{task_id} root@{self._storage_server_ip}:{self._root_folder}/ --delete',
                stdout=myoutput_syncing,
                stderr=myoutput_syncing,
                universal_newlines=True,
                shell=True,
            )
            p.wait()
            # print("synced files, start delete cache")
            if not os.path.exists(f"{self._cache_folder}/{task_id}"):
                os.makedirs(f"{self._cache_folder}/{task_id}")
            os.system(
                f"mv {self._root_folder}/{task_id}/downloading_log.txt {self._cache_folder}/{task_id}"
            )
            os.system(
                f"mv {self._root_folder}/{task_id}/sync_log.txt {self._cache_folder}/{task_id}"
            )
            os.system(f"rm -rf {self._root_folder}/{task_id}")
            print("deleted cache, done")
        else:
            print("Chongqing server is closed")
            os.system(f"rm -rf {self._root_folder}/*")

    def _video_list_monitor_thread(self):
        thread1 = threading.Thread(target=self._loop_message, name="t1", args=())
        thread1.start()

    def _loop_message(self):
        # video_list = open(f'{self.__file_path}', 'w+')
        # string = "/Video/文昭谈古论今/[1096]爆料穿幫、習近平被黑兩次：邀訪歐洲四國領導人是「假消息」；歷史差點轉向、與肯定不轉（文昭談古論今20220720第1118期）' '[ibO2Uh40_nE].mp4"
        # print(f"ssh -p {self._storage_server_port} root@cq.qinyupeng.com 'rm {string}'")
        # p = subprocess.Popen(f"ssh -p {self._storage_server_port} root@cq.qinyupeng.com 'rm {string}'",stdout=video_list, stderr=video_list,universal_newlines=True, shell=True)
        # p.wait()
        while True:
            try:
                time.sleep(1)
                for folder in self.__folder_name_list:
                    if os.path.exists(self._root_folder):
                        os.system(f"rm -rf {self._root_folder}/*")
                time.sleep(1)
                for key in self.mapping_table.keys():
                    # self.__thread_youtube_sync(f"https://www.youtube.com/playlist?list={key}")
                    self._youtube_sync_command(
                        f"https://www.youtube.com/playlist?list={key}", ""
                    )
                self.__log("Wait 1 hour ")
                time.sleep(3600)
            except Exception as error:
                self.__log("error: " + str(error))

    def __thread_youtube_sync(self, url):
        thread1 = threading.Thread(
            target=self._youtube_sync_command, name="t1", args=(url, "")
        )
        thread1.start()

    def _youtube_sync_command(self, url, args):
        try:
            if self.__isServerOpening(
                self._storage_server_ip, self._storage_server_port
            ):
                task_id = str(round(time.time() * 1000))
                video_list_id = url[url.find("list=") + len("list=") :]
                remote_folder_path = self.mapping_table[video_list_id]
                folder_name = remote_folder_path[0][
                    remote_folder_path[0].rfind("/") + 1 :
                ]
                # task_id = folder_name
                if folder_name not in self.__folder_name_list:
                    self.__folder_name_list.append(folder_name)

                # prepare all folders
                folder_path = f"{self._root_folder}/{folder_name}"
                if not os.path.exists(self._root_folder):
                    os.makedirs(self._root_folder)
                if not os.path.exists(folder_path):
                    os.mkdir(folder_path)
                if len(os.listdir(folder_path)) != 0:
                    os.system(f"rm {folder_path}/*.mp4")
                    os.system(f"rm {folder_path}/*.mp4.part")
                time.sleep(1)

                # open all files
                path_online_youtube_video_list = f"{folder_path}/online_video_list.txt"
                path_download_log = f"{folder_path}/downloading.txt"
                path_sync_log = f"{folder_path}/sync.txt"
                path_NAS_video_list = f"{folder_path}/NAS_video_list.txt"
                file_video_list = open(path_online_youtube_video_list, "w+")
                file_download_log = open(path_download_log, "w+")
                file_sync_log = open(path_sync_log, "w+")
                file_NAS_video_list = open(path_NAS_video_list, "w+")
                time.sleep(1)

                # start download video list
                os.chdir(f"{folder_path}")
                command_remote_video_list = f"ssh -p {self._storage_server_port} root@{self._storage_server_ip} 'ls {remote_folder_path[0]}'"
                p = subprocess.Popen(
                    command_remote_video_list,
                    stdout=file_NAS_video_list,
                    stderr=file_NAS_video_list,
                    universal_newlines=True,
                    shell=True,
                )
                p.wait()
                command_online_video_list = (
                    f"{self._tool_package} -j --flat-playlist {url}"
                )
                p = subprocess.Popen(
                    command_online_video_list,
                    stdout=file_video_list,
                    stderr=file_video_list,
                    universal_newlines=True,
                    shell=True,
                )
                p.wait()

                # compare files
                download_list = []
                youtube_video_id_list = []
                NAS_video_list = []
                with open(path_online_youtube_video_list, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        if self.__is_json(line):
                            line_to_json = json.loads(line)
                            youtube_video_id_list.append(line_to_json["id"])
                            download_list.append(line_to_json["id"])
                with open(path_NAS_video_list) as f:
                    NAS_video_list = f.readlines()
                isRemoteVideoListEmpty = True
                for video_id in NAS_video_list:
                    if ".mp4" in video_id:
                        isRemoteVideoListEmpty = False
                        break
                #sort nas list
                sorted_NAS_List = []
                for i in range(len(NAS_video_list)):
                    for index, video_id in enumerate(NAS_video_list):
                        if f"[{i}]" in video_id:
                            sorted_NAS_List.append(video_id)
                for video_name in sorted_NAS_List:
                    theID = video_name[video_name.find(".mp4")-11: video_name.find(".mp4")]
                    index_replicate = 0
                    for video_name in sorted_NAS_List:
                        if theID in video_name:
                            index_replicate += 1
                            if(index_replicate >= 2):
                                sorted_NAS_List.remove(video_name)
                                # os.system(f"ssh -p {self._storage_server_port} root@{self._storage_server_ip} 'rm {remote_folder_path[0]}/{video_name}'")
                                break

                if isRemoteVideoListEmpty:
                    return
                for video_id in NAS_video_list:
                    for youtube_video_id in download_list:
                        if youtube_video_id in video_id:
                            download_list.remove(youtube_video_id)

                for download_index,video_id in enumerate(download_list):
                    download_youtube_video_command = f"{self._tool_package} -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio' --merge-output-format mp4 https://www.youtube.com/watch?v={video_id}"
                    p = subprocess.Popen(

                        download_youtube_video_command,
                        stdout=file_download_log,
                        stderr=file_download_log,
                        universal_newlines=True,
                        shell=True,
                    )
                    p.wait()


                    cache_video = os.listdir(folder_path)
                    # for index, i in enumerate(range(len(string_list))):
                    # destination_folder = string_list[index].replace(task_id, "")
                    find_video_in_NAS = False
                    for item in cache_video:
                        if item.endswith(".mp4"):
                            for index, line in enumerate(sorted_NAS_List):
                                if video_id in line:
                                    find_video_in_NAS = True
                            if find_video_in_NAS:
                                return
                            if os.path.exists(f"{folder_path}/{item}"):
                                os.rename(
                                    f"{folder_path}/{item}",
                                    f"{folder_path}/[{download_index+len(sorted_NAS_List)}]{item}",
                                )


                            p = subprocess.Popen(
                                f'rsync -avz -I --progress -e "ssh -p {self._storage_server_port}" {folder_path} root@{self._storage_server_ip}:/Video',
                                stdout=file_sync_log,
                                stderr=file_sync_log,
                                universal_newlines=True,
                                shell=True,
                            )


                            p.wait()
                            time.sleep(1)
                            if os.path.exists(f"{folder_path}/[{download_index+len(sorted_NAS_List)}]{item}"):
                                os.remove(f"{folder_path}/[{download_index+len(sorted_NAS_List)}]{item}")
                            self.__log(f"[Sent]{folder_path}/[{download_index+len(sorted_NAS_List)}]{item}")

        except Exception as error:
            self.__log("error: " + str(error))

    def __parse_message(self, msg):
        my_json = json.loads(msg)
        return my_json["message"], my_json["type"], my_json["proxy"]

    def __is_json(self, myjson):
        try:
            json.loads(myjson)
        except ValueError as e:
            return False
        return True

    def __isServerOpening(self, ip, port):
        s = socket(AF_INET, SOCK_STREAM)
        try:
            s.settimeout(5)
            s.connect((ip, port))
            isConnected = True
        except Exception as error:
            time.sleep(1)
            # print(error)
            isConnected = False
        finally:
            s.close()
            return isConnected

    def __log(self, result):
        if not os.path.exists(self.__file_path):
            with open(self.__file_path, "w+") as f:
                pass
        with open(self.__file_path, "a+") as f:
            f.write(f"{result}\n")
        if os.path.getsize(self.__file_path) > 1024 * 512:
            os.remove(self.__file_path)

    async def __echo(self, reader, writer):
        address = writer.get_extra_info("peername")
        data = await reader.readuntil(b"\r\n")
        resp = data.decode().strip()
        message, msg_type, proxy = self.__parse_message(resp)
        await self.__mission_manager(message, msg_type, proxy)
        writer.write(
            b"start downloading"
            + "->".encode("utf-8")
            + message.encode("utf-8")
            + b"\r\n"
        )
        await writer.drain()

    async def __mission_manager(self, message, type, proxy):
        p = subprocess.Popen(
            "python3 -m pip install --upgrade pip", universal_newlines=True, shell=True
        )
        p.wait()
        p = subprocess.Popen(
            "pip3 install " + self._tool_package + " --upgrade",
            universal_newlines=True,
            shell=True,
        )
        p.wait()
        if proxy != "":
            proxy = "proxychains"
        if type == self._tool_package:
            self.__thread_download(
                f"{proxy} {type} -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio' --merge-output-format mp4 {message}"
            )
        elif type == "wget":
            self.__thread_download(f"{proxy} {type} {message}")
        elif type == "instagram-scraper":
            self.__thread_download(f"{proxy} {type} {message}")
        elif type == "aria2c":
            self.__thread_download(f"{proxy} {type} {message}")
        elif type == "command":
            self.__thread_download(f"{proxy} {message}")
        elif type == "youtube":
            self.__thread_download(f"{proxy} {message}")
        elif type == "sync_youtube":
            self.__thread_youtube_sync(f"{proxy} {message}")


if __name__ == "__main__":

    qs = QinServer()
    qs._video_list_monitor_thread()
    # qs.start_server()
