import collections
from typing import List


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
    return collections.Counter(lst1) == collections.Counter(lst2)


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