#!/bin/bash

function semver_bump() {
  RE='^[v]?([0-9]*)[.]([0-9]*)[.]([0-9]*)$'

  if [[ $1 =~ $RE ]]; then
    case "$2" in
    *#major*)
      new_tag="v$((${BASH_REMATCH[1]} + 1)).0.0"
    ;;
    *#minor*)
      new_tag="v${BASH_REMATCH[1]}.$((${BASH_REMATCH[2]} + 1)).0"
    ;;
    *)
      new_tag="v${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.$((${BASH_REMATCH[3]} + 1))"
    ;;
    esac
 fi
}

# get merge commit and check it out locallt
merge_commit_sha=$(cat "$GITHUB_EVENT_PATH" | jq -r '.pull_request.merge_commit_sha')
merge_commit_message=$(git --no-pager log --format=%B -n 1)
git remote add github "https://$GITHUB_ACTOR:$GITHUB_TOKEN@github.com/$GITHUB_REPOSITORY.git"
git checkout $merge_commit_sha

# get current tag and bump it using the commit message as a key
current_tag=$(git describe --abbrev=0 --tags 2>&1)
if [[ $current_tag == *"fatal: No names found"* ]]; then
  new_tag="v1.0.0"
else
  semver_bump "$current_tag" "$merge_commit_message"
fi

# tag the commit with the new tag and push it to remote
git tag $new_tag
git push github --tags

# comment on PR with new tag and link to tag release
pr_number=$(cat "$GITHUB_EVENT_PATH" | jq -r '.number')
curl -XPOST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/${GITHUB_REPOSITORY}/issues/${pr_number}/comments \
  -d "{\"body\": \"This PR has now been tagged as [$new_tag](https://github.com/${GITHUB_REPOSITORY}/releases/tag/${new_tag})\"}"
