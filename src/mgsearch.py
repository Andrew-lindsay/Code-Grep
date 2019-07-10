#!/usr/bin/python
import re2
import os
from os.path import join
import sys
import time
from multiprocessing import Process, Pool, Manager, active_children 
import multiprocessing
import itertools
import argparse
import Queue
from collections import defaultdict
import repositorydb
from pprint import pprint


class MgQuery(object):
    """ Modeling a Query over a large set of in a directory structure """

    def __init__(self, query, max_matches, timeout, nprocs=4):
        self.query = query
        self.nprocs = nprocs
        self.max_matches = max_matches
        self.timeout = timeout
        self.file_queue = multiprocessing.Queue(nprocs)  # set max size
        self.results = multiprocessing.Array('i', self.nprocs)  # list of results
        self.pool = []  # processor prologs

    def _join_result_dict(list_of_dict):
        if not len(list_of_dict) > 1:
            return

        merge_dict = list_of_dict[0]

        for repo_dict in list_of_dict[1:]:
            for repo_name, file_list in repo_dict[1:].iteritems():
                merge_dict[repo_name].extend(file_list)
            del repo_dict

        return merge_dict

    @staticmethod
    def process_file_name(file_path, repo_name):
        """ Function removes the start of file path containing
         root to directory """

        len_repo = len(repo_name)

        if not len(file_path) > len(repo_name):
            return ""

        if file_path[len_repo] == '/':
            repo_file_path = file_path[len_repo + 1:]
        else:
            repo_file_path = file_path[len_repo:]

        repo_file_path = repo_file_path.split('/')
        repo_name = join(repo_file_path[0], repo_file_path[1])
        file_path_f = '/'.join(repo_file_path[2:])
        return repo_name, file_path_f

    @staticmethod
    def _search_worker(query, file_names, results, id, repo_dir, time_limit=None, max_matches=None):
        """ Code run for each process of parallel search """
        query_re = re2.compile(query, re2.MULTILINE)
        regex_hits = 0
        out_file = open("res{}.out".format(id), "w")
        start_time = time.time()
        results_info = defaultdict(list)

        # loop until no more data provided in queue or timelimit or max matches met
        while True:

            if time_limit is not None:
                try:
                    tim_l = time_limit - (time.time() - start_time)
                    file_name = file_names.get(timeout=tim_l)
                except (ValueError, Queue.Empty) as e:
                    file_name = None
                    print("Time Waiting on get exceed limit exit: {}".format(e))
            else:
                file_name = file_names.get()

            if time_limit is not None and (time.time() - start_time) > time_limit:
                print("Time limit exceeded: {}".format(time_limit))
                break

            if file_name is None:
                break

            try:
                with open(file_name.strip('\n'), "r") as file_handle:

                    hit_in_file = False

                    for res_q in query_re.finditer(file_handle.read()):
                        # If string is a unicode object,
                        # need to convert it to a unicode-encoded
                        # string object before writing it to a file :(
                        # need way of getting name of repo (enforce use of directory being given where repos are )

                        # format of data to output
                        # [{ repo_name : number of hits,
                        #   list_of_files : ["file1.c", "file2.c" ]
                        # },
                        #  ... ]

                        out_file.write(u"{}: {}\n".format(
                            file_name, res_q.group()).encode('utf8'))

                        regex_hits += 1
                        hit_in_file = True

                    if hit_in_file:
                        repo_name, file_path = MgQuery.process_file_name(
                            file_name, repo_dir)
                        results_info[repo_name].append(file_path)

            except UnicodeDecodeError:
                sys.stderr.write(u"UnicodeDecodeError: " + file_name + u"\n")
            except IOError:
                # some repos have broken symlinks in them, want to avoid them
                sys.stderr.write(
                    "ERROR: broken symlinks {}\n".format(file_name))

            # assuming decrease in search time if needing
            # to push results to shared queue
            if max_matches is not None:
                results[id] = regex_hits
        # clean up
        out_file.close()
        pprint(dict(results_info))
        results[id] = regex_hits

    def _start_procs(self, repo_dir):
        # reset pool ?
        self.pool = []
        for proc_id in xrange(self.nprocs):
            p = Process(target=self._search_worker, args=(
                self.query, self.file_queue, self.results, proc_id, repo_dir, self.timeout, self.max_matches))
            p.start()
            self.pool.append(p)

    def _kill_procs(self):
        for p in self.pool:
            p.terminate()

    def _join_procs(self):
        # wait for child processes
        for p in self.pool:
            # if p.is_alive():
            p.join()
        print("all procs finished")

    def _produce_data(self, pathfile=None, dir_repos=None, dirs_list=None, endings=None, filetypes=None):
        """ File paths added to shared queue for processes to access 
            If a file with paths to files is provided it is used over secified directory
            If no file is provided or path to a directory to search, searches for repo 
            directory in current path """

        if pathfile is not None:
            try:
                fn = open(pathfile, "r")
            except IOError as e:
                sys.stderr.write("ERROR: {}\n".format(e))
                self._kill_procs()
                sys.exit(1)
        else:
            # default search directory is repos
            dir_repos = dir_repos if dir_repos is not None else "repos"
            print(dir_repos)
            fn = self._search_dirs(
                dir_repos, dirs_list, endings=endings, filetypes=filetypes)

        iters = itertools.chain(fn, (None,) * self.nprocs)
        start_time = time.time()

        if self.timeout is not None:
            try:
                for file_name in iters:
                    # time_lim - time taken
                    self.file_queue.put(file_name, timeout=self.timeout -
                                        (time.time() - start_time))
            except (ValueError, Queue.Full) as e:
                sys.stderr.write("Time out reached so break: {}\n".format(e))

        elif self.max_matches is not None:
            # not all items will be comsumed if max_matches set
            while sum(self.results) < self.max_matches:
                # print(sum(results))
                try:
                    self.file_queue.put(next(iters))
                except StopIteration:
                    print("All Files added to work queue")
                    break

            # shutdown all process once max_matches reached
            # chance this blocks forever if already processes stopped
            print("CHILDERN: {}".format(len(active_children()) - 1))
            for _ in range(len(active_children()) - 1):
                self.file_queue.put(None)

        else:
            for file_name in iters:
                self.file_queue.put(file_name)

    def _search_dirs(self, dir_repos, dirs_list, endings=None, filetypes=None):
        """ Recursive search of directories to get file names """
        allowed_file_types = ("")

        if endings is not None:
            allowed_file_types = tuple(endings)
        elif filetypes is not None:
            if filetypes == "cpp":
                allowed_file_types = (".cpp", ".cc", ".C", ".cxx",
                                      ".m", ".hpp", ".hh", ".h", ".h++",
                                      ".H", ".hxx", ".tpp", ".c++")
            elif filetypes == "c":
                allowed_file_types = (".c", ".h")

        print("allowed_file_types: {}".format(allowed_file_types))

        dirs_list_cmp = dirs_list if dirs_list is not None else [dir_repos]

        for dir_path in dirs_list_cmp:
            if os.path.isfile(dir_path):
                sys.stderr.write(
                    "ERROR: directory {} does not exist\n".format(dir_path))
                return

            for (dirpath, dirs, filesnames) in os.walk(dir_repos):
                # could get count for repositories from here
                for file_ in filesnames:
                    if file_.endswith(allowed_file_types):
                        yield join(dirpath, file_)

    def _build_output_file(self, res_file="mg_res.txt"):

        if os.path.isfile(res_file):
            os.remove(res_file)
        final_res_file = open(res_file, "a")

        # combine result files
        for n in xrange(self.nprocs):
            fn = "res{}.out".format(n)
            out_file = open(fn, "r")
            final_res_file.write(out_file.read())
            out_file.close()
            os.remove(fn)  # remove intermediate file

        final_res_file.close()

    def search_files(self, pathfile=None, dir_repos=None, dirs_list=None, endings=None, filetypes=None):

        self._start_procs(dir_repos)

        self._produce_data(pathfile, dir_repos, dirs_list, endings, filetypes)

        self._join_procs()

        self._build_output_file()

        print("=== Number of hits: {} ===".format(sum(self.results)))
# ================================================================================


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
# ===========================================================


def parse_users_args():
    parser = argparse.ArgumentParser(
        "Grep throught set of files defined by file file_names.txt (multiline grep supported through re2 libaray)")
    parser.add_argument('--query', '-q',
                        help='Regular expression to be used in search',
                        action="store", type=str, required=True)
    parser.add_argument('--nprocs', '-np',
                        help='Number of processes to spawn to search in parallel',
                        action="store", type=int, default=4)
    parser.add_argument('--max_matches', '-mm',
                        help='Max number of matches to reach before aborting search',
                        action="store", type=int)
    parser.add_argument('--timeout', '-t',
                        help='Specify the length of time the search should run for before exiting',
                        action="store", type=int)
    parser.add_argument('--directory', '-d',
                        help='Specify the path of directory holding the repositories to search through',
                        action="store", type=unicode)
    parser.add_argument('--pathfile', '-pf',
                        help='file containing paths to files to search', action='store', type=str)
    parser.add_argument('--filetypes', '-ft',
                        help='Specify the type of files to grep through when search a given directory e.g --cpp matches .cpp, .cc, .C, .cxx, .m, .hpp, .hh, .h, .h++, .H, .hxx, .tpp, .c++', action='store', type=str)
    parser.add_argument('--endings', '-e',
                        help='Specify the ending to search for as list of strs e.g -e ".c" ".h" ',
                        nargs='+', action='store', type=str)
    parser.add_argument('--database', '-db',
                        help='Name of database to use for search narrowing queries',
                        action='store', type=str)
    parser.add_argument('--stars', '-s',
                        help='Limit search to repositories within specified limits e.g >10, <5, =9" ',
                        action='store', type=str)
    parser.add_argument('--language', '-l',
                        help='Specify language of repositories to search e.g C, C++, prolog',
                        action='store', type=str)
    parser.add_argument('--size', '-sz',
                        help='Size of repositories to search', action='store', type=str)
    # parser.add_argument('--root_dir', '-rd',
    #                     help='location of the directory containing the collection of repositories', action='store', type=str)

    x = parser.parse_args()
    return (x.query, x.nprocs, x.max_matches, x.timeout,
            x.directory, x.pathfile, x.endings, x.filetypes,
            x.database, x.stars, x.language, x.size)


def main():
    """ Handles passing of args to function """

    (query_arg, nprocs, max_matches, time_limit, dir_repos, pathfile,
     endings, filetypes, database, stars, language, size) = parse_users_args()

    # DEBUG
    print("q: {}, np: {}, mm: {}, t: {}, listdirs: {}, pathfile: {} , endings: {}, types: {}".format(
        query_arg, nprocs, max_matches, time_limit, dir_repos, pathfile, endings, filetypes))

    if time_limit is not None and max_matches is not None:
        print("Cannot set both max_matches and timeout")

    # if database present validate args of stars, language, size
    if database is not None:

        check_query = re2.compile(r"^(<|>|=)\d+$")

        if stars is not None:
            if check_query.match(stars) is None:
                stars = None
                sys.stderr.write("ERROR: Invalid stars search\n")
                return

        if size is not None:
            if check_query.match(size) is None:
                size = None
                sys.stderr.write("ERROR: Invalid size search i.e >10\n")
                return

        if language is not None:
            if re2.match(r"(\w|+|-)+$", language) is None:
                sys.stderr.write(
                    "ERROR: Invalid language search i.e C, CPP, C++\n")
                language = None
                return

        repo_db = repositorydb.RepoDatabase(db_name=database)
        results = repo_db.search_db(
            repo_dir=dir_repos, stars=stars, size=size, language=language)

        mgsearch_query = MgQuery(
            query=query_arg, nprocs=nprocs, timeout=time_limit, max_matches=max_matches)

        # list of repositories from database search are passed as list of directories
        mgsearch_query.search_files(
            pathfile=pathfile, dir_repos=dir_repos, dirs_list=results, endings=endings, filetypes=filetypes)

        repo_db.close_db()

    else:
        mgsearch_query = MgQuery(
            query=query_arg, nprocs=nprocs, timeout=time_limit, max_matches=max_matches)

        mgsearch_query.search_files(
            pathfile=pathfile, dir_repos=dir_repos, dirs_list=None, endings=endings, filetypes=filetypes)


if __name__ == '__main__':
    main()
