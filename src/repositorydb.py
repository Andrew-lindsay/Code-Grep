#!/usr/bin/python2

import sqlite3
from sqlite3 import Error
import os
from os.path import join


class RepoDatabase():
    """docstring for RepoDatabase"""

    def __init__(self, db_name, create_db=False):
        tb_create_repos = """ CREATE TABLE IF NOT EXISTS repositories (
                        name nvarchar PRIMARY KEY,
                        stars int,
                        size int,
                        language text
                    );"""

        tb_create_metadata = """ CREATE TABLE IF NOT EXISTS metadata (
                        database_path nvarchar PRIMARY KEY
                    );"""

        if not os.path.isfile(db_name) and not create_db:
            raise IOError

        self.conn = sqlite3.connect(db_name)
        self.curs = self.conn.cursor()
        self.curs.execute(tb_create_repos)
        self.curs.execute(tb_create_metadata)

        self.repo_insert = ''' INSERT OR IGNORE INTO repositories (name, stars, size, language)
                            VALUES (?,?,?,?)'''

    def close_db(self):
        self.conn.close()

    def insert_repo(self, repo_tuple):
        self.curs.execute(self.repo_insert, repo_tuple)
        self.conn.commit()

    def insert_many_repos(self, repo_generator):
        """ Takes a generator of repo tuples to insert into the """
        self.curs.executemany(self.repo_insert, repo_generator)
        self.conn.commit()

    def list_repositories(self):
        sql = ''' SELECT name FROM repositories;'''
        results = self.curs.execute(sql)
        return map(lambda item: item[0], results)
        # for x in results:
        #     yield x[0]

    def search_db(self, stars=None, size=None, language=None):
        """ Returns a list of repositories """
        search_clauses = []

        if stars is not None:
            stars = "stars" + str(stars)
            search_clauses.append(stars)

        if language is not None:
            language = "language=\"{}\"".format(language)
            search_clauses.append(language)

        if size is not None:
            size = "size" + size
            search_clauses.append(size)

        search_options = ' AND '.join(search_clauses)
        where = "WHERE" if len(search_clauses) > 0 else ""

        sql = "SELECT * FROM repositories {} {};".format(where, search_options)
        results = self.curs.execute(sql)
        print(sql)
        # return map(lambda item: item[0], results)

        # generator getting a set of results from query to try and
        # improve performance
        while True:
            res = results.fetchmany(100)
            if res == []:
                break
            for item in res:
                yield item[0]

        # for res in results:
        #     yield res[0]


def main():
    repo_db = RepoDatabase(db_name="test_repos.db")
    results = repo_db.search_db(stars=None, language=None, size=None)
    for item in results:
        print(item)


if __name__ == '__main__':
    main()
