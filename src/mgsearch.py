#!/usr/bin/python

import re2
import os
import sys
import time
from multiprocessing import Process, Pool, Manager, active_children
import itertools
import Queue
import argparse


# ====================== Process Pool approach ========================
def pool_multiproc(query, nprocs=4):
    """ requires reading/gathering all directories at once"""
    p = Pool(processes=nprocs)

    out_file_name = "mg_res.txt"

    # remove output file if it exists
    if os.path.isfile(out_file_name):
        os.remove(out_file_name)

    # Using file to pass files name to grep
    with open("file_names.txt", "r") as fn:
        file_names = fn.readlines()

    res = p.map(worker, [(query, f) for f in file_names])
    print("=== Number of hits: {} ===".format(sum(res)))


def worker(data):
    query, file_name = data
    query_re = re2.compile(query, re2.MULTILINE)
    regex_hits = 0

    out = open("mg_res.txt", "a")
    with open(file_name.strip('\n'), "r") as file_handle:
        for res_q in query_re.finditer(file_handle.read()):
            # may have to lock file on write with mutex lock
            out.write("{}: {}\n".format(file_name.strip('\n'), res_q.group()))
            # print("{}: {}".format(file_name.strip('\n'), res_q.group()))
            regex_hits += 1

    # print("=== Number of hits: {} ===".format(regex_hits))
    out.close()
    return regex_hits
# =========================================================================


def search_worker(query, file_names, results, id, time_limit=None, max_matches=None):
    """ Code run for each process of parallel search """
    query_re = re2.compile(query, re2.MULTILINE)
    regex_hits = 0
    out_file = open("res{}.out".format(id), "w")
    start_time = time.time()

    # loop until no more data provided in queue or timelimit or max matches met
    while True:

        if time_limit is not None:
            try:
                tim_l = time_limit - (time.time() - start_time)
                file_name = file_names.get(timeout=tim_l)
            except Queue.Empty as e:
                file_name = None
                print("Time Waiting on get exceed limit exit: {}".format(e))
        else:
            file_name = file_names.get()

        if time_limit is not None and (time.time() - start_time) > time_limit:
            print("Time limit exceeded: {}".format(time_limit))
            break

        if file_name is None:
            break

        with open(file_name.strip('\n'), "r") as file_handle:
            for res_q in query_re.finditer(file_handle.read()):
                out_file.write("{}: {}\n".format(
                    file_name.strip('\n'), res_q.group()))
                regex_hits += 1
        # assuming decrease in search time if needing to push results to shared queue 
        if max_matches is not None:
            results[id] = regex_hits

    # clean up
    out_file.close()
    results[id] = regex_hits


def mgsearch_parallel(query, nprocs=4, time_limit=None, max_matches=None):
    # setup shared data structures
    manager = Manager()
    file_queue = manager.Queue(nprocs)  # set max size
    results = manager.list([0] * nprocs)  # list of results
    start_time = time.time()

    # start processes
    pool = []
    for proc_id in xrange(nprocs):
        p = Process(target=search_worker, args=(
            query, file_queue, results, proc_id, time_limit, max_matches))
        p.start()
        pool.append(p)

    # create data: files names to search
    with open("file_names.txt", "r") as fn:
        iters = itertools.chain(fn, (None,) * nprocs)

        if time_limit is not None:
            try:
                for file_name in iters:
                    # time_lim - time taken
                    file_queue.put(file_name, timeout=time_limit -
                                   (time.time() - start_time))
            except (ValueError, Queue.Full) as e:
                print("Time out reached so break: {}".format(e))
        elif max_matches is not None:
            # not all items will be comsumed if max_matches set
            while sum(results) < max_matches:
                # print(sum(results))
                try:
                    file_queue.put(next(iters))
                except StopIteration:
                    print("All Files added to work queue")
                    break

            # shutdown all process once max_matches reached
            # chance this blocks forever if already processes stopped
            print("CHILDERN: {}".format(len(active_children()) - 1))
            for _ in range(len(active_children()) - 1):
                file_queue.put(None)
        else:
            for file_name in iters:
                file_queue.put(file_name)

    # wait for child processes
    for p in pool:
        # if p.is_alive():
        p.join()

    print("all procs finished")

    # remove output file if it exists
    res_file = "mg_res.txt"
    if os.path.isfile(res_file):
        os.remove(res_file)
    final_res_file = open(res_file, "a")

    # combine result files
    for n in xrange(nprocs):
        fn = "res{}.out".format(n)
        out_file = open(fn, "r")
        final_res_file.write(out_file.read())
        out_file.close()
        os.remove(fn)  # remove intermediate file

    final_res_file.close()
    print("=== Number of hits: {} ===".format(sum(results)))


# =============================================================
def mgsearch(query):
    """ Single process approach to multiline grep search"""
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

    parser = argparse.ArgumentParser(
        "Grep throught set of files defined by file file_names.txt (multiline grep supported through re2 libaray)")
    parser.add_argument('--query', '-q', 
        help='Regular expression to be used in search',
         action="store", type=str, required=True)
    parser.add_argument('--nprocs', '-np', 
        help='Number of processes to spawn to search in parallel',
         action="store", type=int)
    parser.add_argument('--max_matches', '-mm',
        help='Max number of matches before',
        action="store", type=int)
    parser.add_argument('--timeout', '-t',
        help='Specify the length of time the search should run fro before exiting',
        action="store", type=int)

    x = parser.parse_args()
    query_arg = x.query
    nprocs = x.nprocs
    max_matches = x.max_matches
    time_limit = x.timeout

    print("q: {}, np: {}, mm: {}, t: {}".format(
        query_arg, nprocs, max_matches, time_limit))

    nprocs = 4 if nprocs is None else nprocs

    if time_limit is not None and max_matches is not None:
        print("Cannot set both max_matches and timeout")

    # print(sys.argv)
    # mgsearch_parallel(nprocs=4, query=query_arg,
    #                   time_limit=float(t_lim), max_matches=int(mm))

    mgsearch_parallel(nprocs=nprocs, query=query_arg,
                      time_limit=time_limit, max_matches=max_matches)
    # =====================================
    # mgsearch(query=query_arg)
    # =====================================
    # pool_multiproc(query_arg, nprocs=4)


if __name__ == '__main__':
    main()
