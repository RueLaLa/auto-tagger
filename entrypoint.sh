#!/bin/bash

function semver_bump() {
  RE='^v\([0-9]*\)[.]\([0-9]*\)[.]\([0-9]*\)$'

  MAJOR=$(echo $1 | sed -e "s|$RE|\1|")
  MINOR=$(echo $1 | sed -e "s|$RE|\2|")
  PATCH=$(echo $1 | sed -e "s|$RE|\3|")

  case "$2" in
  major)
    let MAJOR+=1
    let MINOR=0
    let PATCH=0
    ;;
  minor)
    let MINOR+=1
    let PATCH=0
    ;;
  patch)
    let PATCH+=1
    ;;
  esac

  new_tag="v$MAJOR.$MINOR.$PATCH"
}

merge_commit_sha=$(cat "$GITHUB_EVENT_PATH" | jq -r '.pull_request.merge_commit_sha')
merge_commit_message=$(git --no-pager log --format=%B -n 1)
git remote add github "https://$GITHUB_ACTOR:$GITHUB_TOKEN@github.com/$GITHUB_REPOSITORY.git"
git checkout $merge_commit_sha

current_tag=$(git describe --abbrev=0 --tags 2>&1)
if [[ $current_tag == *"fatal: No names found"* ]]; then
  new_tag="v1.0.0"
else
  case $merge_commit_message in
    *#major*)
      semver_bump $current_tag major
      ;;
    *#minor*)
      semver_bump $current_tag minor
      ;;
    *)
      semver_bump $current_tag patch
      ;;
  esac
fi

git tag $new_tag
git push github --tags
