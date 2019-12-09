import datetime
import random
test_proxy = 10
test_proxy_excellent = 11
test_proxy_good = 12
test_proxy_normal = 13
test_proxy_poor = 14
test_proxy_fail = 15
test_proxy_over_time = 17
try_open_proxy = 16
testlog_label = 19


def print_red(mes):
    print("\033[31m%s\033[0m" % mes)


def print_green(mes):
    print("\033[32m%s\033[0m" % mes)


def to_file(mes, filename):
    fl = open(filename, 'a')
    mes = mes + '\n'
    fl.write(mes)
    fl.close()


test_log_name = 'log_init'


def _print(mes, color=None, isdis=True, mes_collent=None, showtime=True, logname=None):
    global test_log_name
    if (showtime):
        now = datetime.datetime.now()
        time_easy = now.strftime("%Y/%m/%d %X")
        mes = time_easy + '   '+mes
    if(isdis):
        if(color == None):
            print(mes)
        elif(color == 'red'):
            print_red(mes)
        else:
            print_green(mes)
    if(mes_collent == None):
        return
    else:
        if(True):
            return
        if(test_log_name == 'log_init'):
            test_log_name = logname

        if(mes.strip() != ''):
            to_file(mes, test_log_name)


def percent(a, b):
    return ('{:.2%}'.format(a/b))


def put_dis(a, b):
    print("上传完成 %s" % percent(a, b))


def get_dis(a, b):
    print("下载完成 %s" % percent(a, b))
