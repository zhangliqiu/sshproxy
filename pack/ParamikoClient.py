import paramiko
import configparser
import time
import os
import socket
import copy
if __name__ == "__main__":
    from str_tool import get_line, byto_hex, to_str
    from _print import _print, put_dis, get_dis
else:

    from pack.str_tool import get_line, byto_hex, to_str
    from pack._print import _print, put_dis, get_dis

ifdebug = False
time_cose = False


class ParamikoClient(object):
    def __init__(self, config_str):
        self.config = configparser.ConfigParser()
        self.config.read(config_str)
        try:
            self.hostname = self.config.get('user', 'host')
            self.sshport = int(self.config.get('user', 'port'))
            self.username = self.config.get('user', 'username')
            self.password = self.config.get('user', 'password')
            self.os = self.config.get('user','os')
        except Exception as e:
            _print("配置文件不完整,或者格式错误%s" % e, 'red')
            exit()

        self.ping = None  # 单位   ms
        self.addr = (self.hostname, self.sshport)
        self.sock = None

        self.alive = False
        self.permit_connect = False
        self.Transport = paramiko.channel
        self.Transport_status = 0

        self.SSHClient = paramiko.SSHClient()
        self.SSHClient_status = 0
        self.Chanel = paramiko.Channel
        self.Chanel_status = 0
        self.sftp = paramiko.sftp
        self.sftp_status = 0

        self.SSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.remote_rootdir = '未连接'
        self.localdir = os.getcwd()
        self.out = None
        self.error = None
    #获取远程根目录对 ftp 对上传下载比较重要,所有我放在了基类



    def Get_ping(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            t1 = time.time()
            sock.connect((self.hostname, self.sshport))
            t2 = time.time()
            sock.close()
            self.ping = (t2 - t1) * 1000
            self.alive = True
            self.permit_connect = True
        except socket.timeout:
            self.alive = False
        except ConnectionRefusedError:
            self.alive = True
            self.permit_connect = False
            _print("连接被拒绝", 'red')
        except Exception:
            pass
        return self.ping

    def connect(self):
        ping = self.Get_ping()

        if (self.permit_connect == False):
            return False

        if(self.Transport_status == 1):
            return True
       
            _print("正在连接    %s@%s  端口:%s" %
                   (self.username, self.hostname, self.sshport), None)
            ping = self.ping
            if(ping > 100):
                _print("网络延迟: %.0f ms" % ping, 'red')
            else:
                _print("网络延迟: %.0f ms" % ping, 'green')

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.hostname, self.sshport))
            Transport = paramiko.Transport(sock)
            Transport.connect(username=self.username,
                                password=self.password)
            self.sock = sock
        except socket.timeout:
            _print("连接超时", 'red')
            return False
        except paramiko.SSHException:
            _print("认证失败", 'red')
            return False

        self.Transport = Transport
        self.Transport_status = 1
        _print("连接成功", 'green')
        return True
    


    def open_sshclient(self):
        if(self.Transport_status == 0):
            self.connect()
        if(self.SSHClient_status == 1):
            return True

        self.SSHClient._transport = self.Transport
        self.SSHClient_status = 1
        return True

    def exec_command(self, com_str, isdis=False, wait=1):
        self.open_sshclient()

        old = float(time.time())
        try:
            _print("执行: %s" % com_str, None, isdis)
            stdin, stdout, stderror = self.SSHClient.exec_command(
                com_str, -1, wait)
            self.out = stdout.read()            
            self.error = stderror.read()

            if(ifdebug):
                self.print_result()
            if(time_cose == True):
                now = float(time.time())
                _print("耗时:%.3f 秒" % (now - old))
            return True
        except paramiko.SSHException as e:
            _print('连接异常,命令执行失败', 'red')
            raise e
        except socket.timeout:
            _print('执行超时返回', 'red')

    def print_result(self):
        _print("\n ===========打印结果===========")
        if(len(self.out) != 0):
            _print(to_str(self.out), 'green')
        if(len(self.error) != 0):
            _print('错误:')
            _print(to_str(self.error), 'red')
        _print("\n ==========结束============")

    def open_channel(self):
        if(self.Transport_status == 0):
            self.connect()
        if(self.Chanel_status == 1):
            return True
        else:
            try:
                _print('打开channel...', None, ifdebug)
                self.Chanel = self.Transport.open_session()
                self.Chanel.get_pty()
                self.Chanel.invoke_shell()
                self.Chanel_status = 1
                _print('打开成功', 'green', ifdebug)
                self.recv(0.3)
                return True
            except paramiko.SSHException as e:
                _print("channel打开失败", 'red')
                _print(e, 'red')
                raise e

    def channel_send(self, bs, isdis=False):
        self.open_channel()
        mu = self.Chanel.send(bs)
        if(mu > 0):
            _print("发送%s个字节" % mu, 'green', ifdebug and isdis)
        return mu

    def shell_run(self, command, wait=0.1, isdis=False):

        self.open_channel()
        sends = command.encode()
        self.channel_send(sends)

        # 清除回显
        
        recvtime = self.ping*2/1000  # 单位   s
        self.recv(recvtime, isdis)
        _print("输入 :%s " % command, None, ifdebug and isdis)
        # 发送会车以执行
        self.channel_send(b'\n')
        _print("会车", None, ifdebug and isdis)
        wait = wait + (recvtime)
        stdout = self.recv(wait, isdis)
        self.out = stdout
        if(isdis):
            self.print_result()

    def recv(self, wait=0.010, isdis=False):
        re = b''
        _print('数据等待 %s 秒' % wait, None, ifdebug and isdis)
        try:

            self.Chanel.settimeout(wait)
            time.sleep(wait)
            re = self.Chanel.recv(2048)
        except Exception as identifier:
            pass
        if(isdis):
            print(re)
        return re


    def get_remote_rootdr(self):
        
        if(self.os == 'unix'):
            self.exec_command('pwd')
            self.remote_rootdir = self.out.decode().strip()
        elif(self.os == 'win'):
            self.shell_run('\r',0.5,False)
            
            strout = self.out.__str__()
            sta = strout.find('C:\\')
            end = strout.find('>')
            self.remote_rootdir = strout[sta:end].replace('\\\\','\\')
        return self.remote_rootdir

    def open_sftp(self):
        re = self.connect()
        if (re == False):
            return False
        if(self.sftp_status == 1):
            return True
        transport = paramiko.Transport((self.hostname, self.sshport))
        transport.connect(username=self.username, password=self.password)
        self.sftp = paramiko.SFTPClient.from_transport(transport)
        self.sftp_status = 1
        return True

    def sftp_listdir(self, path='.'):
        re = self.open_sftp()
        if (re == True):
            re = self.sftp.listdir(path)
        return re


    # put get 所用
    def local_to_absolute(self, filename):
        if(filename[0] != '/'):
            filename = self.localdir + '/' + filename
        return filename

    def remote_to_absolute(self, filename):
        #print(filename)
        
        if(self.remote_rootdir[0] != '/'):
            if(self.remote_rootdir[1] != ':'):
                _print('远程根目录为: %s' % self.remote_rootdir,'red')
                raise Exception
        if(filename[0] == '/' or filename[1] == ':'):
            return filename
        filename = self.remote_rootdir + '/' + filename
        return filename



    def sftp_change_dir(self, dirname):
        self.open_sftp()
        self.sftp.chdir(dirname)

    def put(self, localpath, remotepath=None, isdis=True):
        self.open_sftp()
        #print("%s  %s" % (localpath, remotepath))
        localpath = self.local_to_absolute(localpath)
        if(remotepath == None):
            remotepath = os.path.basename(localpath)

        try:            
            remotepath = self.remote_to_absolute(remotepath)
        except Exception:
            return False
        #print("put\nlocal:%s\nremote:%s" % (localpath, remotepath)) 
        if(isdis):
            self.sftp.put(localpath, remotepath, put_dis)
        else:
            self.sftp.put(localpath, remotepath)


    def get(self, remotepath, localpath=None, isdis=True):
        self.open_sftp()
        try:    
            remotepath = self.remote_to_absolute(remotepath)
        except Exception:
            return False  
        basename = os.path.basename(remotepath)
        if(localpath == None):
            localpath = self.localdir + '/' + basename
        localpath = self.local_to_absolute(localpath)

        if(os.path.isdir(localpath)):
            if(localpath[-1] != '/'):
                localpath = localpath + '/'
            localpath = localpath + basename
        #print("get:\nremote:%s\nlocal:%s" % (remotepath, localpath))
        if(isdis):
            self.sftp.get(remotepath, localpath, get_dis)
        else:
            self.sftp.get(remotepath, localpath)



    def close(self):
        self.sftp.close()
        self.sftp_status = 0
        self.Chanel.close()
        self.Chanel_status = 0
        self.Transport.close()
        self.Transport_status = 0
