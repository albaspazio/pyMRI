import os
import re

import matplotlib.pyplot as plt


# on the X-axis goes a the order with the list (like an histogram, to separate two groups
def histogram_plot_2groups(string_list, fnameout, grp1_label, col_id=3, measure_distance=0.1,
                           groups_offset=3, colors=("red", "green"), grp_labels=("control", "experimental")):
    ctrl_y = []
    ctrl_x = []
    exp_y = []
    exp_x = []

    for s in range(len(string_list)):
        l = re.split(r'\t+', string_list[s])
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
def scatter_plot_2groups(string_list, xdata, fnameout, grp1_label, col_id=3, colors=("red", "green"),
                         grp_labels=("control", "experimental")):
    ctrl_y = []
    ctrl_x = []
    exp_y = []
    exp_x = []

    cnt = 0
    for s in range(len(string_list)):
        l = re.split(r'\t+', string_list[s])
        group_ch = l[0][0]
        if group_ch == grp1_label:
            ctrl_y.append(float(l[col_id]))
            ctrl_x.append(float(xdata[cnt]))
        else:
            exp_y.append(float(l[col_id]))
            exp_x.append(float(xdata[cnt]))
        cnt = cnt + 1

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
def scatter_plot_2dataseries(ydata1, xdata1, ydata2, xdata2, fnameout, colors=("red", "green"),
                             grp_labels=("control", "experimental")):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)  # , axisbg="1.0")

    ax.scatter(xdata1, ydata1, alpha=0.8, c=colors[0], edgecolors='none', s=30, label=grp_labels[0])
    ax.scatter(xdata2, ydata2, alpha=0.8, c=colors[1], edgecolors='none', s=30, label=grp_labels[1])

    plt.title(os.path.basename(fnameout))
    plt.legend(loc=4)
    plt.show()

    plt.savefig(fnameout, dpi=1200)
    plt.close()


# on the X-axis goes a the order with the list (like an histogram, to separate two groups
def scatter_plot_dataserie(ydata, xdata, fnameout, color="red", label="control", show=False):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)  # , axisbg="1.0")

    ax.scatter(xdata, ydata, alpha=0.8, c=color, edgecolors='none', s=30, label=label)

    plt.title(os.path.basename(fnameout))
    plt.legend(loc=4)

    if show:
        plt.show()

    if len(fnameout) > 0:
        plt.savefig(fnameout, dpi=1200)

    plt.close()
