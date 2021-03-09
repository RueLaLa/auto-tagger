#!/usr/bin/env python

import json
import os

import git
import requests
import semver


def semver_bump(curr_ver, commit_msg):
    if "#major" in commit_msg:
        new_ver = curr_ver.bump_major()
    elif "#minor" in commit_msg:
        new_ver = curr_ver.bump_minor()
    else:
        new_ver = curr_ver.bump_patch()
    return str(new_ver)


def comment_on_pr(pr_number, comment_body):
    url = f'https://api.github.com/repos/{os.getenv("GITHUB_REPOSITORY")}/issues/{pr_number}/comments'
    headers = {
        'Authorization': f'Bearer {os.getenv("GITHUB_TOKEN")}',
        'Accept': 'application/vnd.github.v3+json'
    }
    body = {'body': comment_body}
    requests.post(url, headers=headers, data=body)


def main():
    repo = git.Repo(os.pwd())
    event_info = json.loads(os.getenv('GITHUB_EVENT_PATH'))

    origin_url = f'https://{os.getenv("GITHUB_ACTOR")}:{os.getenv("GITHUB_TOKEN")}@github.com/{os.getenv("GITHUB_REPOSITORY")}.git'
    repo.create_remote('github',  origin_url)

    merge_commit_sha = event_info['pull_request']['merge_commit_sha']
    repo.git.checkout(merge_commit_sha)

    current_tag = reversed(repo.tags)[0]

    if current_tag is None:
        new_tag = 'v1.0.0'
    else:
        try:
            current_version = semver.VersionInfo.parse(current_tag[1:])
            merge_commit_message = repo.head.commit
            new_tag = semver_bump(current_version, merge_commit_message)

            repo.create_tag(new_tag, ref=merge_commit_sha)
            repo.remote.github.push(new_tag)
            comment_body = f'This PR has now been tagged as [$new_tag](https://github.com/{os.getenv("GITHUB_REPOSITORY")}/releases/tag/{new_tag})'
        except ValueError:
            comment_body = "latest tag does not conform to semver, failed to bump version"

    comment_on_pr(event_info['number'], new_tag, comment_body)


if __name__ == "__main__":
    main()
