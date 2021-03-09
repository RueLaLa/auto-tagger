#!/usr/bin/env python

import json
import os

import git
import requests
import semver


def setup_git(merge_commit_sha):
    """Initializes the git repo and checks out the commit ID created from the pull request.
    Assumes the current directory is the git repo to be loaded.

    Args:
        merge_commit_sha (str): hex sha string of the merge commit

    Returns:
        repo (object): git repo object
    """
    repo = git.Repo(os.getcwd())
    repo.git.checkout(merge_commit_sha)
    return repo


def semver_bump(repo):
    """Loads the most recently created tag from the git repo and parses it into a semver object.
    It is then incremented by a keyword in the commit message. Parsing exceptions are handled in parent function.

    Args:
        repo (object): git repo object

    Returns:
        new_tag (str): string of the new tag post incrementing semver section
    """
    current_tag = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)[-1]
    if current_tag.startswith('v'):
        current_tag = str(current_tag)[1:]
    else:
        current_tag = str(current_tag)

    curr_ver = semver.VersionInfo.parse(current_tag)
    commit_msg = repo.head.commit.message

    if '#major' in commit_msg:
        new_ver = curr_ver.bump_major()
    elif '#minor' in commit_msg:
        new_ver = curr_ver.bump_minor()
    else:
        new_ver = curr_ver.bump_patch()

    if current_tag.startswith('v'):
        return f'v{str(new_ver)}'
    else:
        return str(new_ver)


def create_and_push_tag(repo, merge_commit_sha, new_tag):
    """Creates a new tag from arguments in the git repo and pushes it to github.
    Authentication is handled by environment variables passed in from github actions.

    Args:
        repo (object): git repo object
        merge_commit_sha (str): hex sha string of merge commit used to attach tag
        new_tag (str): new tag string to be committed and pushed to remote

    Returns:
        None
    """
    repo.create_tag(new_tag, ref=merge_commit_sha)
    origin_url = f"https://{os.getenv('GITHUB_ACTOR')}:{os.getenv('GITHUB_TOKEN')}@github.com/{os.getenv('GITHUB_REPOSITORY')}.git"
    gh_origin = repo.create_remote('github',  origin_url)
    gh_origin.push(new_tag)


def comment_on_pr(pr_number, comment_body):
    """Comments on github PR with a given message.
    Authentication is handled by environment variables passed in from github actions.

    Args:
        pr_number (int): number of the pull request. determines where to post message
        comment_body (str): message to be posted to pull request by github actions bot

    Returns:
        None
    """
    url = f"https://api.github.com/repos/{os.getenv('GITHUB_REPOSITORY')}/issues/{pr_number}/comments"
    headers = {
        'Authorization': f"Bearer {os.getenv('GITHUB_TOKEN')}",
        'Accept': 'application/vnd.github.v3+json'
    }
    body = {'body': comment_body}
    requests.post(url, headers=headers, json=body)


def main():
    """Main function orchestrating the tag bump and commenting on the PR.
    Reads its configuration from a json file and environment variables provided by github actions.

    Args:
        None

    Returns:
        None
    """
    with open(os.getenv('GITHUB_EVENT_PATH')) as f:
        event_info = json.loads(f.read())

    repo = setup_git(event_info['pull_request']['merge_commit_sha'])

    comment_body = ''
    new_tag = None
    if len(repo.tags) == 0:
        new_tag = 'v1.0.0'
    else:
        try:
            new_tag = semver_bump(repo)
        except ValueError:
            comment_body = 'latest tag does not conform to semver ([v]?MAJOR.MINOR.PATCH), failed to bump version'

    if new_tag is not None:
        create_and_push_tag(repo, event_info['pull_request']['merge_commit_sha'], new_tag)
        comment_body = f"This PR has now been tagged as [{new_tag}](https://github.com/{os.getenv('GITHUB_REPOSITORY')}/releases/tag/{new_tag})"

    comment_on_pr(event_info['number'], comment_body)


if __name__ == '__main__':
    main()
