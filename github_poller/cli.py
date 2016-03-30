import click
import requests
import os
import time
import logging
import json

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
@click.option('--level', default="WARN")
def main(user, repo, branch, interval, command, level):
    """Polls github for changes to a repo. Runs the supplied command on change."""

    MIN_INTERVAL = 1

    logging.basicConfig(level=level)

    if interval < MIN_INTERVAL:
        raise ValueError("Interval must be higher than {}".format(MIN_INTERVAL))

    last_sha = read_state()

    while True:
        url = "https://api.github.com/repos/{}/{}/branches/{}".format(user, repo, branch)
        response = requests.get(url)
        if response.status_code != 200:
            logger.warn("Status code wasn't 200 ({}), ignoring"
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

