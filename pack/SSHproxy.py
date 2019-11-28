
import os, configparser, time, stat
if __name__ == "__main__":    
    from ParamikoClient import ParamikoClient
    from str_tool import get_line
    from _print import _print
else:      
    from pack.ParamikoClient import ParamikoClient
    from pack.str_tool import get_line
    from pack._print import _print
    import pack.collect as collect
    

ifdebug = False


class UNIX_SSHproxy(ParamikoClient):
    def __init__(self, config_str):
        super(UNIX_SSHproxy, self).__init__(config_str)

        self.work_dir_name = '.sshproxy'
        self.remote_rsa_file = ''
        try:
            self.local_rsa_file = ''
            self.proxy_server_ip = self.config.get('server', 'host')
            self.proxy_server_port = int(self.config.get('server', 'port'))
            self.proxy_server_user = self.config.get('server', 'username')
            self.socks_port = self.config.get('server', 'socks_port')
        except Exception as e:
            _print("配置文件不完整,或者格式错误%s" % e, 'red')
            exit()


        self.proxy_time = 0
        self.proxy_pid = 0


    def is_work_dir_exit(self, isdis=False):
        return self.is_file_exist(self.work_dir_name, isdis)

    def mk_work_dir(self, isdis=False):
        if(self.is_work_dir_exit() == True):

            _print('工作文件夹已存在', None, isdis and ifdebug)
            self.exec_command('touch %s/_init' % self.work_dir_name, False)
            return True
        _print('创建工作文件夹', None, isdis and ifdebug)
        re = self.mkdir(self.work_dir_name)
        self.exec_command('touch %s/_init' % self.work_dir_name, False)
        return re

    def sftp_work_dir_check(self):
        self.open_sftp()
        listdir = self.sftp_listdir()
        for i in listdir:
            if(i == '_init'):
                return True
        return False

    def sftp_chang_in_work_dir(self, isdis=False):
        self.open_sftp()
        if(self.sftp_work_dir_check() == True):
            return True
        if(self.mk_work_dir() == True):
            _print('进入工作目录', None, isdis and ifdebug)
            self.sftp_change_dir(self.work_dir_name)
            re = self.sftp_work_dir_check()
            return re
        else:
            _print("工作目录不存在", 'red', ifdebug)
            return False

    def up_rsa_file(self, isdis=False):

        re = self.open_sftp()
        if(re == True):
            if(self.local_rsa_file == ''):
                _print('代理 local_rsa_file 文件未配置', 'red')
                return False
            if(self.sftp_chang_in_work_dir() == False):
                _print('非sshproxy工作目录', 'red')
                return False
            _print('上传 rsa 文件', None, ifdebug)
            self.remote_rsa_file = self.remote_rootdir + '/' + \
                self.work_dir_name + '/' + os.path.basename(self.local_rsa_file)
            self.put(self.local_rsa_file, self.remote_rsa_file, isdis)
            re = self.is_file_exist(self.remote_rsa_file)
            if(re == True):
                self.sftp.chmod(self.remote_rsa_file, 0o600)
                return True
        return False

    def proxy_check(self,isdis = True):
        self.open_sshclient()
        _print('测试代理')
        oldtime = time.time()
        com_str = 'curl -x socks5h://127.0.0.1:%s www.google.com' % self.socks_port
        print(com_str)
        self.exec_command(com_str, False, 4)
        newtime = time.time()
        htmllen = len(self.out)
        time_cose = newtime-oldtime
        self.proxy_time = time_cose
        if(htmllen > 10000):
            if(time_cose < 1):
                _print('代理速度 %.3f 秒 优秀' % time_cose, 'green',
                       isdis or ifdebug, collect.test_proxy_excellent)
                return True
            elif(time_cose < 2):
                _print('代理速度 %.3f 秒 良好' % time_cose,
                       'green', isdis or ifdebug, collect.test_proxy_good)
                return True
            elif(time_cose < 3):
                _print('代理速度 %.3f 秒 正常' % time_cose,
                       None, isdis or ifdebug, collect.test_proxy_normal)
                return True
            else:
                _print('代理速度 %.3f 秒 不佳,现在是网络波动' %
                       time_cose, 'red', isdis or ifdebug, collect.test_proxy_poor)
                return False
        else:
            _print('代理速度 大于4 秒 失败', 'red', isdis or ifdebug, collect.test_proxy_fail)
            return False

    def get_proxy_pid(self, isdis=False):
        self.open_sshclient()
        _print('获取pid', None, ifdebug and isdis)
        self.exec_command(
            "lsof -i:6060 | grep -i LISTEN | awk '{print $2}'", False)
        strpid = self.out.decode()
        strpid = get_line(strpid, 0, 1)
        pid = 0
        try:
            pid = int(strpid)
        except Exception:
            pass
        if(pid == 0):
            _print('没有代理进程运行', None, ifdebug)
        self.proxy_pid = pid
        return pid

    def check_remote_rsa(self):
        self.open_sshclient()
        basename = os.path.basename(self.local_rsa_file)
        remote_rsa_filename = self.remote_rootdir + '/' + self.work_dir_name + '/' + basename
        if self.is_file_exist(remote_rsa_filename):
            return remote_rsa_filename
        return None
    def _open_proxy(self, isdis=False):
        self.open_sshclient()

        self.remote_rsa_file = self.check_remote_rsa()
        if (self.remote_rsa_file == None):
            if (self.up_rsa_file() == False):
                _print("rsa文件上传失败", 'red')
                return False
        sock_port = self.socks_port
        rsa_file = self.remote_rsa_file
        ssh_port = self.proxy_server_port
        username = self.proxy_server_user
        hostname = self.proxy_server_ip
        
        com_str = 'ssh -D%s -i %s -fNg -p%s %s@%s' % (
            sock_port, rsa_file, ssh_port, username, hostname)
        _print(com_str)
        self.shell_run(com_str, 5)
        _print("尝试打开代理进程",None,ifdebug,collect.try_open_proxy)
        _print(self.out.decode(), None, ifdebug)

    def open_proxy(self):
        re = self.proxy_check()
        pid = self.proxy_pid
        if(pid == 0):
            pid = self.get_proxy_pid()
        #re = False
        if(re == True):
            if(pid > 0):
                _print('代理进程 pid: %s' % pid, 'green', ifdebug)
            return True
        else:
            if(pid > 0):
                re = self.kill_pid(pid)
                if(re == True):
                    self._open_proxy()
                else:
                    return False
            else:
                self._open_proxy()

        re = self.proxy_check()
        return re
