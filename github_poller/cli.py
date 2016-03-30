import click
import requests
import os
import time
import logging
import json
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)
STATE_FILE = ".github-poller"

def save_state(sha):
    with open(STATE_FILE, 'w+') as f:
        f.write(sha + "\n")

def read_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            sha = f.read().rstrip()
            logger.info("Read state from state file: {}".format(sha))
            return sha
    else:
        return None

@click.command()
@click.argument('user')
@click.argument('repo')
@click.argument('branch')
@click.argument('interval', type=int)
@click.argument('command')
@click.option('--oauth-user')
@click.option('--oauth-token')
@click.option('--level', default="WARN")
def main(user, repo, branch, interval, command, oauth_user, oauth_token, level):
    """
    Polls github for changes to a repo. Runs the supplied command on change.

    Note that webhooks are probably better if you are able to
    listen on a publicly accessible server.

    The request limit is constrained for unauthorized tokens (currently 60 reqs/hour).
    Create an oauth token and use with client_id/client_secret to increase it to 5.000 reqs/hour.
    """
    # TODO: Use conditonal requests (https://developer.github.com/v3/)
    MIN_INTERVAL = 1
    RATE_LIMIT_UNAUTH = 60
    RATE_LIMIT_AUTH = 5000

    logging.basicConfig(level=level)

    if interval < MIN_INTERVAL:
        raise ValueError("Interval must be higher than {}".format(MIN_INTERVAL))

    auth = HTTPBasicAuth(oauth_user, oauth_token) if oauth_user and oauth_token else None

    # TODO:
    # rate_limit = RATE_LIMIT_UNAUTH if not token else RATE_LIMIT_AUTH
    # logger.warn("Poll rate may exceed the default rate limit")

    last_sha = read_state()

    url = "https://api.github.com/repos/{}/{}/branches/{}" \
            .format(user, repo, branch)

    while True:
        response = requests.get(url, auth=auth)
        if response.status_code != 200:
            logger.warn("Status code {} != 200. Ignoring"
                    .format(response.status_code))
        else:
            response_obj = response.json()
            sha = response_obj["commit"]["sha"]
            if sha == last_sha:
                logger.debug("No changes")
            else:
                logger.info("SHA has changed. Firing event.")
                os.system(command)
                last_sha = sha
                save_state(last_sha)
        time.sleep(interval)

