#!/usr/bin/python2

import os
from multiprocessing import Process, Manager
import subprocess
import argparse
import itertools
from repositorydb import RepoDatabase
# utilise codesearch backend ? to make index
# ratelimiting so have to wait when they happen


class RepoCloner():
    """docstring for RepoCloner"""

    def __init__(self, directory="repos", nprocs=4, depth=1):
        self.directory = directory
        self.manager = Manager()
        self.nprocs = nprocs
        self.queue = self.manager.Queue(nprocs)
        self.pool = []

    def _start_procs(self):
        for _ in xrange(self.nprocs):
            p = Process(target=self.github_clone, args=(self.queue, self.directory))
            self.pool.append(p)
            p.start()

    def _join_procs(self):
        for p in self.pool:
            p.join()

    def _kill_procs(self):
        for p in self.pool:
            p.terminate()

    @staticmethod
    def github_clone(repo_queue, directory, depth=1):
        while True:
            # check if repo already exists in directory ?
            repo_name = repo_queue.get()
            if repo_name is None:
                break

            base_url = "https://github.com/"

            # set git auth variable (if required)
            repo_url = base_url + repo_name + ".git"

            command = "git clone {} --depth {} {}".format(
                repo_url, depth, os.path.join(directory, repo_name))
            print(command)

            # subprocess.Popen(["git", "clone","https://github.com/Tasssadar/Lorris.git", "repos/Tasssadar/Lorris"])
            subp = subprocess.Popen(
                ["git", "clone", "--depth", str(depth), repo_url, os.path.join(directory, repo_name)])
            subp.wait()
        print("Thats all folks")

    def _get_data_from_db(self, db):
        repo_list = db.list_repositories()
        # None indicates to workers there is no more tasks
        iters = itertools.chain(repo_list, (None,)* self.nprocs)
        for repo in iters:
            self.queue.put(repo)

    def _get_data_from_file(self, fd):
        with open(fd, 'r') as repo_list:
            iters = itertools.chain(repo_list, (None,) * self.nprocs)
            for repo in iters:
                print(repo)
                self.queue.put(repo.strip('\n'))

    def clone_repositories(self, db=None, fd=None):

        self._start_procs()
        if db is not None:
            self._get_data_from_db(db)
        elif fd is not None:
            self._get_data_from_file(fd)
        else:
            self._kill_procs()

        self._join_procs()


def get_args():
    args = argparse.ArgumentParser()
    args.add_argument('--file', '-f', help='', action='store', type=str)
    args.add_argument('--database', '-db', help='', action='store', type=str)
    args.add_argument('--directory', '-d', help='',
                      action='store', type=str, default="repos")
    args.add_argument('--nprocs', '-np', help='', action='store', type=int)
    x = args.parse_args()
    return (x.file, x.database, x.directory, x.nprocs)


def main():
    (file_h, database, directory, nprocs) = get_args()

    repo_cloner = RepoCloner(nprocs=nprocs, directory=directory)

    if file_h is not None:
        repo_cloner.clone_repositories(fd=file_h)

    elif database is not None:
        repo_db = RepoDatabase(db_name=database)
        repo_cloner.clone_repositories(db=repo_db)
    else:
        print("ERROR: must pass either a file or a database")


if __name__ == '__main__':
    main()
