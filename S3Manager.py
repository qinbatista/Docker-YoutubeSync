# -*- coding: utf-8 -*-
import subprocess
import uuid
import os
import json
import platform

class S3Manager:
    def __init__(self):
        if platform.system() == "Darwin":
            self.__file_path = "/Users/qin/Desktop/logs.txt"
            self.__fn_stdout = (
                f"/Users/qin/Desktop/_get_static_ip_stdout{uuid.uuid4()}.json"
            )
            self.__fn_tderr = (
                f"/Users/qin/Desktop/_get_static_ip_stderr{uuid.uuid4()}.json"
            )
        else:
            self.__file_path = "/root/logs.txt"
            self.__fn_stdout = f"./_get_static_ip_stdout{uuid.uuid4()}.json"
            self.__fn_tderr = f"./_get_static_ip_stderr{uuid.uuid4()}.json"
        self.__cluster = "arn:aws:ecs:us-west-2:825807444916:cluster/SSRCluster"
        self.__service = "arn:aws:ecs:us-west-2:825807444916:service/SSRCluster/SSR-Service"
        self.__task_definition = "SSRFargate"
    def __log(self, result):
        if os.path.isfile(self.__file_path) == False:
            return
        with open(self.__file_path, "a+") as f:
            f.write(f"{str(result)}\n")
        if os.path.getsize(self.__file_path) > 1024 * 512:
            with open(self.__file_path, "r") as f:
                content = f.readlines()
                os.remove(self.__file_path)

    def __exec_aws_command(self, command):
        self.__get_static_ip_stdout = open(self.__fn_stdout, "w+")
        self.__get_static_ip_stderr = open(self.__fn_tderr, "w+")
        process = subprocess.Popen(
            command,
            stdout=self.__get_static_ip_stdout,
            stderr=self.__get_static_ip_stderr,
            universal_newlines=True,
            shell=True,
        )
        process.wait()

        aws_result = ""
        filesize = os.path.getsize(self.__fn_tderr)
        if filesize == 0:
            with open(self.__fn_stdout) as json_file:
                aws_result = json_file.readlines()
        else:
            with open(self.__fn_tderr) as json_file:
                aws_result = json_file.read()
        # clean cache files
        os.remove(self.__fn_stdout)
        os.remove(self.__fn_tderr)
        # print(aws_result)
        self.__log(aws_result)
        return aws_result

    def _sync_folder(self,source, _folder_name):
        cli_command = f'aws s3 cp {source} s3://qinyupeng.com/Videos/{_folder_name} --recursive --exclude "*" --include "*.mp4"'
        result = self.__exec_aws_command(cli_command)
        try:
            if "upload" in result:  # type: ignore
                self.__log(f"[_sync_folder] success")
                return True
        except Exception as e:
            self.__log(f"[_sync_folder] failed:" + str(e))
            return False



if __name__ == "__main__":
    ss = S3Manager()
    ss._sync_folder("/Users/qin/Desktop/download/文昭思绪飞扬","/文昭思绪飞扬")
