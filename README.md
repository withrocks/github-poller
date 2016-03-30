# github-poller

Polls github for changes to a repo, running a command on each change.

Example:

To poll for changes to this repo's master branch every 5 seconds, and run
pip install when it happens:

    $ github-poller withrocks github-poller master 5 'pip install -U git+https://github.com/withrocks/github-poller.git@master'

