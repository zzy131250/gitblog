# -*- coding: utf-8 -*-
import argparse

from datetime import datetime
from github import Github


def login(token):
    return Github(token)


def get_me(user):
    return user.get_user().login


def get_repo(user: Github, repo: str):
    return user.get_repo(repo)


def get_TODO(issue):
    body = issue.body.splitlines()
    return [l for l in body if l.startswith("- [ ] ")]


def format_time(time):
    return str(time)[:10]


def main(token, repo_name, from_issue_number=None, issue_number=None):
    user = login(token)
    repo = get_repo(user, repo_name)

    from_issue = repo.get_issue(int(from_issue_number))
    TODO = get_TODO(from_issue)
    comment = [l + "\n" for l in TODO]

    issue = repo.get_issue(int(issue_number))
    now = datetime.now().strftime("%Y-%m-%d")
    issue.create_comment("# " + now + " 打卡\n" + "".join(comment))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("github_token", help="github_token")
    parser.add_argument("repo_name", help="repo_name")
    parser.add_argument(
        "--from_issue_number", help="from_issue_number", default=None, required=False
    )
    parser.add_argument(
        "--issue_number", help="issue_number", default=None, required=False
    )
    options = parser.parse_args()
    main(options.github_token, options.repo_name, options.from_issue_number, options.issue_number)