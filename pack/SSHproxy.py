
import os, configparser, time, stat
if __name__ == "__main__":    
    from ParamikoClient import ParamikoClient
    from str_tool import get_line,to_str
    from _print import _print
else:      
    from pack.ParamikoClient import ParamikoClient
    from pack.str_tool import get_line,to_str
    from pack._print import _print
    import pack.collect as collect
    

ifdebug = False


class SSHproxy(ParamikoClient):
    def __init__(self,config_str):
        super(SSHproxy,self).__init__(config_str)
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
        self.remote_work_dir = ''

    def set_remote_work_dir(self):
        self.remote_work_dir = self.remote_rootdir + '/' + 'sshproxy'
    def sftp_work_dir_check(self):
        self.open_sftp()
        listdir = self.sftp_listdir()
        for i in listdir:
            if(i == '_init'):
                return True
        return False
    def my_init(self):
        self.get_remote_rootdr()

# class WIN_SSHproxy(SSHproxy):
#     def __init__(self,config_str):
#         pass

class UNIX_SSHproxy(SSHproxy):
    def __init__(self, config_str):
        super(UNIX_SSHproxy, self).__init__(config_str)

        
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


    def sftp_chang_in_work_dir(self, isdis=False):
        self.open_sftp()        
        _print('进入工作目录', None, isdis and ifdebug)
        self.sftp_change_dir(self.remote_work_dir)
        re = self.sftp_work_dir_check()
        return re
        

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
        self.exec_command(com_str,ifdebug, 4)
        newtime = time.time()
        if self.out != None:           
            htmllen = len(self.out)
        else:htmllen = 0
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
        com_str = "lsof -i:%s | grep -i LISTEN | awk '{print $2}'" % self.socks_port
        self.exec_command(com_str, isdis)
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
        remote_rsa_filename = self.remote_rootdir + '/' + self.remote_work_dir + '/' + basename
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
        
        self.shell_run(com_str, 5)
        _print("尝试打开代理进程",None,True,collect.try_open_proxy)
        if(self.is_first_connect_proxy_server(self.out)):
            _print('首次连接代理服务器')            
            self.shell_run('yes')

    def is_first_connect_proxy_server(self,out):
        strout = ''
        keys = ('to continue connecting','yes/no')
        try:
            strout = self.out.decode().lower()
        except Exception:
            pass
        for key in keys:
            if(strout.find(key) < 0):
                return False
        return True

    def open_proxy(self):
        re = self.proxy_check()       
        pid = self.get_proxy_pid()
        #re = False
        if(re == True):
            _print('代理正常','green')        
            _print('代理进程 pid: %s' % pid, 'green')          
        else:
            _print('代理异常','red')
            if(pid > 0):
                _print('代理进程 pid: %s 无效' % pid, 'red')
                re = self.kill_pid(pid)
                if(re == True):
                    self._open_proxy()
                    re = self.proxy_check()
                else:
                    return False
            else:
                self._open_proxy()
                re = self.proxy_check()
        return re
