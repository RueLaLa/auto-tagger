#!/usr/bin/env python

import json
import os

import git
import requests
import semver


def setup_git(event_info):
    repo = git.Repo(os.getcwd())
    repo.git.checkout(event_info['pull_request']['merge_commit_sha'])
    return repo


def semver_bump(repo):
    current_tag = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)[-1]
    curr_ver = semver.VersionInfo.parse(current_tag[1:])
    commit_msg = repo.head.commit

    if "#major" in commit_msg:
        new_ver = curr_ver.bump_major()
    elif "#minor" in commit_msg:
        new_ver = curr_ver.bump_minor()
    else:
        new_ver = curr_ver.bump_patch()
    return f'v{str(new_ver)}'


def create_and_push_tag(repo, merge_commit_sha, new_tag):
    repo.create_tag(new_tag, ref=merge_commit_sha)
    origin_url = f'https://{os.getenv("GITHUB_ACTOR")}:{os.getenv("GITHUB_TOKEN")}@github.com/{os.getenv("GITHUB_REPOSITORY")}.git'
    gh_origin = repo.create_remote('github',  origin_url)
    gh_origin.push(new_tag)


def comment_on_pr(pr_number, comment_body):
    url = f'https://api.github.com/repos/{os.getenv("GITHUB_REPOSITORY")}/issues/{pr_number}/comments'
    headers = {
        'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}',
        'Accept': 'application/vnd.github.v3+json'
    }
    body = {'body': comment_body}
    requests.post(url, headers=headers, data=body)


def main():
    with open(os.getenv('GITHUB_EVENT_PATH')) as f:
        event_info = json.loads(f.read())

    repo = setup_git(event_info)

    comment_body = ''
    if len(repo.tags) == 0:
        new_tag = 'v1.0.0'
    else:
        try:
            new_tag = semver_bump(repo)
            comment_body = f'This PR has now been tagged as [$new_tag](https://github.com/{os.getenv("GITHUB_REPOSITORY")}/releases/tag/{new_tag})'
        except ValueError:
            comment_body = 'latest tag does not conform to semver, failed to bump version'

    create_and_push_tag(repo, event_info['pull_request']['merge_commit_sha'], new_tag)
    comment_on_pr(event_info['number'], new_tag, comment_body)


if __name__ == '__main__':
    main()
