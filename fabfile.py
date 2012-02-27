from fabric.api import local, task, abort, settings
from clom import clom

@task
def release():
    """
    Release current version to pypi
    """

    with settings(warn_only=True):
        r = local(clom.git['diff-files']('--quiet', '--ignore-submodules', '--'))

    if r.return_code != 0:
        abort('There are uncommitted changes, commit or stash them before releasing')

    version = open('VERSION.txt').read().strip()

    print('Releasing %s...' % version)
    local(clom.git.tag(version, a=True, m='Release %s' % version))
    local(clom.git.push('origin', 'HEAD'))
    local(clom.git.push('origin', version))
    local(clom.python('setup.py', 'sdist', 'upload'))