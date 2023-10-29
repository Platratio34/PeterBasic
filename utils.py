import re

def split(regex, string):
    s = re.search(regex, string)
    if s is not None:
        sp = s.span()
        return [string[:sp[0]], string[sp[1]:]]
    else:
        return [string, ""]