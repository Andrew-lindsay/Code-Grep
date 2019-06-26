#!/usr/bin/python2

import sqlite3
from sqlite3 import Error


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

    def close_db(self):
        self.conn.close()

    def insert_repo(self, repo_tuple):
        self.curs.execute(self.repo_insert, repo_tuple)
        self.conn.commit()

    def insert_many_repos(self, repo_generator):
        self.curs.executemany(self.repo_insert, repo_generator)
        self.conn.commit()

    def list_repositories(self):
        sql = ''' SELECT name FROM repositories'''
        results = self.curs.execute(sql)
        return map(lambda item: item[0], results)
        # for x in results:
        #     yield x[0]

    def search_db(self, stars=">0", size=">0", language=None):
        """ Returns a list of repositories """
        search_clauses = []
        stars = "stars" + str(stars)
        search_clauses.append(stars)

        if language is not None:
            language = "language=\"{}\"".format(language)
            search_clauses.append(language)

        size = "size" + size
        search_clauses.append(size) 

        search_options = ' AND '.join(search_clauses)

        sql = "SELECT * FROM repositories WHERE {};".format(search_options)
        print(sql)
        results = self.curs.execute(sql)
        # return map(lambda item: item[0], results)
        return results


def main():
    repo_db = RepoDatabase(db_name="test_repos.db")
    results = repo_db.search_db(stars=">5", language="C", size=">400")

    for item in results:
        print(item)


if __name__ == '__main__':
    main()