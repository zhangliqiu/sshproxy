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


def str_to_lines(st):
    strlines = {}
    line = ''
    i = 0
    for t in st:
        if(t != '\n'):
            line = line + t
        else:
            strlines[i] = line
            i = i+1
            line = ''
    return strlines


def get_line(lines, start=0, howmuch=-1):
    try:
        lines = str_to_lines(lines)
        strt = ''
        i = 0
        for t in lines:
            if(t >= start):
                strt = strt + lines[t] + '\n'
                i = i + 1
                if(howmuch > 0 and i == howmuch):
                    break
    except TypeError as e:
        return lines

    return strt


def byto_hex(bys):
    by = [hex(int(i)) for i in bys]
    return by
