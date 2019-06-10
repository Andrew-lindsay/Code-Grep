#!/usr/bin/python

import grpc
import livegrep_pb2
import livegrep_pb2_grpc


def server_call(query="", matches_limit=50):
    with grpc.insecure_channel('localhost:9999') as channel:
        stub = livegrep_pb2_grpc.CodeSearchStub(channel)
        response = stub.Search(livegrep_pb2.Query(
            line=query, max_matches=matches_limit))

        print(type(response))
        print(response)


def repos_returned():
    pass


def main():
    server_call(query="std::.*::iterator")


if __name__ == '__main__':
    main()
