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
    CM_FETCH_DIR = "<-fetch_dir->".encode()
    CM_FETCH_PATH ="<-fetch_path->".encode()
    CM_FETCH_FILE = "<-fetch_file->".encode()
    CM_FETCH_NAME = "<-fetch_name->".encode()
    CM_FETCH_TIME = "<-fetch_time->".encode()
    CM_PUSH_DIR = "<-push_dir->".encode()
    CM_PUSH_FILE = "<-push_file->".encode()
    CM_SEND_OVER = "<-send_over->".encode()
    CM_SYNC_OVER = "<-sync_over->".encode()
    CM_READY = "<-ready->".encode()

    def __init__(self):
        """Init the class of FileSync."""

        this_file = inspect.getfile(inspect.currentframe())
        self.dirpath = os.path.abspath(os.path.dirname(this_file))

        self.synctime = self.readconfig("time", "synctime")
        self.localfolder = self.readconfig("folder", "local")
        self.remotefolder = self.readconfig("folder", "remote")
        self.clientip = self.readconfig("host","client")
        self.serverip = self.readconfig("host","server")
        self.port = int(self.readconfig("host","port"))
        self.fullsync = self.readconfig("sync","full")  
        
        self.logger = self._getLogger()


    
    def _getLogger(self):
        """create running log file,return logging instance."""

        logger = logging.getLogger('[FileSync]')

        #this_file = inspect.getfile(inspect.currentframe())
        #dirpath = os.path.abspath(os.path.dirname(this_file))
        handler = logging.FileHandler(os.path.join(self.dirpath, "synclog.log"))

        formatter = logging.Formatter('%(asctime)s %(name)-8s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        return logger
    
    def readconfig(self,section,name):
        """Read config parameters from the file which name is config.ini."""

        con = configparser.ConfigParser()
        configfile = os.path.join(self.dirpath, "config.ini")
        con.read(configfile, encoding="utf-8")
        return con.get(section,name)


    def setconfig(self,section,name,value):
        """Write config parameters to the file which name is config.ini."""

        con = configparser.ConfigParser()
        configfile = os.path.join(self.dirpath, "config.ini")
        con.read(configfile, encoding="utf-8")
        con.set(section, name, value)
        with open(configfile,"w",encoding="utf-8") as f:
            con.write(f)

    
    def connect(self):
        """Make a socket connect, and return connect handle."""

        con = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            con.connect((self.serverip, self.port))
            msg = "Connect " + self.serverip + " successly."
            print(msg)
            self.logger.info(msg)
        except :
            msg = "Connect" + self.serverip + " failed, please check the network."
            print(msg)
            self.logger.error(msg)
            return None
        return con


    def getRemoteFolder(self, con,remotepath,synctime=0):
        """Return a list of paths in remote directory."""

        msg = "Getting the paths in remote directory: " + remotepath
        print(msg)
        self.logger.info(msg)
        folderlist = []
        try:
            con.sendall(self.CM_FETCH_DIR)
            while True:
                recv = con.recv(128)
                if recv == self.CM_FETCH_PATH:
                    # note remote know about local and remote folder.
                    con.sendall((self.localfolder+","+self.remotefolder).encode())
                    break
            while True:
                recv = con.recv(128)
                if recv == self.CM_FETCH_TIME: #send last sync time
                    con.sendall(synctime.to_bytes(4,byteorder="little"))
                    break
            while True:
                recv = con.recv(1024)
                if recv:
                    if recv == self.CM_SEND_OVER:
                        msg = "End the transform. "
                        break   #end sync folder list
                    else:
                        folderlist.append(recv.decode())
            msg = "Return a list of " + str(len(folderlist)) + " paths in the remote folder " + remotepath
        except Exception as e:
            msg = "Get the remote directory failed:" + e.args[0]
        print(msg)  
        self.logger.info(msg)
        return folderlist
    

    def getFolder(self, folder,synctime=0):
        """Get details of directory on local computer,return lists of path info"""

        msg = "Getting the path lists of local directory " + folder
        print(msg)
        self.logger.info(msg)
        folderlist = []
        for root,subs,files in os.walk(folder):
            foldersize = os.path.getsize(root)
            foldertime = int(os.path.getmtime(root))
            if foldertime > synctime:
                folderinfo = root + ",d," + str(foldersize) + "," + str(foldertime)
                folderlist.append(folderinfo)
            for file in files:
                path = root + "\\" + file
                filesize = os.path.getsize(path)
                filetime = int(os.path.getmtime(path))
                if filetime > synctime:
                    fileinfo = path + ",f," + str(filesize) + "," + str(filetime)
                    folderlist.append(fileinfo)
        msg = "Return " + str(len(folderlist)) + " path info in the local folder " + folder
        print(msg)
        self.logger.info(msg)
        return folderlist
    

    def getDiff(self,local,remote):
        """Compare the difference of two directory, and return the difference items."""

        msg = "Comparing differce path between " + self.localfolder + " and " + self.remotefolder
        print(msg)
        self.logger.info(msg)
        diff = []
        for localinfo in local:
            localdetail = localinfo.split(",")
            localfiletime = int(localdetail[3])
            # get the local file name in path
            localname = localdetail[0].replace(self.localfolder,"")
            findsame = ""
            for remoteinfo in remote:
                remotedetail = remoteinfo.split(",")
                remotefiletime = int(remotedetail[3])
                # get the remote file of folder name in path
                remotename = remotedetail[0].replace(self.remotefolder,"")
                # first compare name 
                if localname == remotename:  
                    # second compare type 
                    if localdetail[1] == "d" and remotedetail[1] == "d":
                        findsame = remoteinfo
                        break   # same folder name, end compare
                    # second compare file size .
                    if localdetail[2] == remotedetail[2]:
                        # if two file have same name and size, consider them as same.
                        findsame = remoteinfo
                        break
                    # has same name but have difference ctime
                    else:
                        if (remotefiletime-localfiletime) >= 3 :   
                            diff.append((remoteinfo,"new in remote")) 
                            break 

                        if (localfiletime-remotefiletime) >= 3:  
                            diff.append((localinfo,"new in local"))
                            break    
                        
            if findsame: 
                remote.remove(findsame)  #delete same item, reduce running time.
            else:       
                diff.append((localinfo,"only in local"))    
        for info in remote:
            diff.append((info,"only in remote"))  
        msg = "Find " + str(len(diff)) + " difference path between local and remote."
        print(msg)
        self.logger.info(msg)
        return diff
    

    def sendFile(self,con,filepath):
        """Send file to remote. If not success, return -1."""

        status = 0
        if os.path.exists(filepath):
            filesize = os.path.getsize(filepath)
            with open(filepath,'rb') as f:
                while filesize > 0:
                    if filesize > 1024:
                        data = f.read(1024)
                        filesize = filesize - 1024
                    else:
                        data = f.read(filesize)
                        filesize = 0
                    con.sendall(data)
                msg = "Send file " + filepath + " to remote successly."
        else:
            msg = "Can't find file " + filepath +", please check file name is correct."
            status = -1
        print(msg)
        self.logger.info(msg)
        return status


    def recvFile(self, con, filepath):
        """Receive a file and save it to specific directory."""
        # deal the file name and size info.
        fileinfo = filepath.split(",")
        filename = fileinfo[0]
        filename = filename.replace(self.remotefolder,self.localfolder) # replace the target folder
        filesize = int(fileinfo[2])

        # if this pc has a samename file,bankup local file first.
        if os.path.exists(filename):    
            # status = self.bankupFile(filename)   
            # self.logger.info("Bankup old file what's name is same.")
            # if backup fail , save receive file as a new file name with sync.
            #if status == -1:
            filename = filename.split(".")[0] + "_sync." + filename.split(".")[-1]
        
        # receive file and save.
        #print("debug: read to receive file ", filename, " size ",filesize)
        rsize = 0
        with open(filename,"wb") as f:
            while filesize > 0:
                if filesize > 1024:
                    recv = con.recv(1024)
                    filesize = filesize - 1024
                else:
                    recv = con.recv(filesize)
                    filesize = 0
                rsize = rsize + f.write(recv)
                                  
        msg = "Receiving file " + filename + ",size:" + str(rsize)
        print(msg)
        self.logger.info(msg)
        return filesize


    def recvDir(self,dir):
        """Receive remote directory and create on local computer."""
        dir = dir.replace(self.remotefolder,self.localfolder)
        if os.path.exists(dir):
            msg = "The local computer has same directory:" + dir
            print(msg)
            self.logger.info(msg)
            return -1
        else:
            os.mkdir(dir)
            msg = "Make the new directory: " + dir
            print(msg)
            self.logger.info(msg)
            return 0


    def getRemoteFile(self,con, path):
        """Get the remote directory or file and save to local."""

        filepath = path.split(",")[0]
        msg = "Getting remote file " + filepath
        print(msg)
        self.logger.info(msg)
        # replace remote path to 
        localfp = filepath.replace(self.remotefolder,self.localfolder)
        type = path.split(",")[1]
        if type == "d": # directory
            if os.path.exists(localfp):
                msg = "Local computer has same directory " + localfp
            else:
                msg = "Create new directory:" + localfp
                os.mkdir(localfp)  
            print(msg)
            self.logger.info(msg)
            return 0
        if type == "f":   # file
            con.sendall(self.CM_FETCH_FILE)
            recv = con.recv(128)
            if recv == self.CM_FETCH_NAME:
                con.sendall(filepath.encode())  # send file name
            filesize = int(path.split(",")[2])
            
            # rename while local has same name file
    
            if os.path.exists(localfp):
                localfp = localfp.split(".")[0] + "_sync." + localfp.split(".")[-1]
                msg = "Local folder has same name file, rename as " + localfp
                print(msg)
                self.logger.info(msg)
                
            with open(localfp,"wb") as f:
                while filesize > 0:
                    recv = con.recv(1024)
                    filesize = filesize - len(recv)
                    f.write(recv)
                msg = "Receive file " + localfp + "> and save it."
                print(msg)
                self.logger.info(msg)
            return filesize
    
    def bankupFile(self, path):
        """Rename file and bankup a copy and bankup time."""

        filepath = path.split(",")[0]   
        dir = os.path.dirname(filepath) 
        if os.access(filepath,os.F_OK):
            basename = os.path.basename(filepath)   # get file name with suffix
            filename = os.path.splitext(basename)   # get file name
            name = filename[0]
            ext = filename[1]
            t = time.strftime("%Y%m%d%H%M",time.localtime())
            newname = name + t  + ext 
            newfilepath = os.path.join(dir,newname)
            try:
                os.rename(filepath,newfilepath)
                msg = "Bankup " + filepath + " to " + newfilepath
                result = 0
            except:
                msg = "File "+ filepath + " access error, backup fail."
                result = -1
            finally:
                print(msg)
                self.logger.info(msg)
                return result            
        else:
            msg = "File "+ filepath + " is locked by other programm. bankup fail."
            print(msg)
            self.logger.info(msg)
            return -1


    def updateRemote(self,con, path):
        """Push local directory or file to remote."""
        pathlist = path.split(",")
        if pathlist[1] == "d":
            con.sendall(self.CM_PUSH_DIR)
            while True:
                recv = con.recv(128)
                if recv == self.CM_FETCH_NAME:
                    con.sendall(pathlist[0].encode())
                    break
            msg = "Send local directory "+ pathlist[0] + " to remote."

        if pathlist[1] == "f":
            con.sendall(self.CM_PUSH_FILE)
            #con.flush()
            time.sleep(0.1)
            while True:
                recv = con.recv(128)
                if recv == self.CM_FETCH_NAME:
                    con.sendall(path.encode())
                    msg = "Send file " + pathlist[0] + " to remote."
                    print(msg)
                    self.logger.info(msg)
                    #break
                if recv == self.CM_READY:
                    #con.flush()
                    break
            self.sendFile(con,pathlist[0])
        return 0
    
    def sendFolder(self,con,folder,synctime=0):
        """Send details of directory to remote."""

        for rec in folder:
            con.sendall(rec.encode())
            time.sleep(0.1)
        con.sendall(self.CM_SEND_OVER)

        msg = "Send " + str(len(folder)) + " paths in folder to remote."
        print(msg)
        self.logger.info(msg)


    def startSync(self):
        """Compare local directory to the remote directory,
        then push new local file to remote, and get new file in remote.
        """
        msg = "Starting two-way file sync between local(" + self.clientip + ") and remote(" + self.serverip +")"
        print(msg)
        self.logger.info(msg)
        con = self.connect()           
        localfolder = []
        remotefolder = []    

        now = int(time.time())
        if self.fullsync: 
            lastsync = 0
            msg = "Start full sync. Sync all files in both folder."
        else:
            msg = "Start increment sync. The last sync time is:" + self.synctime
            lastsync = time.strptime(self.synctime,"%Y-%m-%d %H:%M:%S")
            lastsync = int(time.mktime(lastsync))
        print(msg)
        self.logger.info(msg)

        if now > lastsync:
            localfolder = self.getFolder(self.localfolder,lastsync)               
            remotefolder = self.getRemoteFolder(con,self.remotefolder,lastsync)
        else:
            msg ="Now is not the scheduled sync time:" + self.synctime + "end sync."
            print(msg)
            self.logger.info(msg)
        
        #compare difference        
        diff = self.getDiff(localfolder,remotefolder)

        if diff:
            msg = "Start sync different path between local and remote."
            print(msg)
            self.logger.info(msg)
            for i in diff:
                if (i[1] == "new in remote") or i[1] == "only in remote":
                    self.getRemoteFile(con, i[0])
                if (i[1] == "new in local") or (i[1] == "only in local"):
                    self.updateRemote(con, i[0])
                if (i[1] == "have same size,but not same time."):
                    print(i[1])
            msg = "Sync all difference files."
        else:
            msg = "No difference found after last sync."
        
        print(msg)
        self.logger.info(msg)
        con.sendall(self.CM_SYNC_OVER)
        con.close()
        self.setconfig("time","synctime",time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
        msg = "Stop connect with remote(" + self.serverip +"), save new sync time to config.ini."
        print(msg)
        self.logger.info(msg)
        return 0


    def startServer(self):
        """Start file sync server, receive client's sync request and deal.
        
        Server will deal four type requests from client. 
        The first is send details of directory to client.
        The second is send files which need sync to client.
        The thired is receive the file which pushed by client and save it. 
        The fourth is receive the directory which pushed by client and create it.
        """

        server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        server.bind((self.serverip,self.port))
        server.listen(1)    # only allow one client connect
        msg = "Starting file sync service on " + self.serverip +", waiting for client connect."
        print(msg)
        self.logger.info(msg)
        # Deal sync request until stop server
        while True:
            con,addr = server.accept()
            if con: # receive client connect
                msg = "Client " + addr[0] + " is connected."
                print(msg)
                self.logger.info(msg)
                # Deal sync command until client close connect.
                while True:
                    recv = con.recv(1024)
                    #print("debug: sever waiting for next comand" ,recv)
                    if recv == self.CM_FETCH_DIR: 
                        msg = "Receive comand of fetch directory"  
                        print(msg)
                        self.logger.info(msg)
                        con.sendall(self.CM_FETCH_PATH) # request remote to send sync folder
                        while True:
                            syncpath = con.recv(1024).decode()
                            self.localfolder = syncpath.split(",")[1]
                            self.remotefolder = syncpath.split(",")[0]
                            msg = "Receive request sync path between " + self.localfolder + " and " + self.remotefolder
                            print(msg)
                            self.logger.info(msg)
                            break
                        con.sendall(self.CM_FETCH_TIME) # request last sync time
                        while True:  
                            recv = con.recv(4)
                            synctime = int.from_bytes(recv,byteorder="little")
                            # get details of directory which need sync.
                            folderinfo = self.getFolder(self.localfolder,synctime)
                            # send directory details to client
                            self.sendFolder(con,folderinfo) 
                            break
                        continue
                    if recv == self.CM_FETCH_FILE:
                        msg ="Receive command of fetch file"
                        print(msg)
                        self.logger.info(msg)
                        con.sendall(self.CM_FETCH_NAME)
                        while True:
                            filepath = con.recv(1024).decode()
                            if filepath: 
                                break
                        self.sendFile(con,filepath)
                        continue
                    if recv == self.CM_PUSH_FILE:
                        con.sendall(self.CM_FETCH_NAME)
                        #con.flush()
                        while True:
                            filepath = con.recv(1024).decode()
                            if filepath:
                                msg="Receive command of push file " + filepath
                                print(msg)
                                print(filepath)
                                self.logger.info(msg)
                                print("debug: ready to receive file.")
                                con.sendall(self.CM_READY)
                                self.recvFile(con,filepath)
                                break
                        continue
                    if recv == self.CM_PUSH_DIR:
                        msg="Receive command of push directory."
                        print(msg)
                        self.logger.info(msg)
                        con.sendall(self.CM_FETCH_NAME)
                        while True:
                            filepath = con.recv(1024).decode()
                            if filepath:
                                self.recvDir(filepath)
                                self.logger.info("get the dir name." + filepath)
                                break
                        continue
                    if recv == self.CM_SEND_OVER:
                        continue
                    if recv == self.CM_SYNC_OVER:
                        con.close()
                        msg = "End file sync with " + self.clientip + ",close connect and waiting for new sync."
                        print(msg)
                        self.logger.info(msg)
                        self.setconfig("time","synctime",time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
                        break
        return 0
    
if __name__ == "__main__":
    s = FileSync()
    s.startServer()



