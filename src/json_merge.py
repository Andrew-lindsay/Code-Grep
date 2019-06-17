#!/usr/bin/python

import json
import sys
from pprint import pprint


def main():
    try:
        json_file_1 = sys.argv[1]
        json_file_2 = sys.argv[2]
    except ValueError:
        print("incorrect number of arugements provided")
        print("Usage: json_merge a.json b.json")

    fp_1 = open(json_file_1, "r")
    fp_2 = open(json_file_2, "r")
    contents_json1 = json.load(fp=fp_1)
    contents_json2 = json.load(fp=fp_2)
    contents_json1.update(contents_json2)
    # pprint(contents_json1)
    with open("merged.json", "w") as merged_fp:
        json.dump(contents_json1, fp=merged_fp, indent=4)


if __name__ == '__main__':
    main()
