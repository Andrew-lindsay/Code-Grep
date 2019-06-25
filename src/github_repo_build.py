#!/usr/bin/python2

from github import Github
from github import GithubException
from github.GithubException import RateLimitExceededException
from time import sleep, time
import math
import sqlite3
from sqlite3 import Error
import argparse

class RepoDatabase():
    """docstring for RepoDatabase"""

    def __init__(self, db_name):
        tb_create = """ CREATE TABLE IF NOT EXISTS repositories (
                        name nvarchar PRIMARY KEY,
                        stars int,
                        size int,
                        language text
                    );"""

        self.conn = sqlite3.connect(db_name)
        self.curs = self.conn.cursor()
        self.curs.execute(tb_create)
        self.repo_insert = ''' INSERT OR IGNORE INTO repositories (name, stars, size, language)
                            VALUES (?,?,?,?)'''

    def insert_repo(self, repo_tuple):
        self.curs.execute(self.repo_insert, repo_tuple)
        self.conn.commit()

    def insert_many_repos(self, repo_generator):
        self.curs.executemany(self.repo_insert, repo_generator)
        self.conn.commit()


def fetch_all_query_results(query_str):
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
        res_page = map(lambda repo_obj: (repo_obj.full_name, repo_obj.stargazers_count,
                                         repo_obj.size, repo_obj.language), res.get_page(i))

        results.extend(res_page)
        i += 1

    print("Number of requests left: {}/{}"
          .format(g.get_rate_limit().search.remaining, g.get_rate_limit().search.limit))
    print("FINISHED")
    return results


def star_trawler(query, number_of_stars, start=0):
    for stars in range(start, start + number_of_stars):
        yield fetch_all_query_results(query_str="language:C++ stars:{}".format(stars))


def build_database(database, languages, star_list=100, star_range=None):
    # create database if it does not already exist
    repo_db = RepoDatabase(database)

    if star_range is not None:
        star_list = xrange(star_range[0], star_range[0] + star_range[1])

    lang_flag = ""
    if languages is not None:
        lang_flag = ' '.join(map(lambda x: "language:" + x, languages))

    print(lang_flag)

    # get repo object

    for star in star_list:
        # could be done with a generator if it would help
        # writes batches of 1000 results to database
        results = fetch_all_query_results(query_str="{} stars:{}".format(lang_flag, star))
        repo_db.insert_many_repos(results)

def get_args():
    args = argparse.ArgumentParser(prog="Github-Repo-puller",)
    args.add_argument('--languages', '-l', help='',
                      action='store', nargs='+', type=str, required=True)
    args.add_argument('--star_list', '-sl', help='', action='store', type=int, nargs='+', default=[100])
    args.add_argument('--star_range', '-sr', help='',
                      action='store', type=int)
    args.add_argument('--db_name', '-db', help='', action='store', type=str, required=True)
    x = args.parse_args()
    return (x.languages, x.star_list, x.star_range, x.db_name)


def main():
    (languages, star_list, star_range, db_name) = get_args()
    print((languages, star_list, star_range, db_name))
    build_database(db_name, languages, star_list, star_range)


if __name__ == '__main__':
    main()
