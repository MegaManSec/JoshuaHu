---
layout: post
title: "Automatically re-requesting a team and user review on GitHub review dismissal"
tags: [programming, appsec, security]
description: "When GitHub dismisses a stale approval after a push, nobody is re-requested: not the reviewer, and not the team they reviewed on behalf of. A GitHub Actions workflow that automatically re-requests both."
---

Consider the following situation. You request a review on a GitHub PR using the "Reviewers" UI. That review may be requested from a group or a single user. A reviewer then reviews the PR:

>  MegaManSec reviewed on behalf of operasoftware/prodsec 18 hours ago

The list of "Reviewers" is now only MegaManSec - regardless of whether the group or individual reviewer was initially requested.

The PR author changes something in the PR (or just rebases or merges main into the branch).

If you have GitHub's "Dismiss stale pull request approvals when new commits are pushed" setting enabled, the review from MegaManSec (that's me!!1!) gets dismissed - but not re-requested, and other prodsec users won't have the opportunity to review it (or see it, if they look for "requested review" for their team).

The solution? If a review is dismissed and a change is made, automatically re-request a review from both the person, _and_ their team which initially instigated the review (if applicable).

```yaml
name: Re-request dismissed reviews

# Like pull_request, this event builds the PR merge ref, so it doesn't fire
# on PRs with merge conflicts.
on:
  pull_request_review:
    types: [dismissed]

permissions: {}

jobs:
  re-request:
    # Skipped for fork PRs and Dependabot (no secrets on this event) and bot
    # reviewers (can't be requested).
    if: >-
      github.event.pull_request.state == 'open' &&
      github.event.pull_request.head.repo.full_name == github.repository &&
      github.actor != 'dependabot[bot]' &&
      github.event.review.user.type == 'User'
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      # github.token can neither see teams nor request them, so team re-requests need an app token.
      - name: Mint scoped token
        id: app-token
        uses: actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1 # v3.2.0
        with:
          app-id: ${{ vars.GH_APP_ID }}
          private-key: ${{ secrets.GH_APP_PRIVATE_KEY }}
          permission-pull-requests: write
          permission-members: read

      # A team member's review satisfies the team's request and removes it, so
      # re-request each team the review was on behalf of that no other approval
      # still covers, and the reviewer unless they are the sender (they
      # dismissed it, or their push did).
      - name: Re-request review
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          REVIEW_ID: ${{ github.event.review.node_id }}
          REVIEWER: ${{ github.event.review.user.login }}
          SENDER: ${{ github.event.sender.login }}
        run: |
          request() {
            echo "Requesting review from $2"
            gh api --method POST "repos/$GITHUB_REPOSITORY/pulls/$PR_NUMBER/requested_reviewers" \
              -f "$1[]=$2" --silent || failed=1
          }

          [ "$SENDER" = "$REVIEWER" ] || request reviewers "$REVIEWER"

          teams=$(gh api graphql -f id="$REVIEW_ID" -f query='
            query($id: ID!) {
              node(id: $id) {
                ... on PullRequestReview {
                  onBehalfOf(first: 100) { nodes { slug } }
                  pullRequest {
                    latestOpinionatedReviews(first: 100) {
                      nodes { state author { login } onBehalfOf(first: 100) { nodes { slug } } }
                    }
                  }
                }
              }
            }' --jq '.data.node
              | [.onBehalfOf.nodes[].slug]
                - [.pullRequest.latestOpinionatedReviews.nodes[]
                    | select(.state == "APPROVED" and .author.login != env.REVIEWER)
                    | .onBehalfOf.nodes[].slug]
              | .[]')

          for team in $teams; do
            request team_reviewers "$team"
          done

          exit "${failed:-0}"
```

Note: you might want to skip the GitHub App and just give the workflow's own `GITHUB_TOKEN` `permissions: pull-requests: write`. That's fine for re-requesting the reviewer, but `GITHUB_TOKEN` can't be granted any organization permissions, so it can neither see which team a review was on behalf of, nor request a review from a team. Instead, you need to create a GitHub App with the _Pull requests: Read and write_ and _Members: Read-only_ permissions, install it on the repository, and put its App ID in the `GH_APP_ID` variable and its private key in the `GH_APP_PRIVATE_KEY` secret.
