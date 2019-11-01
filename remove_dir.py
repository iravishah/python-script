import requests
import json
import git
import os
import shutil
import subprocess
import sys

path = '/path/to/repos'
backup_path = '/backup/path'
repo_list = ['repo1']

# if os.path.exists(path):
    # shutil.rmtree(path, ignore_errors=True)
    # shutil.rmtree(backup_path, ignore_errors=True)
    # os.makedirs(path, exist_ok=True)
    # os.makedirs(backup_path, exist_ok=True)


def get_urls():
    url = 'https://api.github.com/users/iravishah/repos'
    headers = {
        "Authorization": "Basic <token>"
    }
    params = {
        "page": 1,
        "per_page": 100
    }
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    urls = dict()
    for repo in data["values"]:
        if repo["links"]["clone"][0]["name"] == "ssh":
            urls[repo["name"]] = repo["links"]["clone"][0]["href"]
        if repo["links"]["clone"][1]["name"] == "ssh":
            urls[repo["name"]] = repo["links"]["clone"][1]["href"]
    return urls


def blank_values(new_file, data):
    for ele in data:
        if type(data[ele]) == dict:
            new_file[ele] = dict()
            blank_values(new_file[ele], data[ele])
        else:
            new_file[ele] = ''
    return new_file


repos = get_urls()
print(repos)

for r in repos:
    try:
        if repo_list.index(r) != -1:
            print('processing for ', r)
            local_path = path + '/' + r
            repo_instance = git.Repo
            
            print('cloning repo...')
            repo_instance.clone_from(repos[r], local_path)
            print('cloned repo...')

            rpo = repo_instance(local_path)
            remote_branches = rpo.git.branch('-a')
            remote_branches = [x.strip() for x in remote_branches.split('\n')]
            print(remote_branches);
            remote_branches = remote_branches[2:]
            print(remote_branches)
            active_branch = rpo.active_branch.name
            # remote_branches = ['remotes/origin/develop']

            print('branches are ', remote_branches)

            for rb in remote_branches:
                new_br = rb.split('/')
                local_branch = new_br[-1]
                if new_br[-2] == 'feature':
                    local_branch = new_br[-2] + '/' + new_br[-1]
                if new_br[-2] == 'hotfix':
                    local_branch = new_br[-2] + '/' + new_br[-1]
                if new_br[-2] == 'fix':
                    local_branch = new_br[-2] + '/' + new_br[-1]
                if new_br[-2] == 'fature':
                    local_branch = new_br[-2] + '/' + new_br[-1]
                if new_br[-2] == 'prod':
                    local_branch = new_br[-2] + '/' + new_br[-1]

                if local_branch != active_branch:
                    rpo.git.checkout('-b', local_branch, rb)
                    rpo.git.pull('origin', local_branch)
                else:
                    rpo.git.checkout(active_branch)
                    rpo.git.pull('origin', local_branch)

                os.chdir(local_path)

                env_dir = os.getcwd() + '/env'
                if r == 'engine' or r == 'integration-engine':
                    env_dir = os.getcwd() + '/config'

                isEnvExists = os.path.exists(env_dir)
                if isEnvExists == True:
                    print('copy env folder from ', local_branch)
                    shutil.copytree(env_dir, backup_path +
                                '/' + r + '/' + local_branch)
                    # shutil.rmtree(env_dir)
                    configs = os.listdir(env_dir)
                    print('configs ', configs)
                    flag = False
                    for config in configs:
                        if os.stat(env_dir + '/' + config).st_size != 0 and config.endswith('.json'):
                            flag = True
                            new_file = dict()
                            print(env_dir + '/' + config)
                            with open(env_dir + '/' + config, 'r') as data_file:
                                data = json.load(data_file)

                            json_data = blank_values(new_file, data)

                            with open(env_dir + '/' + config, 'w') as outfile:
                                json.dump(json_data, outfile, indent=2)
                    if flag == True:
                        if r == 'engine' or r == 'integration-engine':
                            rpo.git.add('config/')
                        else:
                            rpo.git.add('env/')
                        rpo.git.commit(m='updated configs of env folder')
                        # rpo.git.push('origin', local_branch)
                        try:
                            rpo.git.push('origin', local_branch)
                            # print('test')
                        except:
                            e = sys.exc_info()
                            print('protected branch ', rb)
                            print(e)
                config_path = os.getcwd() + '/config.json'
                isRooTConfig = os.path.exists(config_path)
                if isRooTConfig == True:
                    os.makedirs(backup_path + '/' + r + '/' + local_branch, exist_ok=True)
                    shutil.copyfile(config_path, backup_path +
                                '/' + r + '/' + local_branch + '/config.json')
                    new_file = dict()
                    with open(config_path, 'r') as data_file:
                        data = json.load(data_file)

                    json_data = blank_values(new_file, data)

                    with open(config_path, 'w') as outfile:
                        json.dump(json_data, outfile, indent=2)
                    
                    rpo.git.add('config.json');
                    rpo.git.commit(m='updated config.json')
                    try:
                        # print('env')
                        rpo.git.push('origin', local_branch)
                    except:
                        e = sys.exc_info()[0]
                        print('protected branch config', rb)
                        print(e)

    except ValueError as error:
        print(error)

