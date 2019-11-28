import time
test_proxy = 10
test_proxy_excellent = 11
test_proxy_good = 12
test_proxy_normal = 13
test_proxy_poor = 14
test_proxy_fail = 15
test_proxy_over_time = 17
try_open_proxy = 16


def print_red(mes):
    print("\033[31m%s\033[0m" % mes)


def print_green(mes):
    print("\033[32m%s\033[0m" % mes)

def _print(mes, color=None, isdis=True, mes_collent=None, showtime=True):
    
    if (showtime):        
        now = time.asctime(time.localtime(time.time()))
        mes = now + '   '+mes
    if(isdis):
        if(color == None):
            print(mes)
        elif(color == 'red'):
            print_red(mes)
        else:
            print_green(mes)
    
    if(mes_collent != None):
        test_log = open('test_log', 'a')
        
        now = time.time()
        if mes_collent == test_proxy_excellent:
            test_log.write("%f %s\n" % (now,mes))
        elif mes_collent == test_proxy_fail:
            test_log.write("%f %s\n" % (now,mes))
        elif mes_collent == test_proxy_good:
            test_log.write("%f %s\n" % (now,mes))
        elif mes_collent == test_proxy_normal:
            test_log.write("%f %s\n" % (now,mes))
        elif mes_collent == test_proxy_poor:
            test_log.write("%f %s\n" % (now, mes))
        elif mes_collent == test_proxy_over_time:
            test_log.write("%f %s\n" % (now, mes))     
        
        
        test_log.close()


def percent(a, b):
    return ('{:.2%}'.format(a/b))


def put_dis(a, b):
    print("上传完成 %s" % percent(a, b))


def get_dis(a, b):
    print("下载完成 %s" % percent(a, b))
