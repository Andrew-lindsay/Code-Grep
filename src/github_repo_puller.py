#!/usr/bin/python

from github import Github
import os

# utilise codesearch backend ? to make index


def github_pull(token, depth, dir):
    # g = Github(token)
    base_url = "https://github.com/"
    flags = "--depth 1 "

    # set git auth variable (if required)

    # open file with repo list
    with open("repo_list.txt", "r") as repo_list:
        # its the call to git clone that are probably causing
        # ratelimiting so have to wait when they happen
        for repo_name in repo_list:
            repo_url = base_url + repo_name.strip('\n') + ".git"
            print("Repo url: ".format(repo_url))
            os.system(' '.join(["git clone", repo_url, flags, os.path.join(dir, repo_name)]))


def build_config_file():
    """ Construction json config file for list of repositories that are to be indexed"""
    pass


def main():
    github_pull("", depth=1, dir=os.path.join(os.getcwd(), "repos"))


if __name__ == '__main__':
    main()
