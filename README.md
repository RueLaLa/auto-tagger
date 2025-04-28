auto-tagger
===

# Introduction

This is a simple github action that is triggered on github PR merging that will increment the git tag on the merge commit following [semver](https://semver.org) and add a comment to the merged commit with the new tag.

# Installation

To use this, simply define an action configuration yaml in the `.github/workflows` directory of your repository with the following contents:
```
name: Auto Tagger

on:
  pull_request:
    types: [closed]

jobs:
  auto-tagger:
    uses: RueLaLa/auto-tagger/.github/workflows/auto_tagger.yml@master

```

The default Github token created for the action to use has enough permissions to checkout, tag, and push the new tag on the repo that this action is defined in.

# Local Testing

To test the semver component locally, install the python dependencies by running `pip install -r requirements.txt` where auto-tagger is checked out.

Then, cd to the directory you want to test in and run the below command:
```
DRYRUN=True GITHUB_SHA=$(git rev-parse HEAD) /path/to/auto-tagger/entrypoint.py
```

# Usage

Once installed, when merging a pull request, simply include either `#major`, `#minor`, or `#patch` to the commit message. Alternatively, if you don't include of these, a patch level bump will be assumed. Below is an example from the pull request page:
![merge commit message example](docs/merge_commit_msg_example.png)
