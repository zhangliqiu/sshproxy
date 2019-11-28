
import paramiko
import os
import socket
import sys
import time
import configparser
import random
from pack.SSHproxy import UNIX_SSHproxy
from pack._print import _print
# 数据收集
import pack.collect as collect

basedir = os.getcwd()

basename = os.path.basename(__file__)
def toabs_path(filename):
    if (filename[0] != '/'):
        filename = basedir + '/' + filename
    return filename

__author__ = 'likeliekkas'
__telegram__ = '+1 626 346 7918'

argv = sys.argv
if (len(argv) != 3):
    print("usage: %s configfile_name server_rsa_filename" % basename)
    exit()
configname = toabs_path(argv[1])
rsa_file = toabs_path(argv[2])

# print("%s %s " % (configname, rsa_file))
# exit()
config = configparser.ConfigParser()
config.read(configname)
try:
    check_alive_cycle = int(config.get('config', 'check_alive_cycle'))
    open_proxy_cycle_base = int(config.get('config', 'open_proxy_cycle_base'))
    open_proxy_cycle_range = int(config.get(
        'config', 'open_proxy_cycle_range'))
    open_proxy_fail_cycle = int(config.get('config', 'open_proxy_fail_cycle'))
    open_proxy_fail_time = int(config.get('config', 'open_proxy_fail_time'))
except Exception as e:
    _print("配置文件不完整,或者格式错误%s" % e, 'red')
    exit()

os.system('clear')
mes = ''
head = "\n\n\n作者: %s\n电报: %s\n" % (__author__, __telegram__)
head += "本代理基于 ssh 动态端口转发\n"
head += "向 IETF 组织致敬\n"
mes += head
mes += "\n\n\n本程序\n每过 %s 秒会检查下被代理主机是否开机" % check_alive_cycle
mes += "\n每过 %s ~ %s 秒维护一次代理,如果维护失败" % (
    open_proxy_cycle_base, open_proxy_cycle_base + open_proxy_cycle_range)
mes += "\n则会在 %s 秒后再次维护" % open_proxy_fail_cycle
mes += "\n如果连续 %s 次维护失败,程序退出\n\n\n程序会在 4 秒钟后运行" % open_proxy_fail_time
_print(mes, 'green', True, None, False)

_print('\n\n特别提醒,本程序用到第外部库为 paramiko\n可以使用 \npip3 install paramiko\n失败多试几次再百度',
       'red', True, None, False)
time.sleep(1)
os.system('clear')

continous_failcount = 0

while True:
    client = UNIX_SSHproxy(configname)
    client.local_rsa_file = rsa_file
    client.Get_ping()
    if (client.permit_connect == True):
        _print("主机上线", 'green')
        client.connect()
        client.my_init()
        while True:
            try:
                re = client.open_proxy()
                if (re == True):
                    continous_failcount = 0
                    next_open_time = open_proxy_cycle_base + \
                        random.randint(0, open_proxy_cycle_range)
                else:
                    continous_failcount += 1
                    _print('连续第 %s 次维护代理失败' % continous_failcount, 'red')
                    if (continous_failcount == open_proxy_fail_time):
                        _print('达到连续维护失败次数,程序退出,可以联系作者以讨论问题', 'red',True,collect.test_proxy_over_time)
                        exit()
                    next_open_time = open_proxy_fail_cycle
            except paramiko.ssh_exception.SSHException:
                break
            _print("%s 秒后再次维护代理" % next_open_time)
            time.sleep(next_open_time)

    _print("主机断线", 'red')
    del client
    time.sleep(check_alive_cycle)
