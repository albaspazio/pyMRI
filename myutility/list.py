from __future__ import annotations

import collections
from typing import List, Any


def indices(lst1, value) -> List[int]:
    """
    Returns a list of indices where the value occurs in the list.

    Parameters
    ----------
    lst1 : list
        The list to search in.
    value : any
        The value to search for.

    Returns
    -------
    List[int]
        A list of indices where the value occurs in the list.

    """
    return [i for i, j in enumerate(lst1) if j == value]


def unique(lst1):
    """
    Returns a list of unique elements in the list.

    Parameters
    ----------
    lst1 : list
        The list to search in.

    Returns
    -------
    list
        A list of unique elements in the list.

    """
    return list(set(lst1))


def UnionMR(lst1: list, lst2: list) -> list:
    """
    Returns the union of two lists, maintaining repetition.

    Parameters
    ----------
    lst1 : list
        The first list.
    lst2 : list
        The second list.

    Returns
    -------
    list
        The union of the two lists, maintaining repetition.

    """
    return lst1 + lst2


def UnionMRO(lst1: list, lst2: list) -> list:
    """
    Returns the union of two lists, maintaining repetition and ordering.

    Parameters
    ----------
    lst1 : list
        The first list.
    lst2 : list
        The second list.

    Returns
    -------
    list
        The union of the two lists, maintaining repetition and ordering.

    """
    return sorted(lst1 + lst2)


def UnionNoRep(lst1: list, lst2: list) -> list:
    """
    Returns the union of two lists, without repetition.

    Parameters
    ----------
    lst1 : list
        The first list.
    lst2 : list
        The second list.

    Returns
    -------
    list
        The union of the two lists, without repetition.

    """
    return list(set(lst1) | set(lst2))


def UnionNoRepO(lst1: list, lst2: list) -> list:
    """
    Returns the union of two lists, without repetition and ordering.

    Parameters
    ----------
    lst1 : list
        The first list.
    lst2 : list
        The second list.

    Returns
    -------
    list
        The union of the two lists, without repetition and ordering.

    """
    return sorted(list(set(lst1) | set(lst2)))


def same_elements(lst1: list, lst2: list) -> bool:
    """
    Returns True if two lists have the same elements, False otherwise.

    Parameters
    ----------
    lst1 : list
        The first list.
    lst2 : list
        The second list.

    Returns
    -------
    bool
        True if the two lists have the same elements, False otherwise.

    """

    try:
        return sorted(collections.Counter(lst1)) == sorted(collections.Counter(lst2))
    except Exception as e:
        raise e

def first_contained_in_second(lst1: list, lst2: list) -> bool:
    """
    Returns True if the first list is contained in the second list, False otherwise.

    Parameters
    ----------
    lst1 : list
        The first list.
    lst2 : list
        The second list.

    Returns
    -------
    bool
        True if the first list is contained in the second list, False otherwise.

    """
    return all(item in lst2 for item in lst1)


def intersection(lst1, lst2) -> bool:
    """
    Returns True if the two lists have any elements in common, False otherwise.

    Parameters
    ----------
    lst1 : list
        The first list.
    lst2 : list
        The second list.

    Returns
    -------
    bool
        True if the two lists have any elements in common, False otherwise.

    """
    return any(check in lst1 for check in lst2)


def get_intersecting(lst1, lst2) -> list:
    """
    Returns a list of elements that are in both lists.

    Parameters
    ----------
    lst1 : list
        The first list.
    lst2 : list
        The second list.

    Returns
    -------
    list
        A list of elements that are in both lists.

    """
    res = []
    for check in lst2:
        if check in lst1:
            res.append(check)
    return res


def is_list_of(_list:List[Any], _type: type, checkall:bool=True) -> bool:
    """
    Checks if a given variable is a list of a specific type.

    Parameters
    ----------
    _list: variable
        The variable to be checked.
    _type: type
        The type that the elements of the list should be.
    checkall: bool, optional
        If set to True (default), all elements of the list must be of type _type.
        If set to False, only the first element of the list is checked.

    Returns
    -------
    bool
        True if the variable is a list of the specified type, False otherwise.

    """
    if not isinstance(_list, list):
        return False  # If it's not a list, return False

    if len(_list) == 0:  # Check if the list is empty
        return False  # Return False for empty lists

    if checkall:
        # Check if all elements in the list are of the given type
        return all(isinstance(item, _type) for item in _list)
    else:
        # Check only the first element
        return isinstance(_list[0], _type)

# apply the given permutation to a list
def reorder_list(_list, neworder):
    """
    Reorders a list according to a given permutation.

    Parameters
    ----------
    _list: list
        The list to be reordered.
    neworder: list
        A list of indices that specifies the new order of the elements in the list.

    Returns
    -------
    list
        The reordered list.

    """
    return [_list[i] for i in neworder]


def listToString(_list, separator='\t'):
    """
    Converts a list of values to a string, with each value separated by a separator.

    Parameters
    ----------
    _list: list
        The list of values to be converted to a string.
    separator: str, optional
        The separator to use between values (default is a tab character).

    Returns
    -------
    str
        The list values separated by the specified separator.

    """
    _str = _list[0]
    # traverse the list and concatenate to String variable
    for i in range(1, len(_list)):
        _str += separator + str(_list[i])

    return _str


def remove_items_from_list(origlist, list2remove):
    """
    Removes items from a list that are also present in another list.

    Parameters
    ----------
    origlist: list
        The original list.
    list2remove: list
        The list of items to be removed.

    Returns
    -------
    list
        The list with the specified items removed.

    """
    res = []
    for orig_list in origlist:
        if orig_list not in list2remove:
            res.append(orig_list)
    return res


def get_col_from_listmatrix(matrix, zerocolid):
    """
    Extracts a column from a list of lists.

    Parameters
    ----------
    matrix: list of list
        The list of lists from which the column is to be extracted.
    zerocolid: int
        The index of the column to be extracted (zero-based).

    Returns
    -------
    list
        The values of the specified column.

    Raises
    ------
    ValueError
        If the specified column index is out of range.

    """
    ncols = len(matrix[0])

    if zerocolid >= ncols:
        raise ValueError("Error in get_col_from_listmatrix, given colid "
                         "({}) is higher than available columns".format(zerocolid))

    return [r[zerocolid] for r in matrix]


def _argsort(seq):
    """
    Returns the indices that would sort a list in ascending order.

    Parameters
    ----------
    seq: list
        The list for which the sorting indices are to be returned.

    Returns
    -------
    list
        A list of indices that, when applied to the original list, would sort it
        in ascending order.

    """
    # http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    # by unutbu
    return sorted(range(len(seq)), key=seq.__getitem__)
