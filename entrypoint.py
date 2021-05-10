#!/usr/bin/env python

import json
import os

import git
import semver

from github import Github


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


def get_current_tag(tags):
    """Gets a list of all tags and sorts them. The first sort is by commit date, but then
    it is sorted numerically by the semver tag number in the event of two tags on a single commit.

    Args:
        tags (list(object)): a list of tags from the current

    Returns:
        current_tag (str): string of the latest tag on the latest commit
    """
    sorted_tags = sorted(tags, key=lambda t: t.commit.committed_datetime, reverse=True)
    current_tags = [tag for tag in sorted_tags if tag.commit.committed_datetime == sorted_tags[0].commit.committed_datetime]
    if len(current_tags) > 1:
        try:
            current_tags = sorted(current_tags, key=lambda t: [int(t) for t in str(t).replace('v', '').split('.')], reverse=True)
        except ValueError:
            comment_on_pr(f'latest tag ({current_tags}) does not conform to semver ([v]?MAJOR.MINOR.PATCH), failed to bump version')
            exit(1)
    return(str(current_tags[0]))


def semver_bump(current_tag, commit_message):
    """Loads the most recently created tag from the git repo and parses it into a semver object.
    It is then incremented by a keyword in the commit message. Parsing exceptions are handled in parent function.

    Args:
        current_tag (string): current and latest tag found on the repo
        commit_message (string): commit message used to parse which semver section to bump

    Returns:
        new_tag (str): string of the new tag post incrementing semver section
    """
    try:
        curr_ver = semver.VersionInfo.parse(current_tag.replace('v', ''))
    except ValueError:
        comment_on_pr(f'latest tag ({current_tag}) does not conform to semver ([v]?MAJOR.MINOR.PATCH), failed to bump version')
        exit(1)

    if '#major' in commit_message:
        new_ver = curr_ver.bump_major()
    elif '#minor' in commit_message:
        new_ver = curr_ver.bump_minor()
    else:
        new_ver = curr_ver.bump_patch()

    return f'v{str(new_ver)}' if current_tag.startswith('v') else str(new_ver)


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


def comment_on_pr(comment_body):
    """Comments on github PR with a given message.
    Authentication is handled by environment variables passed in from github actions.

    Args:
        comment_body (str): message to be posted to pull request by github actions bot

    Returns:
        None
    """
    g = Github(os.getenv('GITHUB_TOKEN'))
    repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))

    if os.getenv('GITHUB_PR_NUMBER'):
        pr_number = int(os.getenv('GITHUB_PR_NUMBER'))
    else:
        with open(os.getenv('GITHUB_EVENT_PATH')) as f:
            event_info = json.loads(f.read())
        pr_number = event_info['number']

    pr = repo.get_pull(pr_number)
    pr.create_issue_comment(body=comment_body)


def main():
    """Main function orchestrating the tag bump and commenting on the PR.
    Reads its configuration from a json file and environment variables provided by github actions.

    Args:
        None

    Returns:
        None
    """
    repo = setup_git(os.getenv('GITHUB_SHA'))

    comment_body = ''
    new_tag = None
    if len(repo.tags) == 0:
        new_tag = 'v1.0.0'
    else:
        current_tag = get_current_tag(repo.tags)
        new_tag = semver_bump(current_tag, repo.head.commit.message)

    if new_tag is not None:
        comment_body = f"This PR has now been tagged as [{new_tag}](https://github.com/{os.getenv('GITHUB_REPOSITORY')}/releases/tag/{new_tag})"
        if os.getenv('DRYRUN'):
            print(comment_body)
            exit(0)
        create_and_push_tag(repo, os.getenv('GITHUB_SHA'), new_tag)
        comment_on_pr(comment_body)


if __name__ == '__main__':
    main()
