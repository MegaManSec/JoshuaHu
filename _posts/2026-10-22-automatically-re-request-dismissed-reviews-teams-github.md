---
layout: post
title: "Automatically re-requesting a team and user review on GitHub review dismissal"
tags: [programming, appsec, security]
render_with_liquid: false
description: "When GitHub dismisses a stale approval after a push, nobody is re-requested: not the reviewer, and not the team they reviewed on behalf of. A GitHub Actions workflow that automatically re-requests both."
---

Consider the following situation. You request a review on a GitHub PR using the "Reviewers" UI. That review may be requested from a group or a single user. A reviewer then reviews the PR:

>  MegaManSec reviewed on behalf of operasoftware/prodsec 18 hours ago

The list of "Reviewers" is now only MegaManSec - regardless of whether the group or individual reviewer was initially requested.

The PR author changes something in the PR (or just rebases or merges main into the branch).

If you have GitHub's "Dismiss stale pull request approvals when new commits are pushed" setting enabled, the review from MegaManSec (that's me!!1!) gets dismissed - but not re-requested. The prodsec team is still missing from "Reviewers", so the PR doesn't show up in prodsec's review requests either. Other prodsec members can still review it, but nothing tells them that it's waiting on them.

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

The app itself doesn't run anywhere or receive any events. On each run, `actions/create-github-app-token` uses the app's private key to get a token that only covers the current repository and the two permissions in its `permission-*` inputs, and revokes the token when the job finishes. To set it up:

1. Create a new GitHub App in the organization's settings, under "Developer settings". Any name and homepage URL will do, but the re-requests show up as coming from the app, so pick a name people will recognize. Untick "Active" under "Webhook", since nothing needs to send it events.
2. Give it the "Pull requests: Read and write" repository permission and the "Members: Read-only" organization permission. Members is the one that lets the token see teams and request them.
3. Create the app, note its App ID, and generate a private key (this downloads a `.pem` file).
4. Install the app on the organization, for just the repositories that will run the workflow.
5. Add the App ID as a `GH_APP_ID` Actions variable, and the contents of the `.pem` file as a `GH_APP_PRIVATE_KEY` secret, in either the repository's or the organization's settings.

If you only want to re-request the reviewer and not their team, you don't need the app at all. In that case, the workflow is just:

```yaml
name: Re-request dismissed reviews

# Like pull_request, this event builds the PR merge ref, so it doesn't fire
# on PRs with merge conflicts.
on:
  pull_request_review:
    types: [dismissed]

permissions:
  pull-requests: write

jobs:
  re-request:
    # Skipped for fork PRs and Dependabot (read-only token on this event) and
    # bot reviewers (can't be requested).
    if: >-
      github.event.pull_request.state == 'open' &&
      github.event.pull_request.head.repo.full_name == github.repository &&
      github.actor != 'dependabot[bot]' &&
      github.event.review.user.type == 'User'
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      # Re-request the reviewer unless they are the sender (they dismissed it,
      # or their push did).
      - name: Re-request review
        env:
          GH_TOKEN: ${{ github.token }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          REVIEWER: ${{ github.event.review.user.login }}
          SENDER: ${{ github.event.sender.login }}
        run: |
          if [ "$SENDER" != "$REVIEWER" ]; then
            echo "Requesting review from $REVIEWER"
            gh api --method POST "repos/$GITHUB_REPOSITORY/pulls/$PR_NUMBER/requested_reviewers" \
              -f "reviewers[]=$REVIEWER" --silent
          fi
```
