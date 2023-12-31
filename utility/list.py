# lst1 = [23, 15, 2, 14, 14, 16, 20 ,52]
# lst2 = [2, 48, 15, 12, 26, 32, 47, 54]
import collections


# get unique elements of a list
def unique(lst1):
    return (list(set(lst1)))

# union: maintained repetition
# => [23, 15, 2, 14, 14, 16, 20, 52, 2, 48, 15, 12, 26, 32, 47, 54]
def UnionMR(lst1:list, lst2:list):
    final_list = lst1 + lst2
    return final_list


# union: maintained repetition and order
# => [2, 2, 12, 14, 14, 15, 15, 16, 20, 23, 26, 32, 47, 48, 52, 54]
def UnionMRO(lst1:list, lst2:list) -> list:
    final_list = sorted(lst1 + lst2)
    return final_list


# union: without repetition
# => [32, 2, 12, 14, 15, 16, 48, 47, 20, 52, 54, 23, 26]
def UnionNoRep(lst1:list, lst2:list) -> list:
    final_list = list(set(lst1) | set(lst2))
    return final_list


# union: without repetition and order
# => [32, 2, 12, 14, 15, 16, 48, 47, 20, 52, 54, 23, 26]
def UnionNoRepO(lst1:list, lst2:list) -> list:
    final_list = sorted(list(set(lst1) | set(lst2)))
    return final_list


def same_elements(lst1:list, lst2:list) -> bool:
    return collections.Counter(lst1) != collections.Counter(lst2)


# all elements of lst1 are present also in lst2 (lst1 < lst2)
def first_contained_in_second(lst1:list, lst2:list) -> bool:
    return all(item in lst2 for item in lst1)


def intersection(lst1, lst2) -> bool:
    return any(check in lst1 for check in lst2)


def get_intersecting(lst1, lst2) -> list:
    res = []
    for check in lst2:
        if check in lst1:
            res.append(check)
    return check





