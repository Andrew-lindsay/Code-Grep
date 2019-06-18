#!/usr/bin/python

from github import Github
import os
from multiprocessing import Process, Pool
import subprocess
import json

# utilise codesearch backend ? to make index
# ratelimiting so have to wait when they happen


def github_pull(token="", depth=1, dir="repos", repo_name=""):
    # g = Github(token)
    base_url = "https://github.com/"
    flags = "--depth " + str(depth)
    repo_name = repo_name.strip('\n')
    # set git auth variable (if required)
    repo_url = base_url + repo_name + ".git"

    # for proc_num in range(0, num_cores):
    print("Repo url: {}".format(repo_url))
    # args =["git clone", repo_url, flags, os.path.join(dir, repo_name)]
    command = ' '.join(["git clone", repo_url, flags,
                        os.path.join(dir, repo_name)])
    print(command)
    # subprocess.call(["git", "clone", repo_url, flags, os.path.join(dir, repo_name)],shell=True)
    # subprocess.Popen(["git", "clone","https://github.com/Tasssadar/Lorris.git", "repos/Tasssadar/Lorris"])
    subp = subprocess.Popen(
        ["git", "clone", "--depth", str(depth), repo_url, os.path.join(dir, repo_name)])
    subp.wait()


def git_pull_small(name):
    github_pull(repo_name=name)


def pool_git_clone(num_of_proc):
    # create pool of processes and list of reposistories names map them
    # or use a queue of work which is queue of repo names
    pp = Pool(num_of_proc)
    repo_list = open("repo_list.txt", "r")
    repo_names = repo_list.readlines()
    repo_list.close()
    # print(repo_names)
    pp.map(git_pull_small, repo_names)
    print("===== FINISHED =====")
    build_config_file(directory="repos")


def parallel_git_clone(num_cores):

    proc_list = [None] * num_cores

    # open file with repo list
    with open("repo_list.txt", "r") as repo_list:
        # while file not empty
        procs_running = 0
        repo = "-1"
        while repo != "":
            for proc_num in range(0, num_cores):
                repo = repo_list.readline()
                if repo == "":  # end of file
                    break
                proc_list[proc_num] = Process(target=github_pull,
                                              args=("", 1, "repos", repo.strip('\n'),))
                proc_list[proc_num].start()
                procs_running += 1

            for proc_idx in range(procs_running):
                proc_list[proc_idx].join()
            procs_running = 0
    print("===== FINISHED =====")


def repository_entry(name, direc):
    entry = {
        "name": name,
        "path": "{}/{}".format(direc, name),
        "revisions": ["HEAD"],
        "metadata": {
            "github": name
        }
    }
    return entry


def build_config_file(directory="repos", repo_file="repo_list.txt"):
    """ Construction json config file for list of repositories that are to be indexed"""
    config = {"name": "gitub-grep", "repositories": []}

    with open(repo_file, "r") as repo_list:
        for repo in repo_list:
            config["repositories"].append(repository_entry(repo.strip('\n'), directory))

    with open("index.json", "w") as config_json:
        json.dump(config, fp=config_json, indent=4)
    print("==== Config File: index.json created ====")

def main():
    pool_git_clone(num_of_proc=8)
    # parallel_git_clone(num_cores=4)
    # github_pull(token="", depth=1, dir="repos", repo_name="zj463261929/TextBoxes")


if __name__ == '__main__':
    main()
