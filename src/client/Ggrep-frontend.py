#!/usr/bin/python

# minimal implementation of mutiline grep
import grpc
import livegrep_pb2
import livegrep_pb2_grpc
import os
from os.path import join
import re2
# import sys


def goto_line_in_file(file_loc, line):
    """ Returns location in file """
    file_handle = open(file_loc, "r")
    for num in xrange(line):
        file_handle.readline()
    return file_handle


def server_call(query="", matches_limit=50):
    # no effect due to server side
    max_msg_len = 1024 * 1024 * 4  # 4MiB
    # make less

    with grpc.insecure_channel('localhost:9999', options=[('grpc.max_recieve_message_length', max_msg_len),
                                                          ('grpc.max_send_message_length', max_msg_len)]) as channel:
        stub = livegrep_pb2_grpc.CodeSearchStub(channel)
        query_obj = livegrep_pb2.Query(line=query, max_matches=matches_limit)
        setattr(query_obj, 'file', '\.cpp')
        response = stub.Search(query_obj)
        # what is the response object can it be turned
        # directly to json or python dict object
        return response


def mgrep(multiline_query, cs_response):
    """ preforms multiline grep over all files returned from initial search"""
    # dir_loc = os.path.join(os.path.expanduser(
    #   "~"), "Projects/Code-Grep/repo_pull_test9/repos")

    dir_loc = os.path.join(os.path.expanduser(
        "~"), "Projects/test-env/repos")

    query_re = re2.compile(multiline_query, re2.M)

    for item in cs_response.results:
        print("{}/{}, line No: {}".format(
            item.tree.encode('ascii', 'ignore')
            ,item.path.encode('ascii', 'ignore')
            ,item.line_number))

        print(item.line)
        line_num = item.line_number
        file_loc = join(dir_loc, join(item.tree, item.path))
        # print(file_loc)

        # go to specific line of file
        file_data = goto_line_in_file(
            file_loc, line_num - 1)  # at correct line

        # print("\t at line: {}".format(file_data.readline()))
        # matches only next possible match to multi grep
        # could be a completely diff match or a repeat of a past match
        match_object = query_re.search(file_data.read())

        if match_object is not None:
            print("\tString matched: {}".format(match_object.group()))
        else:
            print("No Match")
        file_data.close()


def prepocess_query(query_str):
    codesearch_query = query_str
    return (codesearch_query, query_str)


def g_grep(query="", multiline_q="", matches_limit=50):

    # does query need pre-processing before being passed to codesearch server
    query_s, m_query = prepocess_query(query)

    res_response = server_call(query_s, matches_limit=matches_limit)

    print("=== initial search done ===")
    # save initial results

    # see if multiline query can be build from query
    # i.e does query include multiline characters
    multiline_q = multiline_q if multiline_q != "" else m_query

    results = mgrep(multiline_q, res_response)

    # save results/ output


def main():
    # handle args and other stuff here
    g_grep(query=r"for\s*\(",
           multiline_q=r"for\s*\([^;]*;[^;]*;[^\)]*\)\s*{", matches_limit=4)


if __name__ == '__main__':
    main()
