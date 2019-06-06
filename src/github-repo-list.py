#!/usr/bin/python

from github import Github
from github import GithubException
from github.GithubException import RateLimitExceededException
from time import sleep, time

def generate_repo_list(query_str):
    # Auth token github obj
    g = Github("87fbbf6e4d5bbb3cec34970f06c85b097d1cb68f")
    g.per_page = 100
    print("Items per Page: {}".format(g.per_page))
    res = g.search_repositories(query=query_str)
    repo_res_list = open("repo_res_list.txt", "w")

    print("Number of requests left: {}/{}"
        .format(g.rate_limiting[0], g.rate_limiting[1]))
    print("Total Count: {},  for query: {}".format(res.totalCount, query_str))

    try:
        for res_page in res:
            # print(res_page)
            # if no more requests can be made sleep for 60 seconds required reset time 
            if g.rate_limiting[0] == 0:
                print("Number of requests left: {}/{}"
                    .format(g.rate_limiting[0], g.rate_limiting[1]))
                print("SLEEPING: Rate limiting sucks, Time left: {}s".format(g.rate_limiting_resettime - time()))
                # sleep for require time not hardcoded 60
                sleep(60)
            repo_res_list.write(res_page.full_name + '\n')
            # repo_res_list.flush

    except RateLimitExceededException as e:
        print("GithubException: {}".format(e))
        print("Number of requests left: {}/{}".format(g.rate_limiting[0], g.rate_limiting[1]))

    print("Number of requests left: {}/{}"
        .format(g.rate_limiting[0], g.rate_limiting[1]))


def main():
    generate_repo_list(query_str="language:C stars:10")


if __name__ == '__main__':
    main()
