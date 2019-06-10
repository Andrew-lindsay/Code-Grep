#!/usr/bin/python

import requests
import json


def create_repo_pull_list():
    pass


def get_results(key_words, search_type, num_per_page=10):
    response = requests.get(
        "https://api.github.com/search/" + search_type + "?q=" +
        '+'.join(key_words) + "+language:c&per_page=" + str(num_per_page),
        headers={'Authorization': 'token 87fbbf6e4d5bbb3cec34970f06c85b097d1cb68f'})
    if response.status_code != 200:
        print('Error Status code: {}'.format(response.status_code))

    # save results to a file
    with open("res.json", "w") as res_file:
        try:
            json.dump(response.json(), fp=res_file, indent=4)
        except ValueError:
            print("Response not a json file")

    # print(json.dumps(response.json(), indent=4))
    if search_type == "code":
        search_items = response.json()['items']

        for item in search_items:
            print("Repo: {}\nFile Name: {}\n".format(
                item['repository']['full_name'], item['name']))

    elif search_type == "repositories":
        search_items = response.json()['items']
        # print(json.dumps(response.json(), indent=4))
        with open("repo_list.txt", "w") as repo_list:
            for item in search_items:
                print("Full Repo Name: {}".format(item['full_name']))
                repo_list.write("{}\n".format(item['full_name']))


def main():
    search_terms = ["language:C++", "stars:10", ]
    print("search terms: {}".format(search_terms))
    get_results(search_terms, search_type="repositories", num_per_page=100)


if __name__ == "__main__":
    main()
