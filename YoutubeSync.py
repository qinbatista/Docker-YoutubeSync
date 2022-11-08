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
import S3Manager


class QinServer:
    def __init__(self):
        self.__isConnected = False
        self.__downloader = "yt-dlp"  # "youtube-dl"
        self.__folder_name_list = []
        os.system("cat  ~/.ssh/id_rsa.pub")
        os.system(
            'rsync -avz --progress -e "ssh -o stricthostkeychecking=no -p 10022" /download root@cq.qinyupeng.com:~/'
        )
        if platform.system() == "Darwin":
            self._root_folder = "/Users/batista/Desktop/download"
            self.__file_path = "/Users/batista/Desktop/download/logs.txt"
        else:
            os.system(f"rm -rf /download/*")
            self._root_folder = "/download"
            self.__file_path = "/download/logs.txt"
        os.system("git clone git@github.com:qinbatista/Config_YoutubeList.git")
        config_file = open("./Config_YoutubeList/config.json")
        self.__cookie_file = "/Config_YoutubeList/youtube_cookies.txt"
        self.mapping_table = json.load(config_file)
        self._storage_server_ip = "cq.qinyupeng.com"
        self._storage_server_port = 10022
        if not os.path.exists(self._root_folder):
            os.makedirs(self._root_folder)

        p = subprocess.Popen(
            "python3 -m pip install --upgrade pip", universal_newlines=True, shell=True
        )
        p.wait()
        p = subprocess.Popen(
            "pip3 install " + self.__downloader + " --upgrade",
            universal_newlines=True,
            shell=True,
        )
        p.wait()
        self.__s3_manager = S3Manager.S3Manager()

    def _video_list_monitor_thread(self):
        thread1 = threading.Thread(target=self._loop_message, name="t1", args=())
        thread1.start()

    def _loop_message(self):
        while True:
            try:
                for folder in self.__folder_name_list:
                    if os.path.exists(self._root_folder):
                        os.system(f"rm -rf {self._root_folder}/*")
                time.sleep(1)
                for key in self.mapping_table.keys():
                    self._youtube_sync_command(
                        f"https://www.youtube.com/playlist?list={key}", ""
                    )
                self.__log("Wait 1 hour ")
                time.sleep(3600)
            except Exception as error:
                self.__log("error: " + str(error))

    def _youtube_sync_command(self, url, args):
        if self.__isServerOpening(self._storage_server_ip, self._storage_server_port):
            video_list_id = url[url.find("list=") + len("list=") :]
            remote_folder_path = self.mapping_table[video_list_id]
            folder_name = remote_folder_path[0][remote_folder_path[0].rfind("/") + 1 :]
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

            # start download video list
            os.chdir(f"{folder_path}")
            # downloaded_video_list = self.__get_video_list_from_local(f"{folder_path}/NAS_video_list.txt",remote_folder_path)
            downloaded_video_list = self.__get_video_list_from_S3(
                f"/Videos/{folder_name}/"
            )
            youtube_download_list = self.__get_video_list_from_youtube(folder_path, url)

            # if remote server is empy
            isRemoteVideoListEmpty = True
            for video_id in downloaded_video_list:
                if ".mp4" in video_id:
                    isRemoteVideoListEmpty = False
                    break
            if isRemoteVideoListEmpty:
                return

            # sort nas list and delete replicated video
            sorted_NAS_List = []
            for i in range(len(downloaded_video_list)):
                for index, video_id in enumerate(downloaded_video_list):
                    if f"[{i}]" in video_id:
                        sorted_NAS_List.append(video_id)
            for video_name in sorted_NAS_List:
                theID = video_name[
                    video_name.find(".mp4") - 11 : video_name.find(".mp4")
                ]
                index_replicate = 0
                for video_name in sorted_NAS_List:
                    if theID in video_name:
                        index_replicate += 1
                        if index_replicate >= 2:
                            sorted_NAS_List.remove(video_name)
                            # os.system(f"ssh -p {self._storage_server_port} root@{self._storage_server_ip} 'rm {remote_folder_path[0]}/{video_name}'")
                            break
            loop_list = youtube_download_list.copy()
            for video_id in downloaded_video_list:
                for youtube_video_id in loop_list:
                    if youtube_video_id in video_id:
                        # del youtube_download_list[youtube_video_id]
                        youtube_download_list.pop(youtube_video_id)

            for download_index, video_id in enumerate(youtube_download_list):
                file_download_log = open(f"{folder_path}/downloading.txt", "w+")
                download_youtube_video_command = f"{self.__downloader} -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio' --cookies {self.__cookie_file} --merge-output-format mp4 https://www.youtube.com/watch?v={video_id}"
                p = subprocess.Popen(
                    download_youtube_video_command,
                    stdout=file_download_log,
                    stderr=file_download_log,
                    universal_newlines=True,
                    shell=True,
                )
                p.wait()

                cache_video = os.listdir(folder_path)
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
                                f"{folder_path}/[{youtube_download_list[video_id]}]{item}",
                            )
                        self.__s3_manager._sync_folder(
                            folder_path, f"/Videos/{folder_name}"
                        )
                        name_list = (
                            f'rsync -avz -I --include="*.mp4" --progress -e "ssh -p {self._storage_server_port}" {folder_path}/ root@{self._storage_server_ip}:/Video/{folder_name}',
                        )
                        file_sync_log = open(f"{folder_path}/sync.txt", "w+")
                        p = subprocess.Popen(
                            name_list,
                            stdout=file_sync_log,
                            stderr=file_sync_log,
                            universal_newlines=True,
                            shell=True,
                        )
                        p.wait()

                        time.sleep(1)
                        if os.path.exists(
                            f"{folder_path}/[{youtube_download_list[video_id]}]{item}"
                        ):
                            os.remove(
                                f"{folder_path}/[{youtube_download_list[video_id]}]{item}"
                            )
                        self.__log(
                            f"[Sent]{folder_path}/[{youtube_download_list[video_id]}]{item}"
                        )

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
            self.__isConnected = True
        except Exception as error:
            time.sleep(1)
            # print(error)
            self.__isConnected = False
        finally:
            s.close()
            return self.__isConnected

    def __log(self, result):
        if not os.path.exists(self.__file_path):
            with open(self.__file_path, "w+") as f:
                pass
        with open(self.__file_path, "a+") as f:
            f.write(f"{result}\n")
        if os.path.getsize(self.__file_path) > 1024 * 512:
            os.remove(self.__file_path)

    def __get_video_list_from_local(self, path_NAS_video_list, remote_folder_path):
        file_downloaded_video_list = open(path_NAS_video_list, "w+")
        command_remote_video_list = f"ssh -p {self._storage_server_port} root@{self._storage_server_ip} 'ls {remote_folder_path[0]}'"
        p = subprocess.Popen(
            command_remote_video_list,
            stdout=file_downloaded_video_list,
            stderr=file_downloaded_video_list,
            universal_newlines=True,
            shell=True,
        )
        p.wait()
        with open(path_NAS_video_list) as f:
            return f.readlines()

    def __get_video_list_from_S3(self, folder_name):
        return self.__s3_manager._list_folder(folder_name)

    def __get_video_list_from_youtube(self, folder_path, url):
        path_youtube_video_list = f"{folder_path}/online_video_list.txt"
        file_youtube_video_list = open(path_youtube_video_list, "w+")
        command_online_video_list = f"{self.__downloader} -j --flat-playlist {url}"
        p = subprocess.Popen(
            command_online_video_list,
            stdout=file_youtube_video_list,
            stderr=file_youtube_video_list,
            universal_newlines=True,
            shell=True,
        )
        p.wait()

        youtube_index = {}
        with open(path_youtube_video_list, "r") as f:
            lines = f.readlines()
            for line in lines:
                if self.__is_json(line):
                    line_to_json = json.loads(line)
                    youtube_index.update(
                        {
                            line_to_json["id"]: line_to_json["playlist_count"]
                            - line_to_json["playlist_index"]
                            + 1
                        }
                    )
        return youtube_index


if __name__ == "__main__":
    print("v1")
    qs = QinServer()
    qs._video_list_monitor_thread()
