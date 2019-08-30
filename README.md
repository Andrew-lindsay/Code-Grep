# Code-Grep

Code-Grep is a set of comand-line programmes that together build a pipeline. This pipeline can be used to search for patterns in source code files hosted on GithHub and apply code transformation tools to those files identified.

#### Table of contents
+ Programmes
	+ [github_build_repos](#github_build_repos)
	+ [mgsearch](#mgsearch)
	+ [transformApplication](#transformapplication)
+ [Install instructions](#installation-instructions)

<!-- ## Pipeline -->

## github_build_repos
Takes set of programming language names and set of stars values and searches repositories on GitHub that match those cirterion. 

The list of names returned by the search are output to the terminal by default, can be saved to a file with \-\-file FILENAME flag. The search output can be saved to a database (sqlite3 file) with \-\-db_name NAME flag. The database will included name of repo, number of stars, size of repo and associated language. 

To download the repostiories so they can be search with *mgsearch*, use \-\-clone_repos	DIRECTORY_NAME flag, specifying directory name to store downloaded repositories in to. 

Notes:

- The GitHub api will only return a maximum of 1000 results for any query, if more repostiories are needed altering the query by the number of stars a repository will allow more to be returned.
- If the same database file name is provide for multiple search queries results are added to the existing database file.
- The number of processes to use for cloning git repositories can be specified with *\-\-nprocs* INT flag. 
- Like all the tools help information can be accessed with *\-h* or *\-\-help* command line flags.

#### Example:

```bash
./github_repo_build.py --languages c cpp --star_list 100 101 --db_name repositories.db --clone_repos repos 
```

Command above searches github for repostories with majority language *c* or *c++* which have *100* stars then *101* stars storing repo info in *repositories.db* and clone the repositories found in to the *repos* folder in the directory where the command was run.

<!-- 
repos folder structure:
repos/
	github-username1/
		repository-name1/
 -->

Output: 
```
Items per Page: 100
Number of requests left: 30/30
Total Count: 117,  for query: language:c language:cpp stars:100
Pages: 2.0
Number of requests left: 27/30
FINISHED
Items per Page: 100
Number of requests left: 27/30
Total Count: 106,  for query: language:c language:cpp stars:101
Pages: 2.0
Number of requests left: 24/30
FINISHED
...
```

## mgsearch

Searches for a supplied regex pattern across all files in repositories stored in a directory specified by *\-\-directory* flag. If directory not specified searches *repos* folder in current directory.

```bash
./mgsearch.py --query "[A-Za-z_]\w*\s*[A-Za-z_]\w*\s*;" --directory repos --nprocs 8  
```
The above command search all files in the directory repos for query using 8 parallel processes to speed up the search, if *\-\-nprocs* is not specified 4 processes are used by default. 


#### Explanation of features

##### Limiting search 

The search over the files can be limited by total number of matches using \-\-max_matches INT flag.

```bash
./mgsearch.py --query "int\s*[A-Za-z_]\w*\s*;" --max_matches 100
``` 
or 
```bash
./mgsearch.py -q "int\s*[A-Za-z_]\w*\s*;" -mm 100
```

So search is stopped after first 100 matches across all files are found.

```bash
./mgsearch.py --query "int\s*[A-Za-z_]\w*\s*;" --timeout 60
``` 
or 
```bash
./mgsearch.py -q "int\s*[A-Za-z_]\w*\s*;" -t 60
```

Similarily after 60 seconds the search stops.

Only one flag can be specified at a time, if both are present then number of max_matches takes precedent.

##### Filter files to be checked 
You probably don't want to search all files in a repository probably only those that are source files for a specific language this can be achive with either *\-\-endings* or *\-\-filetypes* flags.

```bash
./mgsearch.py --query "int\s*[A-Za-z_]\w*\s*;" --endings cpp cxx c++
```

Using \-\-endings as above means only files ending in .cpp .cxx and .c++ will be searched.

For c and c++ there are predefined filetypes for all files relating to that language.

```bash
./mgsearch.py --query "int\s*[A-Za-z_]\w*\s*;" --filetypes cpp
``` 
or
```bash
./mgsearch.py -q "int\s*[A-Za-z_]\w*\s*;" -ft cpp
```

So if cpp is used it matches files ending in .cpp, .cc, .C, .cxx, .m, .hpp, .hh, .h, .h++, .H, .hxx, .tpp, .c++

If both flags are specified only *\-\-endings* flag is taken into account.

##### Filter repositories 

To filter repositories to be searched a database had to be created when cloning the repositories, the path to the database file is required using the *\-\-database* flag.

```bash
./mgsearch.py --query "int\s*[A-Za-z_]\w*\s*;" --database repo.db --stars ">10" --language C++ --size "<1000"
```

The above command only searches through the repositories that have more than 10 stars have cpp as dominate language and are smaller than 1000KB.

#### Output of search
The child processes of mgsearch used to search the files in parallel each create there own output file with names res\*.out each of these files are merged together when the search completes.

The files store matches as follows:

```
repos/arthurgervais/Bitcoin-Simulator/src/applications/model/bitcoin-node.cc: int i = 0;
repos/arthurgervais/Bitcoin-Simulator/src/applications/model/bitcoin-node.cc: int k = 0;
repos/arthurgervais/Bitcoin-Simulator/src/applications/model/bitcoin-node.cc: 
              int totalBlockMessageSize = 0;
```
The final output file with the matches can be named using *\-\-output_file* flag, default name is mg_results.txt

Mgseach also produces another file on completion called *results.json* which contains the files repositories names only with the files within them that where matched in json format. This format is used for the transformApplication tool.

```
{
   "katzarsky/WebSocket": [
        "WebSocket/WebSocket.cpp", 
        "WebSocket/md5/md5.c", 
    ], 
    "adamyaxley/Obfuscate": [
        "obfuscate.h"
    ]
}

```

#### Notes:
- The allowed regular expression syntax is specified by [re2 syntax](https://github.com/google/re2/wiki/Syntax)


## transformApplication

transformApplication takes the *results.json* output of the mgsearch and applies a given transformation tool to it, the programme then attempts to compile the the transformed source code to gauge if it was successful.

transformation tool is supplied by the *\-\-tool* flag and takes the same command you would run in a terminal except for the use of keyword *input* which gets replaced by the the file to be transformed. Similarly for the *output* keyword gets replaced by a modified version of the input files name.

```bash
./transformApplication.py --tool "clang-tidy -checks=-*,modernize-loop-convert --fix-errors input -- -std=c++14" --regex modernize-loop-convert
```

If no compile tool is provided by using *\-\-compiler_tool* flag then defaults to `g++ -std=c++17 -c'input -o output`, providing a compiler tool to use works same as transformation tool with *input* and *output* being substituted for the file path for input and modifed for the output.

### Output

The output format of the tool is a tsv file as below:

```tsv
Repo Name			File Name					Diff chunks		Transformed		Compilation
katzarsky/WebSocket	WebSocket/WebSocket.cpp		3				1				FAILURE
katzarsky/WebSocket	WebSocket/base64/base64.cpp	0				0				SUCCESSFUL
```
Diff chunks tries to assess the source code changes to the file by diffing the original file to the transformed one, this is not always the best approach and over estimate changes a lot as it only counts diff regions in the file.

The Transformed column counts the number of appreances of the regex pattern specified by \-\-regex or *\-r* in the standard output of the transformation tool.

Compilation column is set to FAILURE or SUCCESSFUL based on the return code of the compiler tool when attempting to compile the transformed file.

The *\-\-output_csv* flag can set the name for tsv produced as output, default is *transform_results.csv*.

### Example

```bash
./transformApplication.py -t "clang-tidy -checks=-*,modernize-loop-convert --fix-errors input -- -std=c++14" -r modernize-loop-convert -d repos -ct "g++ -std=c++14 -c input -o output"
```

check help flag of the tool, *\-\-help*, more info.

## Installation instructions

This was written in python 2.7 on linux, the re2 dependency along with needing to install sqlite3 might make it harder to use on windows. 

- Dependencies
	- external dependcies
		- [re2 ](https://github.com/google/re2) - regular expression library by google.
		- sqlite3 (ships with most linux distros)
		- python-dev 
		- git
	- python dependencies
		- [GitHub api (python wrapper)](https://pypi.org/project/PyGithub/)
		- [re2 (python wrapper)](https://pypi.org/project/re2/) 

### install re2 library

Follow the install instructions on the [re2 ](https://github.com/google/re2) github page, an outline is also given below.

```
git clone https://github.com/google/re2.git
cd re2 
make 
make test
make install
make test install
```

alternative install using apt on ubuntu 18.04 bionic

```bash
sudo apt-get install libre2-4
sudo apt-get install libre2-dev
```

re2 must be installed before attempting to install re2 python wrapper.

### python dependencies 

ensure pip version is for python 2.7 or use pip2 instead of pip in the commands.

install the python wrapper for GitHub API

`pip install PyGithub`

install the re2 python wrapper, requires python-dev, the python developement files, to be installed if not already present

`sudo apt-get install python-dev`

`pip install re2`

### Clone Repository

Download the repository somewhere convenient    

```git clone https://github.com/Andrew-lindsay/Code-Grep.git```


### Setup GitHub token 

To use the GitHub api with less restrictions a GitHub token is required, follow these instructions to create one https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line.

Once a token is created place it in a file called *token.txt* in .code_grep directory in your home directory.

```bash
mkdir ~/.code_grep
echo "REPLCE WITH TOKEN" > ~/.code_grep/token.txt
``` 

without a token requests will be reduced from 30 to 10 which could lead to slow down when searching for many repositories using *github_repo_build.py* as the request counter only resets after 60 seconds. 


<!-- Once a token is created it needed to be placed in the *github_repo_build.py* file near the top of the file, look for the code below.

```python
# ========= REPLACE WITH GITHUB TOKEN ==============================
g = Github("REPALCE WITH TOKEN", per_page=100)
# ==================================================================
```
If you don't want to use an access token just remove the option for the code like so,

```python
g = Github(per_page=100)
```

this will limit requests from 30 to 10 which could lead to slow down when searching for many repositories using *github_repo_build.py* as requests counter only resets after 60 seconds. 
-->

### Environment setup 

To not have to use the full path to run the scripts and to avoid more permanent install solution adding the Code-Grep source directory to path may be beneficial.

`PATH=$PATH:PATH_TO_CODE_GREP/Code-Grep/src/`

when Code-Grep cloned in the $HOME directory this would work

`PATH=$PATH:/home/andrew/Code-Grep/src/`

to save running each time the above command can be added to users *.bashrc*, careful to use the full path to Code-Grep when doing so.

