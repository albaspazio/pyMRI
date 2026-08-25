import os
import re
from typing import List, Tuple

import matplotlib.pyplot as plt

# on the X-axis goes the order with the list (like an histogram, to separate two groups
def histogram_plot_2groups(
    string_list: List[str],
    fnameout: str,
    grp1_label: str,
    col_id: int = 3,
    measure_distance: float = 0.1,
    groups_offset: int = 3,
    colors: Tuple[str, str] = ("red", "green"),
    grp_labels: Tuple[str, str] = ("control", "experimental"),
) -> None:
    """
    Plots a histogram of two groups of data.

    Args:
        string_list (List[str]): A list of strings, where each string is a line of data.
        fnameout (str): The file name to save the plot to.
        grp1_label (str): The label of the first group.
        col_id (int, optional): The column index of the data to plot. Defaults to 3.
        measure_distance (float, optional): The distance between data points. Defaults to 0.1.
        groups_offset (int, optional): The offset between the two groups of data. Defaults to 3.
        colors (Tuple[str, str], optional): The colors of the data points. Defaults to ("red", "green").
        grp_labels (Tuple[str, str], optional): The labels for the legend. Defaults to ("control", "experimental").

    Returns:
        None: None
    """
    ctrl_y = []
    ctrl_x = []
    exp_y = []
    exp_x = []

    for s in range(len(string_list)):
        l = re.split(r"\t+", string_list[s])
        group_ch = l[0][0]
        if group_ch == grp1_label:
            ctrl_y.append(float(l[col_id]))
            ctrl_x.append(measure_distance * s)
        else:
            exp_y.append(float(l[col_id]))
            exp_x.append(measure_distance * s + groups_offset)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)  # , axisbg="1.0")

    ax.scatter(ctrl_x, ctrl_y, alpha=0.8, c=colors[0], edgecolors='none', s=30, label=grp_labels[0])
    ax.scatter(exp_x, exp_y, alpha=0.8, c=colors[1], edgecolors='none', s=30, label=grp_labels[1])

    plt.title(os.path.basename(fnameout))
    plt.legend(loc=4)
    plt.show()

    plt.savefig(fnameout, dpi=1200)
    plt.close()


# on the X-axis goes a the order with the list (like an histogram, to separate two groups
def scatter_plot_2groups(
    string_list: List[str],
    xdata: List[float],
    fnameout: str,
    grp1_label: str,
    col_id: int = 3,
    measure_distance: float = 0.1,
    groups_offset: int = 3,
    colors: Tuple[str, str] = ("red", "green"),
    grp_labels: Tuple[str, str] = ("control", "experimental"),
) -> None:
    """
    Plots a scatter plot of two groups of data.

    Args:
        string_list (List[str]): A list of strings, where each string is a line of data.
        xdata (List[float]): The x-axis data.
        fnameout (str): The file name to save the plot to.
        grp1_label (str): The label of the first group.
        col_id (int, optional): The column index of the data to plot. Defaults to 3.
        measure_distance (float, optional): The distance between data points. Defaults to 0.1.
        groups_offset (int, optional): The offset between the two groups of data. Defaults to 3.
        colors (Tuple[str, str], optional): The colors of the data points. Defaults to ("red", "green").
        grp_labels (Tuple[str, str], optional): The labels for the legend. Defaults to ("control", "experimental").

    Returns:
        None: None
    """
    ctrl_y = []
    ctrl_x = []
    exp_y = []
    exp_x = []

    for s in range(len(string_list)):
        l = re.split(r"\t+", string_list[s])
        group_ch = l[0][0]
        if group_ch == grp1_label:
            ctrl_y.append(float(l[col_id]))
            ctrl_x.append(measure_distance * s)
        else:
            exp_y.append(float(l[col_id]))
            exp_x.append(measure_distance * s + groups_offset)

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)  # , axisbg="1.0")

    ax.scatter(ctrl_x, ctrl_y, alpha=0.8, c=colors[0], edgecolors='none', s=30, label=grp_labels[0])
    ax.scatter(exp_x, exp_y, alpha=0.8, c=colors[1], edgecolors='none', s=30, label=grp_labels[1])

    plt.title(os.path.basename(fnameout))
    plt.legend(loc=4)
    plt.show()

    plt.savefig(fnameout, dpi=1200)
    plt.close()


# on the X-axis goes a the order with the list (like an histogram, to separate two groups
def scatter_plot_2dataseries(
    ydata1: List[float],
    xdata1: List[float],
    ydata2: List[float],
    xdata2: List[float],
    fnameout: str = "",
    colors: Tuple[str, str] = ("red", "green"),
    grp_labels: Tuple[str, str] = ("control", "experimental"),
) -> None:
    """
    Plots a scatter plot of two data series.

    Args:
        ydata1 (List[float]): The y-axis data for the first data series.
        xdata1 (List[float]): The x-axis data for the first data series.
        ydata2 (List[float]): The y-axis data for the second data series.
        xdata2 (List[float]): The x-axis data for the second data series.
        fnameout (str, optional): The file name to save the plot to. Defaults to "".
        colors (Tuple[str, str], optional): The colors of the data points. Defaults to ("red", "green").
        grp_labels (Tuple[str, str], optional): The labels for the legend. Defaults to ("control", "experimental").

    Returns:
        None: None
    """
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)  # , axisbg="1.0")

    ax.scatter(xdata1, ydata1, alpha=0.8, c=colors[0], edgecolors="none", s=30, label=grp_labels[0])
    ax.scatter(xdata2, ydata2, alpha=0.8, c=colors[1], edgecolors="none", s=30, label=grp_labels[1])

    plt.title(os.path.basename(fnameout))
    plt.legend(loc=4)

    if len(fnameout) > 0:
        plt.savefig(fnameout, dpi=1200)

    plt.close()


# on the X-axis goes a the order with the list (like an histogram, to separate two groups
def scatter_plot_dataserie(
    ydata: List[float],
    xdata: List[float],
    fnameout: str = "",
    color: str = "red",
    label: str = "control",
    show: bool = False,
) -> None:
    """
    Plots a scatter plot of two data series.

    Args:
        ydata (List[float]): The y-axis data.
        xdata (List[float]): The x-axis data.
        fnameout (str, optional): The file name to save the plot to. Defaults to "".
        color (str, optional): The color of the data points. Defaults to "red".
        label (str, optional): The label for the legend. Defaults to "control".
        show (bool, optional): Whether to display the plot. Defaults to False.

    Returns:
        None: None
    """
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)  # , axisbg="1.0")

    ax.scatter(xdata, ydata, alpha=0.8, c=color, edgecolors="none", s=30, label=label)

    plt.title(os.path.basename(fnameout))
    plt.legend(loc=4)

    if show:
        plt.show()

    if len(fnameout) > 0:
        plt.savefig(fnameout, dpi=1200)

    plt.close()
