#!/usr/bin/python

# minimal implementation of mutiline grep
import grpc
import livegrep_pb2
import livegrep_pb2_grpc
import os

def server_call(query="", mutiline_quety="", matches_limit=50):
    dir_loc = os.path.join(os.path.expanduser("~"),"Project/Code-grep/repo_pull_test8/repos")
    with grpc.insecure_channel('localhost:9999') as channel:
        stub = livegrep_pb2_grpc.CodeSearchStub(channel)
        response = stub.Search(livegrep_pb2.Query(
            line=query, max_matches=matches_limit))
        # what is the response object can it be turned directly to json or python dict object
        # print(type(response))
        # print(response)
        for item in response.results:
            print("Path: {}/{}, line: {}".format(item.tree, item.path, item.line_number))
  
  
def repos_returned():
    pass


def main():
    server_call(query="std::.*::iterator")


if __name__ == '__main__':
    main()