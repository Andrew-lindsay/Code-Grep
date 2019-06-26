#!/usr/bin/python2

from github import Github
from time import sleep
import math
import sys
import argparse
from repositorydb import RepoDatabase
from repository_cloner import RepoCloner


def fetch_all_query_results(query_str):
    """ """
    # Auth token github obj
    g = Github("87fbbf6e4d5bbb3cec34970f06c85b097d1cb68f", per_page=100)
    print("Items per Page: {}".format(g.per_page))

    if g.get_rate_limit().search.remaining == 0:
        print("All search requested used up please wait 61s")
        sleep(61)

    res = g.search_repositories(query=query_str)

    # repo_res_list = open("repo_res_list.txt", "a")

    print("Number of requests left: {}/{}"
          .format(g.get_rate_limit().search.remaining, g.get_rate_limit().search.limit))
    print("Total Count: {},  for query: {}".format(res.totalCount, query_str))

    num_of_pages = math.ceil(float(res.totalCount) / g.per_page)
    print("Pages: {}".format(num_of_pages))

    results = []
    i = 0
    while not i == num_of_pages:
        if g.get_rate_limit().search.remaining == 0:
            # # DEBUG
            print("Number of requests left: {}/30"
                  .format(g.get_rate_limit().search.remaining))
            print("SLEEPING; Time left until reset: {}s".format(61))
            sleep(61)

            # DEBUG
            print("Number of requests left: {}/30"
                  .format(g.get_rate_limit().search.remaining))

        # for repo_obj in res.get_page(i):
        #     yield (repo_obj.full_name, repo_obj.stargazers_count, repo_obj.size, repo_obj.language)

        # res_page = map(lambda repo_obj: (repo_obj.full_name, repo_obj.stargazers_count,
        #                                  repo_obj.size, repo_obj.language), res.get_page(i))

        results.extend(res.get_page(i))
        i += 1

    print("Number of requests left: {}/{}"
          .format(g.get_rate_limit().search.remaining, g.get_rate_limit().search.limit))
    print("FINISHED")
    return results


def submit_query(languages, star_list=[100], star_range=None):
    if star_range is not None:
        star_list = xrange(star_range[0], star_range[0] + star_range[1])

    lang_flag = ""
    if languages is not None:
        lang_flag = ' '.join(map(lambda x: "language:" + x, languages))

    # print(lang_flag)
    for star in star_list:
        yield fetch_all_query_results(query_str="{} stars:{}".format(lang_flag, star))


def build_database(database, languages, star_list=[100], star_range=None, clone_repos=False):
    # create database if it does not already exist
    repo_db = RepoDatabase(database)

    for result in submit_query(languages, star_list, star_range):
        result_processed = map(lambda repo_obj: (repo_obj.full_name, repo_obj.stargazers_count,
                                                 repo_obj.size, repo_obj.language), result)
        repo_db.insert_many_repos(result_processed)

    if clone_repos == True:
        repo_cloner = RepoCloner(directory="repos")
        repo_cloner.clone_repositories(db=repo_db)

    repo_db.close_db()


def build_file(file_name, languages, star_list=[100], star_range=None, clone_repos=False):
    """ Creates file to store output of a
        Github search query over reposistories """

    results = []
    for result in submit_query(languages, star_list, star_range):
        results_processed = map(lambda repo_obj: repo_obj.full_name, result)
        results.extend(results_processed)

    unique_res = set(results)
    with open(file_name, 'w') as repo_name_file:
        for repo_name in unique_res:
            repo_name_file.write(repo_name + '\n')

    if clone_repos == True:
        repo_cloner = RepoCloner(directory="repos")
        repo_cloner.clone_repositories(fd=file_name)


def print_query_result(languages, star_list, star_range):
    """ """
    results = []
    for result in submit_query(languages, star_list, star_range):
        results_processed = map(lambda repo_obj: repo_obj.full_name, result)
        results.extend(results_processed)

    unique_res = set(results)

    for repo_name in unique_res:
        sys.stdout.write(repo_name + '\n')


def get_args():
    args = argparse.ArgumentParser(prog="Github-Repo-puller",)
    args.add_argument('--languages', '-l', help='',
                      action='store', nargs='+', type=str, required=True)
    args.add_argument('--star_list', '-sl', help='',
                      action='store', type=int, nargs='+', default=[100])
    args.add_argument('--star_range', '-sr', help='',
                      action='store', type=int)
    args.add_argument('--db_name', '-db', help='',
                      action='store', type=str)
    args.add_argument('--file', '-f', help='',
                      action='store', type=str)
    args.add_argument('--clone_repos', '-cl', help='',
                      action='store_true', default=False)
    x = args.parse_args()
    return (x.languages, x.star_list, x.star_range, x.db_name, x.file, x.clone_repos)


def main():
    (languages, star_list, star_range, db_name, file_name, clone_repos) = get_args()

    print((languages, star_list, star_range, db_name))

    if db_name is not None:
        build_database(db_name, languages, star_list, star_range, clone_repos)
    elif file_name is not None:
        build_file(file_name, languages, star_list, star_range, clone_repos)
    else:
        print_query_result(languages, star_list, star_range)


if __name__ == '__main__':
    main()
