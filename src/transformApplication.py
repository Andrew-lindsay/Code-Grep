#!/usr/bin/python
from subprocess import Popen, PIPE, STDOUT
import sys
from os.path import join, basename
import os
import json
from shutil import copyfile, copy2, rmtree
import re2
import csv
import difflib
import argparse
import multiprocessing
from pprint import pprint
import itertools 


def get_includes(repo_loc):
    # ["-Idir/include","",""]
    include_list = []
    for (dir_path, dirs, filesnames) in os.walk(repo_loc):
        if '.git' in dirs:  # stop recursing dowm .git directory
            dirs.remove('.git')
        for directory in dirs:
            include_path = "-I" + join(dir_path, directory)
            include_list.append(include_path)

    return include_list


def compile_transformed(repo_loc, include_list, input_f, output_f):
    nul = open(os.devnull, 'w')
    # cpp or c ? includes need to be passed
    # get includes
    #  c and c++ handled here seperately ?
    global succ_comps

    command_c = ["g++-6", "-std=c++17", "-c", input_f, "-o", output_f + ".o"]
    command_c.extend(include_list)
    # print(' '.join(command_c))
    p = Popen(command_c, stdout=nul, stderr=nul)
    p.wait()

    print("Compilation return code: {}".format(p.returncode))
    if p.returncode == 0:
        succ_comps += 1

    nul.close()
    return p.returncode


def apply_transformation(transform_tool, regex_hit_pattern, input_f, output_f):
    nul = open(os.devnull, 'w')
    # print("tool: {}\ninput: {}\nouput: {}".format(' '.join(transform_tool), input_f, output_f))
    # print(' '.join(transform_tool))
    counter = 0

    p = Popen(transform_tool, stdout=PIPE, stderr=None)

    # get number of hits for tranformation
    regex_c = re2.compile(regex_hit_pattern)

    for line in p.stdout:
        # print(line)
        match_p = regex_c.search(line)
        if match_p is not None:
            counter += 1

    p.wait()

    print("Transformation return code: {}".format(p.returncode))
    print("Number of successful transformations: {}".format(counter))
    nul.close()

    return counter if p.returncode == 0 else -1


def get_input_output_loc(transform_tool):
    # could replace with regex; find and replace
    # build proper args for transform
    in_index = -1
    out_index = -1

    try:
        in_index = transform_tool.index('input')
    except ValueError:
        pass

    try:
        out_index = transform_tool.index('output')
    except ValueError:
        pass

    return in_index, out_index


def set_in_out_args(transform_tool, input_f, output_f, in_index, out_index):

    if in_index != -1:
        transform_tool[in_index] = input_f

    if out_index != -1:
        transform_tool[out_index] = output_f


def remove_transform_dir(repo_dir="repos", results_dict={}, copy_req=True):
    # get results
    for repo_name, file_list in results_dict.iteritems():
        repo_loc = join(repo_dir, repo_name)

        # create directory for transformed code
        build_path = join(repo_loc, "build-trans")
        if os.path.isdir(build_path):
            # os.rmdir(build_path)
            rmtree(build_path)
            print("Build directory already exists: {}".format(build_path))


def num_diff_regions(before, after):
    before_f = open(before, "r")
    after_f = open(after, "r")
    counter = 0

    for line in difflib.unified_diff(before_f.readlines(), after_f.readlines(), n=0):
        if line.startswith("@@"):
            counter += 1

    before_f.close()
    after_f.close()

    print("Number of continues changed chunks: {}".format(counter))
    return counter


def transform_worker(file_queue, transform_count_array, proc_id, transform_tool, regex, repo_dir, copy_req=True):

    # setup 

    transform_tool_len = len(transform_tool)
    # get index placements for args
    input_index, output_index = get_input_output_loc(transform_tool)

    csv_results_data = open("out_{}.csv".format(proc_id), "w")
    csv_writer = csv.writer(csv_results_data, delimiter='\t')

    while True:

        repo_name, file_list = file_queue.get()

        if repo_name is None:
            break

        repo_loc = join(repo_dir, repo_name)

        build_path = join(repo_loc, "build-trans")
        print(build_path)
        if os.path.isdir(build_path):
            # os.rmdir(build_path)
            rmtree(build_path)
            print("Build directory already exists")
        os.mkdir(build_path)

        # overkill having all directories
        include_list = get_includes(repo_loc=repo_loc)
        # print(include_list)
        print("here")

        # remove previous includes for clang { code is lookin pretty bad now :( }
        transform_tool = transform_tool[:transform_tool_len]
        # add includes to clang command
        transform_tool.extend(include_list)

        for file_n in file_list:
            file_n = file_n.encode('utf8')
            in_file = join(repo_loc, file_n)
            out_file = join(build_path, basename(file_n))

            print("\n=====Process File======")
            print("file:{}, id:{}".format(in_file, proc_id))

            # clang-tidy -checks='modernize-loop-convert' file.in -- -std=c++11
            if copy_req:
                copyfile(in_file, out_file)
                file_path = out_file
            else:  # clang applies changes in place
                file_path = in_file

            # what if tool requires -I arguements to work
            # clang could be used on set of files at once but not all tools could do this

            set_in_out_args(transform_tool, input_f=file_path, output_f=out_file,
                             in_index=input_index, out_index=output_index)

            print(transform_tool[:transform_tool_len])

            transform_c = apply_transformation(
                 transform_tool, regex, input_f=file_path, output_f=out_file)

            # print("Transformation Complete")

            if transform_c != -1:
                transform_count_array[proc_id] += transform_c

            # #  here
            # # print("Compilation Started")
            comp_return_code = compile_transformed(repo_loc, include_list,
                                                   input_f=file_path, output_f=out_file)

            diff_chunk_count = -1
            if os.path.isfile(out_file):
                diff_chunk_count = num_diff_regions(
                    before=in_file, after=out_file)

            # # parallel writing to a csv will be dangerous use locks ? 
            csv_writer.writerow(
                [repo_name,
                 file_n,
                 diff_chunk_count,
                 transform_c if transform_c != -1 else "FAILURE",
                 "SUCCESSFUL" if comp_return_code == 0 else "FAILURE"])


def _start_procs(queue_repo_w_files, transform_count_arr, transform_tool, regex, repo_dir, nprocs, pool):

    for proc_id in range(nprocs):
        p = multiprocessing.Process(target=transform_worker, args=(queue_repo_w_files, transform_count_arr, proc_id, transform_tool, regex, repo_dir))
        p.start()
        pool.append(p)


def _join_processes(process_pool):

    for p in process_pool:
        p.join()


def transform_files_parallel(transform_tool, regex, output_file="transform_results.csv", repo_dir="repos", results_dict={}, nprocs=4, copy_req=True):
    global succ_comps
    succ_comps = 0
    total_number = 0
    transform_count_arr = multiprocessing.Array('L', nprocs)

    process_pool = []
    queue_repo_w_files = multiprocessing.Queue(nprocs)

    # transform_tool_len = len(transform_tool)

    # get index placements for args
    # input_index, output_index = get_input_output_loc(transform_tool)

    # csv_results_data = open("out_{}.csv".format(proc_id), "w")
    # csv_writer = csv.writer(csv_results_data, delimiter='\t')
    # csv_writer.writerow(
    #     ["Repo Name", "File Name", "Diff chunks", "Transformed", "Compilation"])

    _start_procs(queue_repo_w_files, transform_count_arr, transform_tool, regex, repo_dir, nprocs, process_pool)

    # get results
    for repo_name, file_list in itertools.chain(results_dict.iteritems(), ((None,None),)*nprocs ):
        if repo_name is not None:
            repo_name = repo_name.encode('utf8')

        queue_repo_w_files.put((repo_name, file_list))

    _join_processes(process_pool)

    total = sum(transform_count_arr)

    if os.path.isfile(output_file):
        os.remove(output_file)
    csv_results_data = open(output_file, "a")
    csv_results_data.write('\t'.join(["Repo Name", "File Name", "Diff chunks", "Transformed", "Compilation\n"]))

    for proc_id in range(nprocs):
        part_file = "out_{}.csv".format(proc_id)
        with open(part_file, 'r') as csv_part:
            csv_results_data.write(csv_part.read())
        os.remove(part_file)
    print("\n====== Finished =======")
    print("Total transform count: {}".format(total))



def transform_files(transform_tool, regex, output_file="transform_results.csv", repo_dir="repos", results_dict={}, copy_req=True):

    global succ_comps
    succ_comps = 0
    total_number = 0
    transform_count = 0

    transform_tool_len = len(transform_tool)

    # get index placements for args
    input_index, output_index = get_input_output_loc(transform_tool)

    csv_results_data = open(output_file, "w")
    csv_writer = csv.writer(csv_results_data, delimiter='\t')
    csv_writer.writerow(
        ["Repo Name", "File Name", "Diff chunks", "Transformed", "Compilation"])

    # get results
    for repo_name, file_list in results_dict.iteritems():
        repo_name = repo_name.encode('utf8')
        print(type(repo_name))
        print(file_list)
        repo_loc = join(repo_dir, repo_name)

        # create directory for transformed code
        build_path = join(repo_loc, "build-trans")
        if os.path.isdir(build_path):
            # os.rmdir(build_path)
            rmtree(build_path)
            print("Build directory already exists")
        os.mkdir(build_path)

        # overkill having all directories
        include_list = get_includes(repo_loc=repo_loc)
        # print(include_list)
        print("here")
        # remove previous includes for clang { code is lookin pretty bad now :( }
        transform_tool = transform_tool[:transform_tool_len]
        # add includes to clang command
        transform_tool.extend(include_list)

        # parallelise this loop
        # add shared total array 
        for file_n in file_list:
            file_n = file_n.encode('utf8') 
            # transform file
            in_file = join(repo_loc, file_n)
            out_file = join(build_path, basename(file_n))
            total_number += 1

            print("\n=====Process File======")
            print(in_file)

            # clang-tidy -checks='modernize-loop-convert' file.in -- -std=c++11
            if copy_req:
                copyfile(in_file, out_file)
                file_path = out_file
            else:  # clang applies changes in place
                file_path = in_file

            # what if tool requires -I arguements to work
            # clang could be used on set of files at once but not all tools could do this
            # transform_tool = alter_tool_args(transform_tool, file_path, out_file)
            set_in_out_args(transform_tool, input_f=file_path, output_f=out_file,
                            in_index=input_index, out_index=output_index)

            transform_c = apply_transformation(
                transform_tool, regex, input_f=file_path, output_f=out_file)
            # print("Transformation Complete")

            if transform_c != -1:
                transform_count += transform_c

            #  here
            # print("Compilation Started")
            comp_return_code = compile_transformed(repo_loc, include_list,
                                                   input_f=file_path, output_f=out_file)

            diff_chunk_count = -1
            if os.path.isfile(out_file):
                diff_chunk_count = num_diff_regions(
                    before=in_file, after=out_file)

            # parallel writing to a csv will be dangerous use locks ? 
            csv_writer.writerow(
                [repo_name,
                 file_n,
                 diff_chunk_count,
                 transform_c if transform_c != -1 else "FAILURE",
                 "SUCCESSFUL" if comp_return_code == 0 else "FAILURE"])

    print("TOTAL SUCCESSFUL COMPILATIONS: {}/{}".format(succ_comps, total_number))
    print("TOTAL NUMBER OF TRANSFORMATIONS: {}".format(transform_count))
    # all files done now compile directory
    # compile_transformed_files(repo_loc, make_file_loc="~/Project/Code-Grep/Makefile")


def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        '--directory', '-d', help="directory containing repositories", default="repos")
    arg_parser.add_argument(
        '--tool', '-t', help="The command line tool and its arguements to run", type=str)
    arg_parser.add_argument(
        '--regex', '-r', help="Regex pattern to detect hits in tools standard output", default="", type=str)
    arg_parser.add_argument(
        '--input_file', '-f', help="Json file returned by mgsearch to what files to transform", default="results.json")
    arg_parser.add_argument(
        '--output_csv', '-o', help="Name for csv produced as output", default="transform_results.csv")
    arg_parser.add_argument(
        '--clean', '-cl', action='store_true', default=False,
        help="Remove all build directories in repos specified by input file that were created by this tool, use before issuing a second search query over repositories")

    parsed = arg_parser.parse_args()

    if parsed.clean is False and parsed.tool is None:
        arg_parser.error('Error: Either --clean or --tool must be passed')
        sys.exit(0)

    return parsed.directory, parsed.tool, parsed.regex, parsed.input_file, parsed.output_csv, parsed.clean


def main():
    # get list of files to transform
        # file path ?
        # repo and file paths that were hits ?
    # take tool and args to be executed i.e clang
    # collect objs and code for files in repo that were transformed in a dir in repo
    # wait until search completes ?
    # direct use of gcc to compile :-)

    directory, tool, regex, input_file, output_csv, clean = parse_args()

    with open(input_file, "r") as query_results:
        results_dict = json.load(query_results)

    # pprint(results_dict)

    if clean:
        remove_transform_dir(repo_dir=directory, results_dict=results_dict)
        return

    transform_files_parallel(
        transform_tool=tool.split(" "), regex=regex,
        output_file=output_csv, repo_dir=directory,
        results_dict=results_dict)

    # transform_files(
    #     transform_tool=tool.split(" "), regex=regex,
    #     output_file=output_csv, repo_dir=directory,
    #     results_dict=results_dict)

    # transform_files(
    #     transform_tool=[
    #         "clang-tidy", "-checks=-*,modernize-loop-convert", "--fix-errors", 'input', "--", "-std=c++14"],
    #     regex="modernize-loop-convert",
    #     repo_dir=repo_dir, results_dict=results_dict)


if __name__ == '__main__':
    main()
