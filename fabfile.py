from fabric.api import local, task, abort, settings
from clom import clom
from fabric.colors import green

@task
def release():
    """
    Release current version to pypi
    """

    with settings(warn_only=True):
        r = local(clom.git['diff-files']('--quiet', '--ignore-submodules', '--'))
        branch = str(local("git for-each-ref --format='%(refname:short)' `git symbolic-ref HEAD`", capture=True)).strip()

    if branch != 'develop':
        abort('You must be on the develop branch to start a release.')
    elif r.return_code != 0:
        abort('There are uncommitted changes, commit or stash them before releasing')

    version = open('VERSION.txt').read().strip()

    print(green('Releasing %s...' % version))
    local(clom.git.flow.release.start(version))

    # Can't use spaces in git flow release messages, see https://github.com/nvie/gitflow/issues/98
    local(clom.git.flow.release.finish(version, m='Release-%s' % version))
    local(clom.git.push('origin', 'master', tags=True))
    local(clom.python('setup.py', 'sdist', 'upload'))