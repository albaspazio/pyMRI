def is_list_of(_list, _type, checkall=True):
    if isinstance(_list, list):
        if not checkall:
            if isinstance(_list[0], _type):
                return True
        else:
            for i in _list:
                if not isinstance(i, _type):
                    return False
            return True
    return False


# get the sorting schema of a list(e.g [2,3,1,4,5] => [2,0,1,3,4]
def argsort(seq):
    # http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    # by unutbu
    return sorted(range(len(seq)), key=seq.__getitem__)


# apply the given permutation to a list
def reorder_list(_list, neworder):
    return [_list[i] for i in neworder]


def fillnumber2fourdigits(num):

    if num > 9999:
        print("Error in fillnumber2fourdigits, given number is > 9999")
        return

    if num < 10:
        str_num = "000" + str(num)
    elif 9 < num < 100:
        str_num = "00" + str(num)
    elif 99 < num < 1000:
        str_num = "0" + str(num)
    else:
        str_num = str(num)

    return str_num


# if is a string => cast to int or float (when appropriate) or keep it string
# if not         => don't do anything, return input param unchanged
def string2num(string):
    try:
        if not isinstance(string, str):
            return string

        fl_string = float(string)
        if round(fl_string) == fl_string:
            return int(fl_string)
        else:
            return fl_string
    except ValueError:
        return string


def listToString(_list, separator='\t'):

    _str = ""
    # traverse the list and concatenate to String variable
    for element in _list:
        _str += (str(element) + separator)

    return _str