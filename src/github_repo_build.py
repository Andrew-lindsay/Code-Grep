#!/usr/bin/env python

from github import Github
from github.GithubException import RateLimitExceededException
from time import sleep
import math
import sys
import argparse
import os
from repositorydb import RepoDatabase
from repository_cloner import RepoCloner


def fetch_all_query_results(query_str, search_type="repo"):
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

    if search_type == "repo":
        res = g.search_repositories(query=query_str)
    else:
        print(query_str)
        res = g.search_code(query=query_str)

    # repo_res_list = open("repo_res_list.txt", "a")

    print("Number of requests left: {}/{}"
          .format(g.get_rate_limit().search.remaining, g.get_rate_limit().search.limit))
    print("Total Count: {},  for query: {}".format(res.totalCount, query_str))

    num_of_pages = math.ceil(float(res.totalCount) / g.per_page)
    print("Pages: {}".format(num_of_pages))

    results = []
    i = 0
    while not i == num_of_pages:
        try:
            results.extend(res.get_page(i))
            i += 1
        except RateLimitExceededException as rate_limit:
            requests_left = g.get_rate_limit().search.remaining
            if requests_left == 0:
                print("Number of requests left: {}/30"
                    .format(requests_left))
            else: 
                print("Abuse limit reached")
            print("SLEEPING; Time left until reset: {}s".format(61))
            sleep(61)

    print("Number of requests left: {}/{}"
          .format(g.get_rate_limit().search.remaining, g.get_rate_limit().search.limit))
    print("FINISHED")
    return results


def submit_query(languages, query_str, star_list=None, star_range=None, search_type="repo"):
    """ Creates the query string using the languages args and varying star value
        e.g iter 1 "language:c language:c++ stars:10"
            itet 2 "language:c language:c++ stars:11"

    Args:
        languages (list): list of strings denoting programming lanuages
        star_list (list): A list of integer values representing number of github stars

    Yields:
        A list of GitHub repository objects for star value passed in star_list
    """

    # add same checking of user input query_str

    lang_flag = ""
    if languages is not None:
        lang_flag = ' '.join(map(lambda x: "language:" + x, languages))

    if star_list is not None:
        for star in star_list:
            yield fetch_all_query_results(query_str="{} {} stars:{}".format(query_str, lang_flag, star),search_type=search_type)
    else:
        yield fetch_all_query_results(query_str="{} {}".format(query_str, lang_flag), search_type=search_type)


def build_database(database, languages, query_str, star_list=None, star_range=None, clone_repos="repos", nprocs=4, search_type="repo"):
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

    for result in submit_query(languages, query_str, star_list, star_range, search_type):

        if search_type != "repo":
            result = map(lambda code_search_obj: code_search_obj.repository, result)

        result_processed = map(lambda repo_obj: (repo_obj.full_name, repo_obj.stargazers_count,
                                      repo_obj.size, repo_obj.language), result)
    
        repo_db.insert_many_repos(result_processed)

    if clone_repos is not None:
        repo_cloner = RepoCloner(directory=clone_repos, nprocs=nprocs)
        repo_cloner.clone_repositories(db=repo_db)

    repo_db.close_db()


def build_file(file_name, languages, query_str, star_list=None, star_range=None, clone_repos="repos", nprocs=4, search_type="repo"):
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
    for result in submit_query(languages, star_list, star_range, search_type):

        if search_type != "repo":
            result = map(lambda code_search_obj: code_search_obj.repository, result)

        results_processed = map(lambda repo_obj: repo_obj.full_name, result)
        results.extend(results_processed)

    unique_res = set(results)
    with open(file_name, 'w') as repo_name_file:
        for repo_name in unique_res:
            repo_name_file.write(repo_name + '\n')

    if clone_repos is not None:
        repo_cloner = RepoCloner(directory=clone_repos, nprocs=nprocs)
        repo_cloner.clone_repositories(fd=file_name)


def print_query_result(languages, query_str, star_list, star_range, search_type="repo"):
    """ Prints Repository names returned from GitHub API query to screen
    
    Args:
        languages (list): list of programming language names used in query
        star_list (list): list of github star values used in queries
    """

    results = []
    for result in submit_query(languages, query_str, star_list, star_range, search_type):

        if search_type != "repo":
            result = map(lambda code_search_obj: code_search_obj.repository, result)

        results_processed = map(lambda repo_obj: repo_obj.full_name, result)
        results.extend(results_processed)

    unique_res = set(results)

    for repo_name in unique_res:
        sys.stdout.write(repo_name + '\n')


def get_args():
    args = argparse.ArgumentParser(prog="Github-Repo-Builder",)
    args.add_argument('--languages', '-l', help='List of lanauges to be issues in search of github reposistories',
                      action='store', nargs='+', type=str, required=False)
    args.add_argument('--star_list', '-sl', help='List of star values to used to query github database (each star values results in 1000 returned results)',
                      action='store', type=int, nargs='+', default=None)
    # args.add_argument('--star_range', '-sr', help='Create a list of star values from a range',
    #                   action='store', type=int)
    args.add_argument('--db_name', '-db', help='The Name of the database to store all the metadata relating to the reposistories returned from a query',
                      action='store', type=str)
    args.add_argument('--file', '-f', help='A of the file to output the list of reposistory names to if database name not present',
                      action='store', type=str)
    args.add_argument('--clone_repos', '-cl', help='Specify to directory to download the reposistories from the query either stored in a file or database (no effect if neither are specified)',
                      action='store', default=None)
    args.add_argument('--nprocs', '-np', default=4, type=int,
                      help='Number of processes to spawn to clone reposistories in parallel')
    args.add_argument('--query_str','-q', default="", type=str, help="extra string information to narrow github search")
    args.add_argument('--code_search', '-cs', default=False, action='store_true', help="searchs for keywords in code instead of the reposistories")
    x = args.parse_args()
    return (x.languages,  x.query_str, x.star_list, None, x.db_name, x.file, x.clone_repos, x.nprocs, x.code_search)


def main():
    (languages,  query_str, star_list, star_range, db_name,
     file_name, clone_repos, nprocs, code_search) = get_args()

    print((languages, query_str, star_list, star_range, db_name, nprocs, code_search))

    if db_name is not None:
        build_database(db_name, languages, query_str, star_list,
                       star_range, clone_repos, nprocs, "code" if code_search else "repo"  )
    elif file_name is not None:
        build_file(file_name, languages, query_str, star_list, 
                   star_range, clone_repos, nprocs, "code" if code_search else "repo")
    else:
        print_query_result(languages, query_str, star_list, star_range, "code" if code_search else "repo" )


if __name__ == '__main__':
    main()
