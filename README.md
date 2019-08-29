# Code-Grep

Code-Grep is a set of comand-line programmes that together build a pipeline. This pipeline can be used to search for patterns in source code files hosted on GithHub and apply code transformation tools to those files identified.

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
./mgsearch.py --query "\[A-Za-z_]\w*\s*\[A-Za-z_]\w;" --directory repos --nprocs 8  
```
The above command search all files in the directory repos for query using 8 parallel processes to speed up the search, if *\-\-nprocs* is not specified 4 processes are used by default. 


#### Explanation of features

##### Limiting search 

The search over the files can be limited by total number of matches using \-\-max_matches INT flag.

`./mgsearch.py --query "int\s*\[A-Za-z_]\w;" --max_matches 100` or `./mgsearch.py -q "int\s*\[A-Za-z_]\w;" -mm 100` 

So search is stopped after first 100 matches across all files are found.

`./mgsearch.py --query "int\s*\[A-Za-z_]\w;" --timeout 60` or `./mgsearch.py -q "int\s*\[A-Za-z_]\w;" -t 60` 

Similarily after 60 seconds the search stops.

Only one flag can be specified at a time, if both are present then number of max_matches takes precedent.

##### Filter files to be checked 
You probably don't want to search all files in a repository probably only those that are source files for a specific language this can be achive with either *\-\-endings* or *\-\-filetypes* flags.

`./mgsearch.py --query "int\s*\[A-Za-z_]\w;" --endings cpp cxx c++`

Using \-\-endings as above means only files ending in .cpp .cxx and .c++ will be searched.

For c and c++ there are predefined filetypes for all files relating to that language.

`./mgsearch.py --query "int\s*\[A-Za-z_]\w;" --filetypes cpp` or `./mgsearch.py -q "int\s*\[A-Za-z_]\w;" -ft cpp`

So if cpp is used it matches files ending in .cpp, .cc, .C, .cxx, .m, .hpp, .hh, .h, .h++, .H, .hxx, .tpp, .c++

If both flags are specified only *\-\-endings* flag is taken into account.

##### Filter repositories 

To filter repositories to be searched a database had to be created when cloning the repositories, the path to the database file is required using the *\-\-database* flag.

`./mgsearch.py --query "int\s*\[A-Za-z_]\w;" --database repo.db --stars ">10" --language C++ --size "<1000"`

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

Mgseach also produces another file on completion called results.json which contains the files repositories names only with the files within them that where matched in json format. This format is used for the transformApplication tool.

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

TO BE FINISHED

check help command for the tool.


## Installation instructions

This was written in python 2.7 on linux, the re2 dependency along with needing to install sqlite3 might make it harder to use on windows. 

- Dependencies
	- external dependcies
		- [re2 ](https://github.com/google/re2) - regular expression library by google.
		- sqlite3 (ships with most linux distros)
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

alternative using apt on debian distro

`sudo apt-get install re2-3`


### python dependencies 

ensure pip version is for python 2.7 or use pip2 instead of pip in the commands.

install the python wrapper for GitHub API

`pip install PyGithub`

install the re2 python wrapper  

`pip install re2`

### Clone Repository

Download the repository somewhere convenient    

```git clone https://github.com/Andrew-lindsay/Code-Grep.git```

### Environment setup 

To not have to use the full path to run the scripts and to avoid more permanent install solution adding the Code-Grep source directory to path may be beneficial.

`PATH=$PATH:PATH_TO_CODE_GREP/PATH_TO_CODE_GREP/Code-Grep/src/`

when Code-Grep cloned in the $HOME directory this would work

`PATH=$PATH:/home/andrew/Code-Grep/src/`

to save running each time the above command can be added to users *.bashrc*, careful to use the full path to Code-Grep when doing so.