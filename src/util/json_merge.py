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
        sys.exit(1)

    fp_1 = open(json_file_1, "r")
    fp_2 = open(json_file_2, "r")
    contents_json1 = json.load(fp=fp_1)
    contents_json2 = json.load(fp=fp_2)
    print(len(contents_json1))
    print(len(contents_json2))
    contents_json1['list'].extend(contents_json2['list'])
    # pprint(contents_json1)
    with open("merged.json", "w") as merged_fp:
        json.dump(contents_json1, fp=merged_fp, indent=4)
    fp_1.close()
    fp_2.close()


if __name__ == '__main__':
    main()


# time ag --multiline "for\(\s*[\w_][\w0-9_]*\s+[\w_][\w0-9_]*\s+\=\s+[\d\w]*;\s*[\w_][\w0-9_]*\s*<\s+[\w_][\w0-9_]*;\s*[\w_][\w0-9_]*\+\+\s*\)" repos/ > results/ag_res.txt
# ^C
# real	31m44.821s
# user	0m14.674s
# sys	0m37.224s

# time ag --multiline "for\(\s*[\w_][\w0-9_]*\s+[\w_][\w0-9_]*\s+\=\s+[\d\w]*;\s*[\w_][\w0-9_]*\s*<\s+[\w_][\w0-9_]*;\s*[\w_][\w0-9_]*\+\+\s*\)" repos/ > results/ag_res.txt
# ^C

# real	46m48.193s
# user	0m40.712s
# sys	1m37.880s
