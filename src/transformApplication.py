#!/usr/bin/python
from subprocess import Popen, PIPE, STDOUT
import sys
from os.path import join, basename
import os
import json
from shutil import copyfile, copy2, rmtree


def compile_transformed_files(repo_loc, make_file_loc):
    nul = open(os.devnull, 'w')

    p = Popen(["make", "-f", make_file_loc, "-C",
               repo_loc], stdout=None, stderr=None)
    p.wait()

    nul.close()


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
    p = Popen(command_c, stdout=nul, stderr=None)
    p.wait()

    print("Compilation return code: {}".format(p.returncode))
    if p.returncode == 0:
        succ_comps += 1

    nul.close()


def apply_transformation(transform_tool, input_f, output_f):
    nul = open(os.devnull, 'w')
    # print("tool: {}\ninput: {}\nouput: {}".format(' '.join(transform_tool), input_f, output_f))
    # print(' '.join(transform_tool))

    p = Popen(transform_tool, stdout=nul, stderr=None)
    p.wait()
    print("Transformation return code: {}".format(p.returncode))

    nul.close()


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


def transform_files(transform_tool, repo_dir="repos", results_dict={}, copy_req=True):

    global succ_comps
    succ_comps = 0
    total_number = 0

    # get index placements for args
    input_index, output_index = get_input_output_loc(transform_tool)

    # get results
    for repo_name, file_list in results_dict.iteritems():
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

        # add includes to clang command
        transform_tool.extend(include_list)

        for file_n in file_list:
            # transform file
            file_path = join(repo_loc, file_n)
            out_file = join(build_path, basename(file_n))
            total_number += 1

            print("\n=====Process File======")
            print(file_path)

            # clang-tidy -checks='modernize-loop-convert' file.in -- -std=c++11
            if copy_req:
                copyfile(file_path, out_file)
                file_path = out_file

            # what if tool requires -I arguements to work
            # clang could be used on set of files at once but not all tools could do this
            # transform_tool = alter_tool_args(transform_tool, file_path, out_file)
            set_in_out_args(transform_tool, input_f=file_path, output_f=out_file,
                            in_index=input_index, out_index=output_index)

            apply_transformation(
                transform_tool, input_f=file_path, output_f=out_file)
            # print("Transformation Complete")

            #  here
            # print("Compilation Started")
            compile_transformed(repo_loc, include_list,
                                input_f=file_path, output_f=out_file)

    print("TOTAL SUCCESSFUL COMPILATIONS: {}/{}".format(succ_comps, total_number))
    # all files done now compile directory
    # compile_transformed_files(repo_loc, make_file_loc="~/Project/Code-Grep/Makefile")


def main():
    # get list of files to transform
        # file path ?
        # repo and file paths that were hits ?
    # take tool and args to be executed i.e clang
    # collect objs and code for files in repo that were transformed in a dir in repo
    # wait until search completes ?
    # direct use of gcc to compile :-)

    with open("results.json", "r") as query_results:
        results_dict = json.load(query_results)

    repo_dir = "repos"

    #  How to know where to place args in command
    try:
        if sys.argv[1] == "clean":
            remove_transform_dir(repo_dir="repos", results_dict=results_dict)
            return
    except IndexError:
        pass

    transform_files(
        transform_tool=[
            "clang-tidy", "-checks='modernize-loop-convert'", 'input', "--", "-std=c++14"],
        repo_dir=repo_dir, results_dict=results_dict)


if __name__ == '__main__':
    main()
