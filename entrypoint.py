#!/usr/bin/env python3

import json
import os

import git
import semver

from github import Github


class SemVerWithVPrefix(semver.VersionInfo):
    """Class to handle semver parsing with v prefix

    Args:
        version_string (str): version string with v prefix

    Returns:
        instance of sv (semver.Version): parsed semver version object
    """

    @classmethod
    def parse(cls, version):
        parse = version[1:] if version[0] in ("v", "V") else version
        self = super(SemVerWithVPrefix, cls).parse(parse)
        return self

    def __str__(self):
        return "v" + super(SemVerWithVPrefix, self).__str__()


def setup_git(merge_commit_sha):
    """Initializes the git repo and checks out the commit ID created from the pull request.
    Assumes the current directory is the git repo to be loaded.

    Args:
        merge_commit_sha (str): hex sha string of the merge commit

    Returns:
        repo (object): git repo object
    """
    repo = git.Repo(os.getcwd())
    repo.config_writer(config_level="global").set_value(
        "safe", "directory", os.getcwd()
    )
    repo.git.checkout(merge_commit_sha)
    return repo


def get_current_tag(tags):
    """Gets a list of all tags and sorts them. The first sort is by commit date, but then
    it is sorted numerically by the semver tag number in the event of two tags on a single commit.

    Args:
        tags (list(object)): a list of tags from the current

    Returns:
        current_tag (semver.Version): parsed semver version of the latest tag on the latest commit
    """
    newest_tag_date = max([tag.commit.committed_datetime for tag in tags])
    latest_tags = [
        SemVerWithVPrefix.parse(str(tag))
        for tag in tags
        if tag.commit.committed_datetime == newest_tag_date
    ]
    return max(latest_tags)


def semver_bump(current_tag, commit_message):
    """Loads the most recently created tag from the git repo and parses it into a semver object.
    It is then incremented by a keyword in the commit message. Parsing exceptions are handled in parent function.

    Args:
        current_tag (semver.Version): current and latest tag found on the repo
        commit_message (string): commit message used to parse which semver section to bump

    Returns:
        new_tag (str): string of the new tag post incrementing semver section
    """
    if "#major" in commit_message:
        new_ver = current_tag.bump_major()
    elif "#minor" in commit_message:
        new_ver = current_tag.bump_minor()
    else:
        new_ver = current_tag.bump_patch()

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
    gh_origin = repo.create_remote("github", origin_url)
    gh_origin.push(new_tag)


def comment_on_pr(comment_body):
    """Comments on github PR with a given message.
    Authentication is handled by environment variables passed in from github actions.

    Args:
        comment_body (str): message to be posted to pull request by github actions bot

    Returns:
        None
    """
    g = Github(os.getenv("GITHUB_TOKEN"))
    repo = g.get_repo(os.getenv("GITHUB_REPOSITORY"))

    if os.getenv("GITHUB_PR_NUMBER"):
        pr_number = int(os.getenv("GITHUB_PR_NUMBER"))
    else:
        with open(os.getenv("GITHUB_EVENT_PATH")) as f:
            event_info = json.loads(f.read())
        pr_number = event_info["number"]

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
    repo = setup_git(os.getenv("GITHUB_SHA"))

    if len(repo.tags) == 0:
        new_tag = "v1.0.0"
    else:
        current_tag = get_current_tag(repo.tags)
        new_tag = semver_bump(current_tag, repo.head.commit.message)

    comment_body = f"This PR has now been tagged as [{new_tag}](https://github.com/{os.getenv('GITHUB_REPOSITORY')}/releases/tag/{new_tag})"
    print(comment_body)
    if os.getenv("DRYRUN"):
        return

    create_and_push_tag(repo, os.getenv("GITHUB_SHA"), new_tag)
    comment_on_pr(comment_body)


if __name__ == "__main__":
    main()
