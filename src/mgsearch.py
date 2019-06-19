#!/usr/bin/python

import re2
import os
import sys
import time
from multiprocessing import Process, Pool, Manager


def pool_multiproc(query, nprocs=4):
    """ requires reading/gathering all directories at once"""
    p = Pool(processes=nprocs)

    # Using file to pass files name to grep
    with open("file_names.txt", "r") as fn:
        file_names = fn.readlines()
    # =====================================

    res = p.map(worker, [(query, f) for f in file_names])
    print("=== Number of hits: {} ===".format(sum(res)))


def worker(data):
    query, file_name = data
    query_re = re2.compile(query, re2.MULTILINE)
    regex_hits = 0

    with open(file_name.strip('\n'), "r") as file_handle:
        for res_q in query_re.finditer(file_handle.read()):
            print("{}: {}".format(file_name.strip('\n'), res_q.group()))
            regex_hits += 1

    # print("=== Number of hits: {} ===".format(regex_hits))
    return regex_hits


def mgsearch(query):
    query_re = re2.compile(query, re2.MULTILINE)

    file_list = open("file_names.txt", "r")
    regex_hits = 0

    for file_name in file_list:
        with open(file_name.strip('\n'), "r") as file_handle:
            for res_q in query_re.finditer(file_handle.read()):
                print("{}: {}".format(file_name.strip('\n'), res_q.group()))
                regex_hits += 1
    file_list.close()
    print("=== Number of hits: {} ===".format(regex_hits))


def main():
    """ Handles passing of args to function """
    query_arg = sys.argv[1]
    print(sys.argv)
    # mgsearch(query=query_arg)
    # =====================================
    pool_multiproc(query_arg, nprocs=4)


if __name__ == '__main__':
    main()
