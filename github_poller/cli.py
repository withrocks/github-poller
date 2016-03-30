import click
import requests
import os
import time
import logging
import json
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)
STATE_FILE = ".github-poller"

def save_state(etag, sha):
    with open(STATE_FILE, 'w+') as f:
        f.write("{},{}\n".format(etag, sha))

def read_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            content = f.read().rstrip()
            logger.info("Read state from state file: {}".format(content))
            return content.split(",")
    else:
        return None, None

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
    MIN_INTERVAL = 1
    RATE_LIMIT_UNAUTH = 60
    RATE_LIMIT_AUTH = 5000
    HEADER_REMAINING = "X-RateLimit-Remaining"
    HEADER_LIMIT = "X-RateLimit-Limit"

    logging.basicConfig(level=level)

    if interval < MIN_INTERVAL:
        raise ValueError("Interval must be higher than {}".format(MIN_INTERVAL))

    auth = HTTPBasicAuth(oauth_user, oauth_token) if oauth_user and oauth_token else None

    # TODO:
    # rate_limit = RATE_LIMIT_UNAUTH if not token else RATE_LIMIT_AUTH
    # logger.warn("Poll rate may exceed the default rate limit")

    etag, last_sha = read_state()
    url = "https://api.github.com/repos/{}/{}/branches/{}" \
            .format(user, repo, branch)

    while True:
        headers = {"If-None-Match": etag} if etag else None
        response = requests.get(url, auth=auth, headers=headers)
        etag = response.headers["ETag"]

        logger.debug("API Limit: {}/{}".format(
            response.headers[HEADER_REMAINING],
            response.headers[HEADER_LIMIT]))

        if response.status_code == 304:
            logger.debug("No change (304)")
        elif response.status_code != 200:
            logger.warn("Status code {} != 200. Ignoring."
                    .format(response.status_code))
        else:
            response_obj = response.json()
            sha = response_obj["commit"]["sha"]
            if sha == last_sha:
                logger.debug("SHA is unchanged")
            else:
                logger.info("SHA has changed. Firing event.")
                os.system(command)
                last_sha = sha
                save_state(etag, last_sha)
        time.sleep(interval)

