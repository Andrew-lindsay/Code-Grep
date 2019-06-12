#!/usr/bin/python

# minimal implementation of mutiline grep
import grpc
import livegrep_pb2
import livegrep_pb2_grpc
import os
from os.path import join
import re2
import sys

def goto_line_in_file(file_loc, line):
    """ Returns location in file """
    file_handle = open(file_loc, "r")
    for num in xrange(line):
        file_handle.readline()
    return file_handle

def server_call(query="", multiline_query="", matches_limit=50):
    max_msg_len = 1024 * 1024 * 4  # 4MiB
    dir_loc = os.path.join(os.path.expanduser(
        "~"), "Projects/Code-Grep/repo_pull_test9/repos")
    with grpc.insecure_channel('localhost:9999', options=[('grpc.max_recieve_message_length', max_msg_len)]) as channel:
        stub = livegrep_pb2_grpc.CodeSearchStub(channel)
        response = stub.Search(livegrep_pb2.Query(
            line=query, max_matches=matches_limit))
        # what is the response object can it be turned directly to json or python dict object
        # print(type(response))
        # print(response)
        
    query_re = re2.compile(query if multiline_query == "" else multiline_query, re2.M)
    for item in response.results:
        print("Path: {}/{}, line: {}".format(item.tree,
                                                 item.path, item.line_number))
        print("\tcodeseach: {}".format(item.line))
        line_num = item.line_number
        file_loc = join(dir_loc, join(item.tree, item.path))
        # print(file_loc)
        
        # go to specific line of file
        
        #with open(file_loc, "r") as res_file:
        #    print(res_file.readline())
        file_data = goto_line_in_file(file_loc, line_num-1) # at correct line
        #print("\t at line: {}".format(file_data.readline()))
        match_object = query_re.search(file_data.read())
        
        if match_object is not None:
            print("\tString matched: {}".format(match_object.group()))
        else:
            print("No Match")
        file_data.close()
           
def repos_returned():
    pass


def main():
    server_call(query=r"for\s*\(", multiline_query=r"for\s*\([^;]*;[^;]*;[^\)]*\)\s*{", matches_limit=4)


if __name__ == '__main__':
    main()
