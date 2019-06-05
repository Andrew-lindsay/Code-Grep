#!/usr/bin/python

from os.path import join, expanduser
import os

# livegrep/bazel-bin/cmd/livegrep-github-reindex/linux_amd64_stripped/livegrep-github-reindex
# -codesearch livegrep/bazel-bin/src/tools/codesearch
# -http
# -repo jarun/nnn
# -repo borgbackup/borg
# -dir c_repos
# -out c_repos.idx


def main():

    livegrep_github_reindex = join(expanduser(
        "~"), "livegrep/bazel-bin/cmd/livegrep-github-reindex/linux_amd64_stripped/livegrep-github-reindex")

    print(livegrep_github_reindex)

    codesearch_bin = " -codesearch " + join(expanduser(
        "~"), "livegrep/bazel-bin/src/tools/codesearch")

    flags = " -http -dir c_repos -out c_repos.idx "

    repo_call_str = ""
    with open("repo_list.txt") as repo_list:
        for line in repo_list:
            repo_call_str += "-repo {} ".format(line.strip('\n'))

    print(repo_call_str)
    print(livegrep_github_reindex + codesearch_bin + flags + repo_call_str)


if __name__ == "__main__":
    main()
