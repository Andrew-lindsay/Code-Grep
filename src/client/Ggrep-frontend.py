#!/usr/bin/python

# minimal implementation of mutiline grep
import grpc
import livegrep_pb2
import livegrep_pb2_grpc
import os
from os.path import join
import re2
import pprint
# import sys


def goto_line_in_file(file_loc, line):
    """ Returns location in file """
    file_handle = open(file_loc, "r")
    for num in xrange(line):
        file_handle.readline()
    return file_handle


def print_results(response):
    for item in response.results:
        print("{}/{}:{} {}".format(
            item.tree.encode('ascii', 'ignore')
            , item.path.encode('ascii', 'ignore')
            , item.line_number
            , item.line))

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

# parallelise, search of files
def mgrep_in_files(multiline_query, cs_response):
    """ Gather interesting files from initial response and grep them for results"""    

    dir_loc = os.path.join(os.path.expanduser(
        "~"), "Projects/test-env/repos")

    query_re = re2.compile(multiline_query, re2.M)  # [^;] matches newlines

    # file_name_path : hits in initial search
    files_of_interest = {}
    regex_hits = 0

    for item in cs_response.results:
        id_f = join(item.tree, item.path)

        if id_f in files_of_interest:
            files_of_interest[id_f] += 1
        else:
            files_of_interest[id_f] = 1

            file_loc = join(dir_loc, id_f)

            with open(file_loc, "r") as file_handle:
                # res_q = query_re.finditer(file_handle.read())
                # print(res_q)
                for res_q in query_re.finditer(file_handle.read()):
                    print("{}: {}".format(id_f, res_q.group()))
                    regex_hits += 1

    print("=== Number of responses: {} ===".format(regex_hits))
    # pprint.pprint(files_of_interest)


def mgrep(multiline_query, cs_response):
    """ preforms multiline grep over all files returned from initial search"""
    # dir_loc = os.path.join(os.path.expanduser(
    #   "~"), "Projects/Code-Grep/repo_pull_test9/repos")

    dir_loc = os.path.join(os.path.expanduser(
        "~"), "Projects/test-env/repos")

    query_re = re2.compile(multiline_query, re2.M)  # [^;] matches newlines

    for item in cs_response.results:
        print("{}/{}:{} {}".format(
            item.tree.encode('ascii', 'ignore')
            , item.path.encode('ascii', 'ignore')
            , item.line_number
            , item.line))

        line_num = item.line_number
        file_loc = join(dir_loc, join(item.tree, item.path))

        # go to pecific line of filetr.partition(sep)
        # is required ?
        file_data = goto_line_in_file(
            file_loc, line_num - 1)  # at correct line

        # could start query at beginning of line to stop having to uses the scan method of search

        # print("\t at line: {}".format(file_data.readline()))
        # matches only next possible match to multi grep
        # could be a completely diff match or a repeat of a past match
        match_object = query_re.search(file_data.read())

        if match_object is not None:
            print("Matched: {}".format(match_object.group()))
        else:
            print("No Match")
        file_data.close()


def prepocess_query(query_str):
    # complete list of meta characters. ^ $ * + ? { } [ ] \ | ( )
    # \number \A \B \b \D \d \S \s \W \w \Z
    # standard escapes
    # what about \n|^|$ at start of line (no query)
    # being of query \n stops codesearch functioning
    # special characters $|\n|^|.|*|()|
    codesearch_query = query_str
    if "\\n" in query_str or '$' in query_str or '^' in query_str:
        print("Query is multiline")
        codesearch_query = query_str

    return (codesearch_query, query_str)


def g_grep(query="", multiline_q="", matches_limit=50):

    # does query need pre-processing before being passed to codesearch server
    query_s, m_query = prepocess_query(query)

    res_response = server_call(query_s, matches_limit=matches_limit)
    print("=== initial search done ===")

    # save initial results
    # print_results(response=res_response)

    print("=== Number of responses: {} ===".format(len(list(res_response.results))))

    # see if multiline query can be build from query
    # i.e does query include multiline characters
    multiline_q = multiline_q if multiline_q != "" else m_query

    # results = mgrep(multiline_q, res_response)
    mgrep_in_files(multiline_q, res_response)
    # save results/ output


def main():
    # handle args and other stuff here
    g_grep(query=r"int",
           multiline_q=r"int", matches_limit=10000)


if __name__ == '__main__':
    main()
