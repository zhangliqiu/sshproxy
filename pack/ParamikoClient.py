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
        self.localdir = os.path.dirname(__file__)
        self.out = None
        self.error = None

    def Get_ping(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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

        return self.ping

    def connect(self):
        ping = self.Get_ping()

        if (self.permit_connect == False):
            return False

        if(self.Transport_status == 1):
            return True
        try:
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
            self.get_remote_rootdir()
            return True
        except paramiko.SSHException as e:
            _print(e, 'red')
            self.SSHClient.close()
            raise e

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
            _print("执行: %s" % com_str, None, isdis and ifdebug)
            stdin, stdout, stderror = self.SSHClient.exec_command(
                com_str, -1, wait)
            self.out = stdout.read()
            self.error = stderror.read()

            if(isdis):
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

    def get_remote_rootdir(self):
        self.open_sshclient()
        self.exec_command('pwd', False)
        self.remote_rootdir = to_str(self.out).strip()
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

    def is_file_exist(self, filename, isdis=False):
        self.open_sshclient()

        filename = self.remote_to_absolute(filename)

        com_str = 'ls %s > /dev/null 2>&1;echo $?' % filename
        self.exec_command(com_str, False)
        result = int(self.out)
        if(result == 0):
            _print("%s 存在" % filename, 'green', ifdebug and isdis)
            return True
        _print("%s 不存在" % filename, 'red', ifdebug and isdis)
        return False

    # put get 所用
    def local_to_absolute(self, filename):
        if(filename[0] != '/'):
            filename = self.localdir + '/' + filename
        return filename

    def remote_to_absolute(self, filename):
        self.get_remote_rootdir()
        if(filename[0] != '/'):
            filename = self.remote_rootdir + '/' + filename
        return filename

    def mkdir(self, dirname, isdis=False):
        self.open_sshclient()
        newdir = self.remote_to_absolute(dirname)

        if(self.is_file_exist(dirname)):

            _print('%s 已存在无需新建' % newdir, None, ifdebug and isdis)
            return True
        com_str = 'mkdir %s' % dirname
        self.exec_command(com_str, False)
        re = self.is_file_exist(dirname)
        if(re == True):
            _print('%s 新建成功' % newdir, 'green', isdis and ifdebug)
            return True
        _print(' 新建%s失败,请查找原因' % newdir, 'red')
        return False

    def sftp_change_dir(self, dirname):
        self.open_sftp()
        self.sftp.chdir(dirname)

    def put(self, localpath, remotepath=None, isdis=False):
        self.open_sftp()

        localpath = self.local_to_absolute(localpath)
        if(remotepath == None):
            remotepath = os.path.basename(localpath)

        remotepath = self.remote_to_absolute(remotepath)
        #print("put\nlocal:%s\nremote:%s" % (localpath, remotepath))
        if(isdis):
            self.sftp.put(localpath, remotepath, put_dis)
        else:
            self.sftp.put(localpath, remotepath)

    def get(self, remotepath, localpath=None, isdis=False):
        self.open_sftp()

        remotepath = self.remote_to_absolute(remotepath)
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

    def process_check(self, pid):
        pid = int(pid)
        com_str = "ps aux | awk '{print $2}' | grep %s" % pid
        self.exec_command(com_str)
        newpid = None
        try:
            newpid = int(self.out)
        except Exception as e:
            return False

        if(pid == newpid):
            return True
        return False

    def kill_pid(self, pid, isdis=True):
        pid = int(pid)
        com_str = 'kill %s' % pid
        _print("杀死进程 %s " % pid, None, isdis and ifdebug)
        self.exec_command(com_str)
        time.sleep(4)
        re = self.process_check(pid)
        if(re == True):
            _print("尝试第二次杀死进程 %s" % pid, None, isdis and ifdebug)
            com_str = "kill -9 %s" % pid
            self.exec_command(com_str)
            time.sleep(4)
            re = self.process_check(pid)
            if(re):
                _print("进程 %s 杀死失败" % pid, 'red', isdis and ifdebug)
                return False
        _print("进程 %s 杀死成功" % pid, 'green', isdis and ifdebug)
        return True

    def close(self):
        self.sftp.close()
        self.sftp_status = 0
        self.Chanel.close()
        self.Chanel_status = 0
        self.Transport.close()
        self.Transport_status = 0
