#!/usr/bin/python2

from github import Github
from time import sleep
import math
import sys
import argparse
import os
from repositorydb import RepoDatabase
from repository_cloner import RepoCloner


def fetch_all_query_results(query_str):
    """
    Collects all paged results from query of github repositories
    maximum number returned by a query is 100 results per page for
    10 pages. So 1000 results per query max.

    Args:
        query_str (str): String to be passed to github search_repositories API
            e.g "language:c language:c++ stars:10"

    Returns:
        A list of github repository objects include metadata about repository
        name, size, main language
    """

    # Auth token github obj

    auth_file_path = os.path.normpath(os.path.join(
        os.path.expanduser("~"), ".code_grep/token.txt"))

    if os.path.isfile(auth_file_path):
        with open(auth_file_path, "r") as token_file:
            auth_token = token_file.readline().strip()
        # add more validation checks
        g = Github(auth_token, per_page=100)
        print("SUCCESS: Github auth token in use")
    else:
        print("ALERT: No authenication token used number of requests will be limited")
        g = Github(per_page=100)

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

        results.extend(res.get_page(i))
        i += 1

    print("Number of requests left: {}/{}"
          .format(g.get_rate_limit().search.remaining, g.get_rate_limit().search.limit))
    print("FINISHED")
    return results


def submit_query(languages, star_list=[100], star_range=None):
    """ Creates the query string using the languages args and varying star value
        e.g iter 1 "language:c language:c++ stars:10"
            itet 2 "language:c language:c++ stars:11"

    Args:
        languages (list): list of strings denoting programming lanuages
        star_list (list): A list of integer values representing number of github stars

    Yields:
        A list of GitHub repository objects for star value passed in star_list
    """

    if star_range is not None:
        star_list = xrange(star_range[0], star_range[0] + star_range[1])

    lang_flag = ""
    if languages is not None:
        lang_flag = ' '.join(map(lambda x: "language:" + x, languages))

    # print(lang_flag)
    for star in star_list:
        yield fetch_all_query_results(query_str="{} stars:{}".format(lang_flag, star))


def build_database(database, languages, star_list=[100], star_range=None, clone_repos="repos", nprocs=4):
    """ Creates a sqlite3 database of Github repos metadata returned from search queries 
        repositories can be optionally clone in to directory from database.

    Args:
        database (str): Name of database to be created
        languages (list): list of programming language names used in query 
        star_list (list): list of github star values used in queries
        clone_repos (str): Name of directory to clone repositories into 
            if None repositories not cloned
        nprocs (int): Number of processes to clone the github repositories with
            only has effect if clone_repos arg not None 

    Returns:
        Nothing returned

    """
    repo_db = RepoDatabase(database, create_db=True)

    for result in submit_query(languages, star_list, star_range):
        result_processed = map(lambda repo_obj: (repo_obj.full_name, repo_obj.stargazers_count,
                                                 repo_obj.size, repo_obj.language), result)
        repo_db.insert_many_repos(result_processed)

    if clone_repos is not None:
        repo_cloner = RepoCloner(directory=clone_repos, nprocs=nprocs)
        repo_cloner.clone_repositories(db=repo_db)

    repo_db.close_db()


def build_file(file_name, languages, star_list=[100], star_range=None, clone_repos="repos", nprocs=4):
    """ Stores the repostitory names returned from the GitGub repository search query into a file
        Repos store in file can be clone into a specified directory.

    Args:
        file_name (str): Name of file storing repostitory names
        languages (list): list of programming language names used in query
        star_list (list): list of github star values used in queries
        clone_repos (str): Name of directory to clone repositories into
            if None repositories not cloned
        nprocs (int): Number of processes to clone the github repositories with
            only has effect if clone_repos arg not None

    Returns:
        Nothing
    """

    results = []
    for result in submit_query(languages, star_list, star_range):
        results_processed = map(lambda repo_obj: repo_obj.full_name, result)
        results.extend(results_processed)

    unique_res = set(results)
    with open(file_name, 'w') as repo_name_file:
        for repo_name in unique_res:
            repo_name_file.write(repo_name + '\n')

    if clone_repos is not None:
        repo_cloner = RepoCloner(directory=clone_repos, nprocs=nprocs)
        repo_cloner.clone_repositories(fd=file_name)


def print_query_result(languages, star_list, star_range):
    """ Prints Repository names returned from GitHub API query to screen

    Args:
        languages (list): list of programming language names used in query
        star_list (list): list of github star values used in queries
    """

    results = []
    for result in submit_query(languages, star_list, star_range):
        results_processed = map(lambda repo_obj: repo_obj.full_name, result)
        results.extend(results_processed)

    unique_res = set(results)

    for repo_name in unique_res:
        sys.stdout.write(repo_name + '\n')


def get_args():
    args = argparse.ArgumentParser(prog="Github-Repo-Builder",)
    args.add_argument('--languages', '-l', help='List of lanauges to be issues in search of github reposistories',
                      action='store', nargs='+', type=str, required=True)
    args.add_argument('--star_list', '-sl', help='List of star values to used to query github database (each star values results in 1000 returned results)',
                      action='store', type=int, nargs='+', default=[100])
    # args.add_argument('--star_range', '-sr', help='Create a list of star values from a range',
    #                   action='store', type=int)
    args.add_argument('--db_name', '-db', help='The Name of the database to store all the metadata relating to the reposistories returned from a query',
                      action='store', type=str)
    args.add_argument('--file', '-f', help='A of the file to output the list of reposistory names to if database name not present',
                      action='store', type=str)
    args.add_argument('--clone_repos', '-cl', help='Specify to directory to download the reposistories from the query either stored in a file or database (no effect if neither are specified)',
                      action='store', default=None)
    args.add_argument('--nprocs', '-np', default=4,
                      help='Number of processes to spawn to clone reposistories in parallel',)
    x = args.parse_args()
    return (x.languages, x.star_list, None, x.db_name, x.file, x.clone_repos, x.nprocs)


def main():
    (languages, star_list, star_range, db_name,
     file_name, clone_repos, nprocs) = get_args()

    print((languages, star_list, star_range, db_name))

    if db_name is not None:
        build_database(db_name, languages, star_list,
                       star_range, clone_repos, nprocs)
    elif file_name is not None:
        build_file(file_name, languages, star_list,
                   star_range, clone_repos, nprocs)
    else:
        print_query_result(languages, star_list, star_range)


if __name__ == '__main__':
    main()
