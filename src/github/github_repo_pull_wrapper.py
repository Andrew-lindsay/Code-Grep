#!/usr/bin/python

from os.path import join, expanduser
import os

# livegrep/bazel-bin/cmd/livegrep-github-reindex/linux_amd64_stripped/livegrep-github-reindex
# -codesearch livegrep/bazel-bin/src/tools/codesearch // location of codesearch executable can be symlined to default position
# -http // use http instead of ssh
# -repo jarun/nnn
# -repo borgbackup/borg
# -dir repos
# -depth 1 // set depth of github clone, shallow clone arg
# -out indexed_code.idx


def main():

    livegrep_github_reindex = join(expanduser(
        "~"), "livegrep/bazel-bin/cmd/livegrep-github-reindex/linux_amd64_stripped/livegrep-github-reindex")

    # print(livegrep_github_reindex)

    codesearch_bin = " -codesearch " + join(expanduser(
        "~"), "livegrep/bazel-bin/src/tools/codesearch")

    flags = " -http -dir repos -out indexed_code.idx -depth 1 -github-key 87fbbf6e4d5bbb3cec34970f06c85b097d1cb68f "

    repo_call_str = ""
    with open("repo_list.txt") as repo_list:
        for line in repo_list:
            repo_call_str += "-repo {} ".format(line.strip('\n'))

    print(repo_call_str)
    os.system(livegrep_github_reindex + codesearch_bin + flags + repo_call_str)


if __name__ == "__main__":
    main()
