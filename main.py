import concurrent.futures
import multiprocessing
import time

import paramiko
import sys
import pathlib
import glob
import re
from alive_progress import alive_bar


def sourcefileListGeneration(sourcepath):
    files = [str(f) for f in pathlib.Path(sourcepath).iterdir() if
             (f.is_file() and ('mkv' in str(f) or 'mp4' in str(f)))]

    return files


def seasonCalculator(sourceFileList, parentDir):
    seasons = []

    for sourcePath in sourceFileList:
        if re.search('S\d\d', sourcePath) is not None:
            seasons.append(re.search('S\d\d', sourcePath)[0])

    seasons = set(seasons)

    return seasons



def createFolder(host, port, username, password, showname, parentDir, seasons):
    transport_CreateFolder = paramiko.Transport((host, port))

    transport_CreateFolder.connect(username=username, password=password)

    sftp_Create_Folder = paramiko.SFTPClient.from_transport(transport_CreateFolder)

    if showname not in sftp_Create_Folder.listdir(f"{parentDir}"):
        sftp_Create_Folder.mkdir(f"{parentDir}/{showname}")

    if seasons:
        for i in seasons:
            if i not in sftp_Create_Folder.listdir(f"{parentDir}/{showname}"):
                sftp_Create_Folder.mkdir(f"{parentDir}/{showname}/{i}")

    sftp_Create_Folder.close()
    transport_CreateFolder.close()
    print('Folder creation done.')

def printTotals(transferred, toBeTransferred):
    with alive_bar(toBeTransferred) as bar:
        print(transferred)
        bar()


def uploadFile(host, port, username, password, sourceFile, parentDir, showname):
    ext = sourceFile.split('.')[-1]
    if re.search('S\d\d', sourceFile) is not None:
        season = re.search('S\d\d', sourceFile)[0]
        episode = re.search('S\d\dE\d\d', sourceFile)[0]

        targetPath = f"{parentDir}/{showname}/{season}/{showname}.{episode}.{ext}"
    else:
        targetPath = f"{parentDir}/{showname}/{showname}.{ext}"

    transport_UploadFile = paramiko.Transport((host, port))

    transport_UploadFile.connect(username=username, password=password)

    sftp = paramiko.SFTPClient.from_transport(transport_UploadFile)

    #sftp.put(sourceFile, targetPath)
    sftp.put(sourceFile, targetPath,callback=printTotals)

    sftp.close()
    transport_UploadFile.close()


def print_hi():
    host = "1xxxxx"  # hard-coded
    port = 22
    password = "xxx"  # hard-coded
    username = "xxx"  # hard-coded

    parentDirMov = "/mnt/media/Movies"  # parent dir on my server
    parentDirTV = "/mnt/media/TV"  # parent dir on my server
    parentDir=parentDirTV
    showname = 'Billions'
    sourcepath = r'C:\Users\jhg\Downloads\Billions'  # source file dir on my PC

    sourceFileList = sourcefileListGeneration(sourcepath)

    seasons = seasonCalculator(sourceFileList, parentDir)

    createFolder(host, port, username, password, showname, parentDir, seasons)
    
    start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for sourceFile in sourceFileList:
            futures.append(executor.submit(uploadFile, host=host, port=port, username=username, password=password,
                                           sourceFile=sourceFile, parentDir=parentDir, showname=showname))
        for future in concurrent.futures.as_completed(futures):
            print(future.result())
    end = time.time()

    print(end - start)


if __name__ == '__main__':
    print_hi()

