def to_str(bytes_or_str):
    if(bytes_or_str==None):
        return ''
    value = ''
    try:
        value = bytes_or_str.decode()
    except Exception as e:
        hexstr = " ".join(byto_hex(bytes_or_str))
        value += "UTF-8编码失败,下面是源Hex码"
        value += "\n%s" % hexstr
    return value

def bytes_del_nodis(bys):     
    lis = []
    for tt in bys:
        if(tt>127):
            continue
        lis.append(chr(tt))
    
    
    return ''.join(lis)

def str_to_lines(st):
    strlines = []
    line = ''
    i = 0
    for t in st:
        if(t != '\n'):
            line = line + t
        else:
            strlines.append(line)
            i = i+1
            line = ''
    return strlines

def col_of_strs(strlines,col):
    arrylines = str_to_lines(strlines)
    colcumn = []
    for te in arrylines:
        tt = te.split()
        colcumn.append(tt[col-1])
    return colcumn

def get_line(lines, start=0, howmuch=-1):
    listlines = str_to_lines(lines)
    lenlist = len(listlines)
    end = lenlist + 1
    if(howmuch > 0):
        end =  start + howmuch
    
    strt = listlines[start:]

    return strt


def byto_hex(bys):
    by = [hex(int(i)) for i in bys]
    return by
