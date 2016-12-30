#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The purpose of this script is to take any sklearn development branch I'm using
that is not yet in master, and merge it into a "developer master" branch called
`dev_combo`.

CommandLine:
    # Create dev_combo
    python ~/code/ibeis/_scripts/setup_special_sklearn.py

    # Test that `missing_values_rf` is merged correctly
    python -c "import utool, sklearn.ensemble; print(utool.get_func_kwargs(sklearn.ensemble.RandomForestClassifier.__init__))"
    nosetests sklearn/ensemble/tests/test_forest.py
"""
from __future__ import print_function, division, absolute_import, unicode_literals
from os.path import join
import utool as ut
# import git
# import os


def main():
    target = 'dev_combo'
    master = 'master'
    mixins = [
        # 'mbkm_fixup',
        'progiter',
        'multiclass_mcc',
        'missing_values_rf',
    ]
    ut.cprint('--- OPEN REPO ---', 'blue')
    # dpath = os.getcwd()
    dpath = ut.truepath('~/code/scikit-learn')
    repo = ut.Repo(dpath=dpath)
    # update_all(repo, master, mixins)
    REBASE_VERSION = True
    if REBASE_VERSION:
        ut.cprint('--- REBASE BRANCHES ON MASTER ---', 'blue')
        rebase_mixins = [make_dev_rebased_mixin(repo, master, branch) for branch in mixins]
        ut.cprint('--- CHECKOUT DEV MASTER --- ', 'blue')
        reset_dev_branch(repo, master, target)
        ut.cprint('--- MERGE INTO DEV MASTER --- ', 'blue')
        for branch in rebase_mixins:
            repo.issue('git merge --no-edit -s recursive ' + branch)
        # repo.issue('git merge --no-edit -s recursive -Xours ' + branch)
    else:
        # Attempt to automerge taking whatever is in the mixin branches as de-facto
        ut.cprint('--- CHECKOUT DEV MASTER --- ', 'blue')
        reset_dev_branch(repo, master, target)
        ut.cprint('--- MERGE INTO DEV MASTER --- ', 'blue')
        for branch in mixins:
            repo.issue('git merge --no-edit -s recursive -Xtheirs ' + branch)
        # cleanup because we didn't rebase
        fpath = join(repo.dpath, 'sklearn/utils/validation.py')
        ut.sedfile(fpath, 'accept_sparse=None', 'accept_sparse=False', force=True)
        repo.issue('git commit -am "quick fix of known merge issue"')

    # # Recompile the
    if True:
        repo.issue('python setup.py clean')
        repo.issue('python setup.py build -j9')
        repo.issue('python setup.py develop')
    # # repo.reset_branch_to_remote('speedup_kmpp')


def update_all(repo, master, mixins):
    ut.cprint('--- UPDATE ALL ---', 'blue')
    repo.checkout2(master)
    repo.pull2()
    repo.issue('git fetch --all')

    for branch in mixins:
        repo.checkout2(branch)
        # repo.issue('git checkout ' + branch)
        # gitrepo = repo.as_gitpython()  # NOQA
        # repo.reset_branch_to_remote(branch)
        repo.issue('git pull')


def reset_dev_branch(repo, branch, dev_branch):
    repo.checkout2(branch)
    if dev_branch in repo.branches:
        repo.issue('git branch -D ' + dev_branch)
    repo.issue('git checkout -b ' + dev_branch)


def make_dev_rebased_mixin(repo, master, branch):
    # Clear dev rebase branch
    rebase_branch = 'dev_rebase_' + branch

    if branch == 'missing_values_rf':
        reset_dev_branch(repo, branch, rebase_branch)
        missing_values_rf_rebase(repo, master, branch, rebase_branch)
    else:
        reset_dev_branch(repo, branch, rebase_branch)
        repo.issue('git rebase ' + master)
    # # squash everything into a commit
    with repo.chdir_context():
        out = ut.cmd2('git --no-pager log ' + master + '..HEAD --pretty=oneline')['out']
    n_commits = len(out.split('\n'))
    repo.issue('git reset ' + master)
    repo.issue('git commit -am "Combination of %d commits\n%s"' % (n_commits, out))
    # repo.issue('git reset ' + master)
    return rebase_branch


# Make a special rebase branch for missing_values_rf
def missing_values_rf_rebase(repo, master, branch, rebase_branch):
    """
    >>> import sys
    >>> sys.path.append('/home/joncrall/code/ibeis/_scripts')
    >>> from setup_special_sklearn import *
    >>> dpath = ut.truepath('~/code/scikit-learn')
    >>> master = 'master'
    >>> repo = ut.Repo(dpath=dpath)
    >>> branch = 'missing_values_rf'
    >>> rebase_branch = 'dev_rebase_' + branch
    """
    assert branch == 'missing_values_rf'
    reset_dev_branch(repo, branch, rebase_branch)

    # Custom rebase script
    out = repo.issue('git rebase ' + master, error='return')
    fpaths = repo._parse_merge_conflict_fpaths(out)
    fpath = fpaths[0]
    assert len(fpaths) == 1 and fpath.endswith('sklearn/utils/validation.py')
    repo.resolve_conflicts(fpath, 'theirs', force=True)
    ut.sedfile(fpath, 'accept_sparse=None', 'accept_sparse=False', force=True)
    repo.issue('git add ' + fpath)

    # Step 2
    out = repo.issue('git rebase --continue', error='return')
    # Regex to help solve conflicts
    for fpath in repo._parse_merge_conflict_fpaths(out):
        # repo.resolve_conflicts(fpath, 'ours', force=True)
        repo.resolve_conflicts(fpath, 'theirs', force=True)
        # repo.issue('git checkout --theirs ' + fpath)
        repo.issue('git add ' + fpath)

    out = repo.issue('git rebase --continue', error='return')
    assert out is None

    # mixins.remove(branch)
    # mixins.append(rebase_branch)

    # out = repo.issue('git rebase --abort')
    # Fix the patch # apply it
    # repo.issue('git am < fix_empty_poster.patch')


if __name__ == '__main__':
    r"""
    CommandLine:
        export PYTHONPATH=$PYTHONPATH:/home/joncrall/code/ibeis/_scripts
        python ~/code/ibeis/_scripts/setup_special_sklearn.py
        python ~/code/ibeis/_scripts/setup_special_sklearn.py --allexamples
    """
    main()
