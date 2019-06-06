#!/usr/bin/python

from github import Github
from github import GithubException
from github.GithubException import RateLimitExceededException
from time import sleep, time
import math


def generate_repo_list(query_str):
    # Auth token github obj
    g = Github("87fbbf6e4d5bbb3cec34970f06c85b097d1cb68f")
    g.per_page = 100
    print("Items per Page: {}".format(g.per_page))
    if g.get_rate_limit().search.remaining == 0:
        print("All search requested used up please wait 61s")
        sleep(61)
    res = g.search_repositories(query=query_str)
    repo_res_list = open("repo_res_list.txt", "w")
    print("Number of requests left: {}/{}"
          .format(g.get_rate_limit().search.remaining, g.get_rate_limit().search.limit))
    print("Total Count: {},  for query: {}".format(res.totalCount, query_str))

    # print(g.get_rate_limit().search.reset)

    num_of_pages = math.ceil(float(res.totalCount) / g.per_page)
    print("Pages: {}".format(num_of_pages))
    i = 0
    while not i == num_of_pages:
        if g.get_rate_limit().search.remaining == 0:
            # # DEBUG
            print("Number of requests left: {}/30"
                .format(g.get_rate_limit().search.remaining))
            # reset_time = g.rate_limiting_resettime - time() + 1
            # reset_time = reset_time if reset_time >= 0 else 1
            print("SLEEPING; Time left until reset: {}s".format(61))
            sleep(61)
            # DEBUG
            print("Number of requests left: {}/30"
                .format(g.get_rate_limit().search.remaining))
        for res_page in res.get_page(i):
            # print(res_page)
            repo_res_list.write(res_page.full_name + '\n')
        i += 1
    print("FINISHED")
    # try:
    #     for res_page in res:
    #         # print(res_page)
    #         # DEBUG
    #         # print("Number of requests left: {}/{}"
    #                 # .format(g.get_rate_limit().search.remaining, g.get_rate_limit().search.limit))
    #         # DEBUG
    #         # print(g.get_rate_limit().search.reset)
    #         # if no more requests can be made sleep for 60 seconds required reset time
    #         if g.get_rate_limit().search.remaining == 0:
    #             print("Number of requests left: {}/{}"
    #                 .format(g.get_rate_limit().search.remaining, g.get_rate_limit().search.limit))
    #             print(g.get_rate_limit().search.reset)
    #             print("SLEEPING: Rate limiting sucks, Time left until reset: {}s".format(g.get_rate_limit().search.reset. - time()))
    #             # sleep for require time not hardcoded 60
    #             sleep(g.rate_limiting_resettime - time() + 4)
    #         repo_res_list.write(res_page.full_name + '\n')
    #         # repo_res_list.flush()

    # except RateLimitExceededException as e:
    #    print("Number of requests left: {}/{}"
    #     .format(g.get_rate_limit().search.remaining, g.get_rate_limit().search.limit))

    print("Number of requests left: {}/{}"
          .format(g.get_rate_limit().search.remaining, g.get_rate_limit().search.limit))

def main():
    generate_repo_list(query_str="language:C stars:10")


if __name__ == '__main__':
    main()
