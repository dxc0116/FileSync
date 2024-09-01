# Copyright 2024-2044 by Shenghao Zheng All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Shenghao Zheng
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# SHENGHAO ZHENG DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, 
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. 
# IN NO EVENT SHALL SHENGHAO ZHENG BE LIABLE FOR ANY SPECIAL, 
# INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING 
# FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, 
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH
# THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
File sync package write by python.

Copyright (C) 2024-2024 Shenghao Zheng. All Rights Reserved.

"""

import socket
import os
import time
import logging
import inspect
import configparser


class FileSync():
    """This class provides the funtions of file sync.

    Functions:

    connect() -- creat a socket connect.
    getConfig() -- get config from file which name is config.ini.
    setConfig() -- set config to file which name is config.ini.

    String constants:
    CM_FETCH_DIR -- command of fetch directory information.
    CM_FETCH_FILE -- command of fetch file information.
    CM_FETCH_NAME -- command of fetch file name.
    CM_FETCH_TIME -- command of fetch last sync time.
    CM_PUSH_DIR -- command of push directory.
    CM_PUSH_FILE -- command of push file.
    CM_SEND_OVER -- command of send over.
    CM_SYNC_OVER -- command of sync over.
    """

    # customize comand string of socket transform
    CM_FETCH_DIR = "<-fetch_info->".encode()
    CM_FETCH_FILE = "<-fetch_file->".encode()
    CM_FETCH_NAME = "<-fetch_name->".encode()
    CM_FETCH_TIME = "<-fetch_time->".encode()
    CM_PUSH_DIR = "<-push_dir->".encode()
    CM_PUSH_FILE = "<-push_file->".encode()
    CM_SEND_OVER = "<-send_over->".encode()
    CM_SYNC_OVER = "<-sync_over->".encode()
    

    def __init__(self):
        """Init the class of FileSync."""

        self.synctime = self.readconfig("time", "synctime")
        self.localpath = self.readconfig("folder", "local")
        self.remotepath = self.readconfig("folder", "remote")
        self.clientip = self.readconfig("host","client")
        self.serverip = self.readconfig("host","server")
        self.port = int(self.readconfig("host","port"))
        self.needsync = self.readconfig("status","needsync")  #to determine whether sync service need to start.
        self.logger = self._getLogger()

    
    def _getLogger(self):
        """create running log file,return logging instance."""
        logger = logging.getLogger('[FileSync]')

        this_file = inspect.getfile(inspect.currentframe())
        dirpath = os.path.abspath(os.path.dirname(this_file))
        handler = logging.FileHandler(os.path.join(dirpath, "service.log"))

        formatter = logging.Formatter('%(asctime)s %(name)-8s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        return logger
    
    def readconfig(self,section,name):
        """Read config parameters from the file which name is config.ini."""
        con = configparser.ConfigParser()
        con.read("config.ini", encoding="utf-8")
        return con.get(section,name)


    def setconfig(self,section,name,value):
        """Write config parameters to the file which name is config.ini."""
        con = configparser.ConfigParser()
        con.read("config.ini", encoding="utf-8")    
        con.set(section, name, value)
        with open("config.ini","w",encoding="utf-8") as f:
            con.write(f)

    
    def connect(self):
        """Make a socket connect, and return connect handle."""
        con = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            con.connect((self.serverip, self.port))
            msg = "Connect" + self.serverip + "success."
            print(msg)
            self.logger.info(msg)
        except :
            msg = "Connect" + self.serverip + "failed, please check the network."
            print(msg)
            self.logger.error(msg)
            return None
        return con

    '''连接远端电脑，并获取远端文件夹信息。分为全量和增量两种模式'''
    def getRemoteFolder(self, con,remotepath,synctime=0):
        print("获取远端上次同步后变化的目录信息。")
        folderlist = []
        try:
            con.sendall(self.CM_FETCH_DIR)  # 发送全量同步需求
            while True:
                recv = con.recv(128)
                if recv == self.CM_FETCH_TIME:
                    print("接收到发送同步时间的请求的")
                    con.sendall(synctime.to_bytes(4,byteorder="little"))
                    break
            while True:
                recv = con.recv(1024)
                if recv:
                    if recv == self.CM_SEND_OVER:
                        #print("接收完成，退出接收任务")
                        break   #end sync folder list
                    else:
                        folderlist.append(recv.decode())
                        #print("接收远端目录/文件信息：",recv)
            print("共收到",len(folderlist),"条对端目录信息。")
        except Exception as e:
            print("获取远端目录失败",e.args)
        print("-"*80)
        return folderlist
    
    '''根据文件夹目录名，获取本地文件夹内的子目录和文件信息，并返回列表字符串类型的清单'''
    def getFolder(self, folder,synctime=0):
        print("获取本地上次同步后变化的目录信息。")
        folderlist = []
        for root,subs,files in os.walk(folder):
            foldersize = os.path.getsize(root)
            foldertime = int(os.path.getmtime(root))
            #print("foldertime and synctime",foldertime, synctime)
            if foldertime > synctime:
                folderinfo = root + ",d," + str(foldersize) + "," + str(foldertime)
                folderlist.append(folderinfo)
                print("添加晚于上次同步的本地目录信息：",folderinfo)
            for file in files:
                path = root + "\\" + file
                filesize = os.path.getsize(path)
                filetime = int(os.path.getmtime(path))
                if filetime > synctime:
                    fileinfo = path + ",f," + str(filesize) + "," + str(filetime)
                    folderlist.append(fileinfo)
                    print("添加晚于上次同步的本地文件信息：",fileinfo)
        print("共找到",len(folderlist),"条待同步本地目录/文件信息")
        print("-"*80)
        return folderlist
    
    '''比较两个文件夹信息的差异，并返回差异信息项，以及差异所在位置'''
    def getDiff(self,local,remote):
        diff = []
        for localinfo in local:
            localdetail = localinfo.split(",")
            localfiletime = int(localdetail[3])
            findsame = ""
            for remoteinfo in remote:
                remotedetail = remoteinfo.split(",")
                remotefiletime = int(remotedetail[3])
                #print("比较两者差异：",localinfo,remoteinfo)
                # 存在相同文件夹或文件名是进行差异判断
                if (localdetail[0] == remotedetail[0]):
                    findsame = remoteinfo   
                    # 若是文件夹，则直接退出二次循环
                    if localdetail[1] == "d":
                        findsame = remoteinfo
                        break

                    # 若是文件则根据修改时间判断差异。因电脑间存在时间差，故以3秒作为误差值。
                    #if (remotefiletime-localfiletime) > 3 :   
                    #    diff.append((remoteinfo,"new in remote"))   # 远端文件更新，添加差异

                    #if (localfiletime-remotefiletime) > 3:  
                    #    diff.append((localinfo,"new in local"))     # 本端文件更新，添加差异
                    #break

                    #第一版是以文件修改时间进行判断差异，但在实际调试过程中发现因为两台电脑之间
                    #可能因为文件的复制而照成时间差异，而引起不必要的同步，所以优化为先判断文件大小
                    #如果大小相同，再进行时间差异比较。
                    if localdetail[2] == remotedetail[2]:
                        findsame = remoteinfo
                        break
                    else:
                        if (remotefiletime-localfiletime) > 3 :   
                            diff.append((remoteinfo,"new in remote"))   # 远端文件更新，添加差异

                        if (localfiletime-remotefiletime) > 3:  
                            diff.append((localinfo,"new in local"))     # 本端文件更新，添加差异
                        
            if findsame: 
                remote.remove(findsame)  #删除相同文件名，避免重复循环查找
            else:       
                diff.append((localinfo,"only in local"))    # 远端无匹配项，添加差异
        for info in remote:
            diff.append((info,"only in remote"))  # 本端无匹配项，添加差异
        print("差异比较，共发现",len(diff),"条差异信息。")
        print("-"*80)
        return diff
    
    '''根据文件路径名获取文件，并发送到socket'''
    def sendFile(self,con,filepath):
        if os.path.exists(filepath):
            info = "Find the" + filepath +"and sending file to remote."
            self.logger.info(info)
            fp = open(filepath,'rb')
            data = fp.read()
            print(filepath,"size is" ,len(data))
            con.sendall(data)
            time.sleep(0.2) 
            self.logger.info("End file send.")
            return 0
        else:
            info = "Can't find the" + filepath +",please check file name is correct."
            return -1

    '''根据文件名接收文件，并保存到本机指定目录'''
    def recvFile(self, con, filepath):
        fileinfo = filepath.split(",")
        filename = fileinfo[0]
        filesize = int(fileinfo[2])
        info = "Receive file which name is " + filename + "size:" + str(filesize)
        self.logger.info(info)

        if os.path.exists(filename):    #若存在同名文件，则先备份
            self.bankupFile(filename)   
            self.logger.info("Bankup old file what's name is same.")

        file = open(filename,"wb")
        recvsize = 0
        while recvsize < filesize:
            if (filesize - recvsize) > 1024:
                recv = con.recv(1024)
            else:
                recv = con.recv(filesize-recvsize)
            recvsize = recvsize + len(recv)
            file.write(recv)

        self.logger.info("End receive file ")
        file.close()
        return recvsize

    '''接收目录信息，并新建目录。若成功返回0，若已经存在返回-1'''
    def recvDir(self,dir):
        if os.path.exists(dir):
            print("当前目录已存在，无需新建。",dir)
            self.logger.info("The directory is aleady exist.")
            return -1
        else:
            os.mkdir(dir)
            self.logger.info("Make new directory .")
            return 0

    '''根据目录文件名，获取远端文件，并保存到本地目录'''
    def getRemoteFile(self,con, path):
      
        filepath = path.split(",")[0]
        print("获取远端文件",path)
        type = path.split(",")[1]
        if type == "d":
            if os.path.exists(filepath):
                print("目前已存在，保留原目录名",filepath)
            else:
                print("目录不存在，创新新目录",filepath)
                os.mkdir(filepath)  # 只需创建本地目录
        else:
            print("发送请求文件命令")
            con.sendall(self.CM_FETCH_FILE)
            recv = con.recv(128)
            if recv == self.CM_FETCH_NAME:
                #print("请求更新的文件名",filepath)
                con.sendall(filepath.encode())  # 发送文件名
            #filesize = int.from_bytes(con.recv(4), byteorder="little") # 获取远端文件大小
            filesize = int(path.split(",")[2])
            #print("根据差异表获取接收文件大小:",filesize)
            
            # 将原文件改名并备份到当前目录
            if os.path.exists(filepath):
                print("存在同名文件，备份同名文件为",filepath)
                self.bankupFile(filepath)
            #file = os.path.basename(filepath)
            file = open(filepath,"wb")
            recvsize = 0
            while recvsize < filesize:
                if (filesize - recvsize) > 1024:
                    recv = con.recv(1024)
                else:
                    recv = con.recv(filesize-recvsize)
                recvsize = recvsize + len(recv)
                file.write(recv)
            file.close()
            print("接收并保存远端文件",filepath)
        return 0
    
    '''文件改名，并备份'''
    def bankupFile(self, path):
        filepath = path.split(",")[0]   #从目录夹信息中获取绝对路径文件名
        dir = os.path.dirname(filepath) #获取目录路径
        basename = os.path.basename(filepath)   # 获取带后缀的文件名
        filename = os.path.splitext(basename)   
        name = filename[0]
        ext = filename[1]
        t = time.strftime("%Y%m%d%H%M",time.localtime())
        newname = name + t + ext 
        newfilepath = os.path.join(dir,newname)
        os.rename(filepath,newfilepath)

    '''推进本地文件至对端'''
    def updateRemote(self,con, path):
        pathlist = path.split(",")
        if pathlist[1] == "d":
            print("发送本地目录至对端", pathlist[0])
            con.sendall(self.CM_PUSH_DIR)
            while True:
                recv = con.recv(128)
                if recv == self.CM_FETCH_NAME:
                    con.sendall(pathlist[0].encode())
                    return 0
                
        if pathlist[1] == "f":
            print("发送本地文件至对端", pathlist[0],end=" ")
            con.sendall(self.CM_PUSH_FILE)
            while True:
                recv = con.recv(128)
                if recv == self.CM_FETCH_NAME:
                    con.sendall(path.encode())
                    break               
            fp = open(pathlist[0],"rb")
            con.sendall(fp.read())
            print("成功。")
        return 0
    
    def sendFolder(self,con,folder,synctime=0):
        #print("发送目录文件信息至对端，共",len(folder),"条")
        for rec in folder:
            con.sendall(rec.encode())
            time.sleep(0.1)
        con.sendall(self.CM_SEND_OVER)

        print("完成目录文件信息的发送，共",len(folder),"条")

    '''同步进程，根据是否需要同步参数，启停同步过程'''
    def startSync(self):
        while self.needsync:
            print("开始两台电脑间的文件同步任务.")
            con = self.connect()           
            localfolder = []
            remotefolder = []    

            now = int(time.time())
            if self.synctime == "" : 
                lastsync = 0
                print("开启首次全量同步任务。")
            else:
                print("最近一次同步时间为：",self.synctime)
                lastsync = time.strptime(self.synctime,"%Y-%m-%d %H:%M:%S")
                lastsync = int(time.mktime(lastsync))
            print("-"*80)
            # 若当前时间大于同步时间，进行同步
            if now > lastsync:
                localfolder = self.getFolder(self.localpath,lastsync)
                
                remotefolder = self.getRemoteFolder(con,self.remotepath,lastsync)
            else:
                print("还未到计划同步时间:",self.synctime,"结束本次同步任务。")
                break

            diff = self.getDiff(localfolder,remotefolder)
                # 根据差异项获取对端新的文件进行同步
            #for i in diff:
            #    print("差异信息",i)

            if diff:
                print("开始逐条同步差异信息。")
                for i in diff:
                    #self.logger.info("差异信息逐条比对")
                    if (i[1] == "new in remote") or i[1] == "only in remote":
                        #print("发现远端新文件，获取文件",i[0])
                        self.getRemoteFile(con, i[0])
                    if (i[1] == "new in local") or (i[1] == "only in local"):
                        #print("发现本地新目录/文件，推送文件并覆盖",i[0])
                        self.updateRemote(con, i[0])
            else:
                print("自上次同步后未有文件增减，结束同步任务。")
            self.needsync = False
            setconfig("time","synctime",time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
            con.sendall(self.CM_SYNC_OVER)
            con.close()
            print("关闭远端连接，保存同步时间。")
        return 0

    '''启动服务器端的侦听和文件同步服务'''
    def startServer(self):
        server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        server.bind((self.serverip,self.port))
        server.listen(1)    # only allow one client connect
        print("启动文件同步服务，等待远端连接......")
        self.logger.info("Staring file sync service, waiting for connect.")
        # 进入自动等待连接的循环状态
        while True:
            con,addr = server.accept()
            if con:
                print("客户端",addr, "连接本级成功。")
                info = "Client(" + addr[0] + ") is connected."
                self.logger.info(info)
                while True:
                    recv = con.recv(1024)
                    print("当前接收的命令:",recv)
                    if recv == self.CM_FETCH_DIR:
                        self.logger.info("Receive comand of fetch info")
                        con.sendall(self.CM_FETCH_TIME)
                        print("发送同步时间请求")
                        while True:
                            recv = con.recv(4)
                            print("receive commd",recv)
                            synctime = int.from_bytes(recv,byteorder="little")
                            print("对端发送的同步时间",synctime)
                            folderinfo = self.getFolder(self.localpath,synctime)
                            self.sendFolder(con,folderinfo)
                            break
                        continue
                    if recv == self.CM_FETCH_FILE:
                        self.logger.info("Receive command of fetch file")
                        con.sendall(self.CM_FETCH_NAME)
                        while True:
                            filepath = con.recv(1024).decode()
                            if filepath: 
                                #print(filepath)
                                break
                        self.sendFile(con,filepath)
                        continue
                    if recv == self.CM_PUSH_FILE:
                        self.logger.info("Receive command of push file")
                        con.sendall(self.CM_FETCH_NAME)
                        while True:
                            filepath = con.recv(1024).decode()
                            print(filepath)
                            if filepath:
                                self.recvFile(con,filepath)
                                self.logger.info("get the file and save it.")
                                break
                        continue
                    if recv == self.CM_PUSH_DIR:
                        con.sendall(self.CM_FETCH_NAME)
                        while True:
                            filepath = con.recv(1024).decode()
                            if filepath:
                                self.recvDir(filepath)
                                self.logger.info("get the dir name.")
                                break
                            continue
                    if recv == self.CM_SEND_OVER:
                        continue

                    if recv == self.CM_SYNC_OVER:
                        con.close()
                        self.logger.info("end file sync,close connect,waiting for new sync.")
                        setconfig("time","synctime",time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
                        break
              
        return 0
    
if __name__ == "__main__":
    s = FileSync()
    s.startServer()



