#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TODO:
    * needs to check if required modules are installed (or prefereably developed)
    * needs to be able to ignore plugins that the user doesnt care about

Super Setup
PREREQ:
git config --global push.default current
export CODE_DIR=~/code
mkdir $CODE_DIR
cd $CODE_DIR
git clone https://github.com/WildbookOrg/ibeis.git
cd ibeis

python super_setup.py --bootstrap
OR (if in virtual environment)
python super_setup.py --bootstrap --nosudo
OR
./_scripts/bootstrap.py
THEN
./_scripts/__install_prereqs__.sh
THEN
./super_setup.py --build --develop
./super_setup.py --build --develop

./super_setup.py --status

# If on current branch copy so super setup isn't overwriten as we go
python -c "import utool as ut; ut.copy('super_setup.py', '_ibeis_setup.py')"

# Status
python _ibeis_setup.py -y --gg "git status"
python _ibeis_setup.py -y --gg "git branch"

# Setup Next
#python _ibeis_setup.py -y --gg "git pull"
#python _ibeis_setup.py -y --gg "git checkout master"
#python _ibeis_setup.py -y --gg "git pull"
#python _ibeis_setup.py -y --gg "git checkout -b next"
#python _ibeis_setup.py -y --gg "git checkout next"
#python _ibeis_setup.py -y --gg "git push -u origin next"
#python _ibeis_setup.py -y --gg "git push remote origin/next"
####python _ibeis_setup.py -y --gg "git merge master"


#python _ibeis_setup.py -y --gg "git checkout ^HEAD"
#python _ibeis_setup.py -y --gg "git checkout master"
#python _ibeis_setup.py -y --gg "git checkout next"


# -- MERGE topic -> next
##python _ibeis_setup.py -y --gg "git checkout topic"
##python _ibeis_setup.py -y --gg "git checkout next"
##python _ibeis_setup.py -y --gg "git merge topic"


# -- MERGE next -> master
python _ibeis_setup.py -y --gg "git checkout master"
python _ibeis_setup.py -y --gg "git merge next"

# -- SAFER MERGE topic -> next
python super_setup.py --checkout next
python super_setup.py --newlocalbranch merge_next_joncrall_dev_branch
python super_setup.py --merge joncrall_dev_branch
./run_tests.py
python super_setup.py --checkout next
python super_setup.py --merge merge_next_joncrall_dev_branch

# Push
python _ibeis_setup.py -y --gg "git push"

#python _ibeis_setup.py -y --gg "git checkout master"
#python _ibeis_setup.py -y --gg "git checkout next"


# MAKE A NEW BRANCH
python super_setup.py --newbranch joncrall_dev_branch
python super_setup.py --checkout joncrall_dev_branch
python super_setup.py --checkout next

python super_setup.py --newbranch jdb
python super_setup.py --checkout jdb


GitReferences:
    http://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging

FIXME:
    graph-viz
    pydot
    ibeis_cnn
    Theano
    Lasange
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from os.path import dirname, realpath
import platform
import sys
import os

#-----------------
# SYSTEM ENTRY POINT, NO UTOOL, BARE PYTHON
#-----------------


USAGE = ('''

 --- USAGE ---

IBEIS (IMAGE ANALYSIS) SUPER SETUP

This script is meant to help setup, install, and update the developer
enviroment for IBEIS Image Analysis.

****
# Step 1 Initial Development Prereqs:

The first thing is to ensure you have a baseline development enviroment (gcc,
fortran, cmake, blas, git, pip, etc...).  This should work well for apt-get,
yum, and macports package managers.  It is possible to use Windows MinGW, but
it is not well supported.

The following command outputs the commands to install these prereq packages.

    python super_setup.py --bootstrap

****
# Step 2 - utool

Just running the script will download and install utool --- a utility library
used in all aspects of the system.

    python super_setup.py

****
# Step 3 - Download / Update Image Analysis Packages

Running the script again once utool is installed will ensure the rest of the
repositories are cloned and on your machine in the directory above this one, or
in a custom location set by your $CODE_DIR environment variable.  Running with
the pull command will update the packages as well.

    python super_setup.py pull

****
# Step 3.5 - Grab and Build Extern libraries with scripts

         python super_setup.py --opencv
         python super_setup.py --dcnn
         python super_setup.py --flann
         python super_setup.py --pyqt

****
# Step 4 - Build C++ components.

Some submodles require C++ libraries. Build them using the following Command.

    python super_setup.py build

****
# Step 5 - Install the system.

Register these packages with the python enviroment.

    ~python super_setup.py develop~
    # Actually this command instead
    pip install -e .

 --- /USAGE ---
''')


def define_argparse():
    """ todo, find a way to use this effectively """
    import argparse
    parser = argparse.ArgumentParser(description='IBEIS super setup')
    # parser.add_argument('command', help='command to run')

    def add_flag(group, name, help=None):
        group.add_argument(name.replace('--', ''), action='store_true',
                           default=False, help=help)

    # subparsers = parser.add_subparsers()
    # subparsers.add_parser('pull', help='pulls IBEIS repos')
    # subparsers.add_parser('ensure', help='ensures checkouts of IBEIS repos')
    # sub = subparsers.add_parser('move-wildme', help='changes to the wildme repos')
    # sub.add_argument('--fmt', dest='fmt', action='store',
    #                  choices=['ssh', 'https'], help='url type')

    ## Setup options for parser_a

    ## Add nargs="*" for zero or more other commands
    # parser.add_argument('extra', nargs = "*", help = 'Other commands')

    # parser.add_argument('command', action='store_true', default=False,
    #                     help='outputs commands to install prereqs')

    g1 = parser.add_argument_group('setup')
    add_flag(g1, 'bootstrap', help='outputs commands to install prereqs')
    add_flag(g1, 'ensure', help='ensures that all repos are checked out')
    add_flag(g1, 'build', help='builds python packages')
    add_flag(g1, 'develop', help='installs packages in developer mode')
    add_flag(g1, 'dcnn', help='setup dcnn packages')

    g4 = parser.add_argument_group('maintenance')
    add_flag(g4, 'pull', help='pulls all IBIES repos')

    g3 = parser.add_argument_group('extern')
    add_flag(g3, 'no_qt')
    add_flag(g3, 'no_gui')
    add_flag(g3, 'ignore_opencv')

    g2 = parser.add_argument_group('utils')
    add_flag(g2, 'move_wildme',
             help='changes to the wildme repos')
    args = parser.parse_args()
    return args


# args = define_argparse()
# print('args = %r' % (args,))
# sys.exit(1)


def get_plat_specifier():
    """
    Standard platform specifier used by distutils
    """
    import setuptools  # NOQA
    import distutils
    plat_name = distutils.util.get_platform()
    plat_specifier = ".%s-%s" % (plat_name, sys.version[0:3])
    if hasattr(sys, 'gettotalrefcount'):
        plat_specifier += '-pydebug'
    return plat_specifier


def import_module_from_fpath(module_fpath):
    """ imports module from a file path """
    import platform
    from os.path import basename, splitext
    python_version = platform.python_version()
    modname = splitext(basename(module_fpath))[0]
    if python_version.startswith('2.7'):
        import imp
        module = imp.load_source(modname, module_fpath)
    elif python_version.startswith('3'):
        import importlib.machinery
        loader = importlib.machinery.SourceFileLoader(modname, module_fpath)
        module = loader.load_module()
    else:
        raise AssertionError('invalid python version')
    return module


def bootstrap(WIN32):
    if WIN32:
        # need to preinstall parse
        win32bootstrap_fpath = os.path.abspath('_scripts/win32bootstrap.py')
        win32bootstrap = import_module_from_fpath(win32bootstrap_fpath)
        win32bootstrap.bootstrap_sysreq()

    else:
        #import bootstrap
        bootstrap_fpath = os.path.abspath('_scripts/bootstrap.py')
        bootstrap = import_module_from_fpath(bootstrap_fpath)
        #sys.path.append(os.path.abspath('_scripts'))
        bootstrap.bootstrap_sysreq()
    sys.exit(0)


#################
#  ENSURING UTOOL
#################


def syscmd(cmdstr):
    print('RUN> ' + cmdstr)
    os.system(cmdstr)


def ensure_utool(CODE_DIR, pythoncmd):
    WIN32 = sys.platform.startswith('win32')
    #UTOOL_BRANCH = ' -b <branch> <remote_repo>'
    UTOOL_BRANCH = 'next'
    UTOOL_REPO = 'https://github.com/WildbookOrg/utool.git'
    print('FATAL ERROR: UTOOL IS NEEDED FOR SUPER_SETUP. Attempting to get utool')
    cwdpath = os.path.realpath(os.getcwd())
    usr_code_dir = os.path.expanduser(CODE_DIR)
    os.chdir(usr_code_dir)
    print("user code dir = %r" % usr_code_dir)
    print('cloning utool')
    if not os.path.exists('utool'):
        syscmd('git clone ' + UTOOL_REPO + ' -b ' + UTOOL_BRANCH)
    os.chdir('utool')
    print('pulling utool')
    syscmd('git pull')
    print('installing utool for development')
    cmdstr = '{pythoncmd} setup.py develop'.format(pythoncmd=pythoncmd)
    # TODO: use pip instead
    # cmdstr = '{pythoncmd} -m pip install .'.format(pythoncmd=pythoncmd)
    in_virtual_env = hasattr(sys, 'real_prefix')
    if not WIN32 and not in_virtual_env:
        cmdstr = 'sudo ' + cmdstr
    syscmd(cmdstr)
    os.chdir(cwdpath)
    sys.path.append(usr_code_dir)
    print('Please rerun super_setup.py')
    print(' '.join(sys.argv))
    if '--check-utool-error-code-0' in sys.argv:
        sys.exit(0)
    else:
        sys.exit(1)

#-----------------
#  UTOOL PYTHON
#-----------------


def initialize_repo_managers(CODE_DIR, pythoncmd, PY2, PY3):
    import utool as ut
    WITH_CNN = True
    WITH_PYRF = True
    #WITH_TPL = True
    WITH_QT = not ut.get_argflag('--no-qt')
    WITH_GUI = not ut.get_argflag('--no-gui')
    WITH_CUSTOM_TPL = True
    WITH_FLUKEMATCH = True
    #-----------
    # IBEIS project repos
    #-----------
    # if True:
    #     jon_repo_base = 'https://github.com/WildbookOrg'
    #     jason_repo_base = 'https://github.com/WildbookOrg'
    # else:
    #     jon_repo_base = 'https://github.com/wildme'
    #     jason_repo_base = 'https://github.com/wildme'
    # else:
    #     jon_repo_base = 'git@hyrule.cs.rpi.edu
    #     jason_repo_base = 'git@hyrule.cs.rpi.edu

    ibeis_rman = ut.RepoManager([
        'https://github.com/WildbookOrg/utool.git',
        # 'https://github.com/WildbookOrg/sandbox_utools.git',
        'https://github.com/WildbookOrg/vtool.git',
        'https://github.com/WildbookOrg/dtool.git',
        'https://github.com/WildbookOrg/detecttools.git',
    ], CODE_DIR, label='core', pythoncmd=pythoncmd)

    tpl_rman = ut.RepoManager([], CODE_DIR, label='tpl', pythoncmd=pythoncmd)
    if not GET_ARGFLAG('--ignore-opencv'):
        cv_repo = ut.Repo('https://github.com/Itseez/opencv.git', CODE_DIR, modname='cv2')
        tpl_rman.add_repo(cv_repo)

    if WITH_GUI:
        ibeis_rman.add_repos([
            'https://github.com/WildbookOrg/plottool.git',
        ])

        if WITH_QT:
            ibeis_rman.add_repos([
                'https://github.com/WildbookOrg/guitool.git',
            ])
            tpl_rman.add_repo(ut.Repo(modname=('PyQt4', 'PyQt5', 'PyQt')))

    if WITH_CUSTOM_TPL:
        flann_repo = ut.Repo('https://github.com/WildbookOrg/flann.git', CODE_DIR, modname='pyflann')
        ibeis_rman.add_repo(flann_repo)
        ibeis_rman.add_repos([
            'https://github.com/WildbookOrg/hesaff.git',
        ])

    if WITH_CNN:
        ibeis_rman.add_repos([
            'https://github.com/WildbookOrg/ibeis_cnn.git@next',
            'https://github.com/WildbookOrg/pydarknet.git',
        ])
        if WITH_FLUKEMATCH:
            ibeis_rman.add_repos([
                'https://github.com/zmjjmz/ibeis-flukematch-module.git'
            ])
        # CNN Dependencies
        tpl_rman.add_repos([
            'https://github.com/Theano/Theano.git',
            'https://github.com/lisa-lab/pylearn2.git',
            'https://github.com/Lasagne/Lasagne.git',
        ])
        tpl_rman.add_repos([
            'https://github.com/Theano/libgpuarray.git',
        ])

    if WITH_PYRF:
        ibeis_rman.add_repos([
            'https://github.com/WildbookOrg/pyrf.git',
        ])

    if False:
        # Depricated
        ibeis_rman.add_repos([
            #'https://github.com/WildbookOrg/pybing.git',
            #'https://github.com/aweinstock314/cyth.git',
            #'https://github.com/hjweide/pygist',
        ])

    # Add main repo (Must be checked last due to dependency issues)
    ibeis_rman.add_repos([
        'https://github.com/WildbookOrg/ibeis.git',
    ])

    #-----------
    # Custom third party build/install scripts
    #-----------
    define_custom_scripts(tpl_rman, ibeis_rman, PY2, PY3)

    return tpl_rman, ibeis_rman


def define_custom_scripts(tpl_rman, ibeis_rman, PY2, PY3):
    """
    export THEANO_FLAGS="device=cpu,print_active_device=True,enable_initial_driver_test=True"
    set THEANO_FLAGS=device=cpu,print_active_device=True,enable_initial_driver_test=True,print_test_value=True

    python -c "import pydot; print(pydot.__file__)"
    python -c "import pydot; print(pydot.__version__)"
    python -c "import pydot; print(pydot.find_graphviz())"
    python -c "import theano; print(theano.__file__)"
    python -c "import pylearn2; print(pylearn2.__file__)"
    python -c "import lasagne; print(lasagne.__file__)"
    python -c "import ibeis_cnn; print(ibeis_cnn.__file__)"
    python -c "import detecttools; print(detecttools.__file__)"

    # http://stackoverflow.com/questions/18042919/how-to-install-pyqt5-on-a-new-virtualenv-and-work-on-an-idle
    pip install vext.pyqt5
    sudo apt-get install pyqt5-dev
    sudo apt-get install python3-pyqt5
    python
    python -c "import sip; print('[test] Python can import sip')"
    python -c "import sip; print('sip.__file__=%r' % (sip.__file__,))"
    python -c "import sip; print('sip.SIP_VERSION=%r' % (sip.SIP_VERSION,))"
    python -c "import sip; print('sip.SIP_VERSION_STR=%r' % (sip.SIP_VERSION_STR,))"

    ln -s /usr/lib/python3/dist-packages/PyQt5/ /home/joncrall/venv3/lib/python3.4/site-packages/PyQt5
    ln -s /usr/lib/python3/dist-packages/sip*.so /home/joncrall/venv3/lib/python3.4/site-packages/
    ln -s /usr/lib/python3/dist-packages/sip*.py /home/joncrall/venv3/lib/python3.4/site-packages/
    """
    import utool as ut

    major = str(sys.version_info.major)
    minor = str(sys.version_info.minor)
    majorminor = [major, minor]
    pyoff = '2' if sys.version_info.major == 3 else '3'
    plat_spec = get_plat_specifier()
    # build_dname = 'build' + ''.join(majorminor)
    build_dname = 'cmake_builds/build' + plat_spec

    script_fmtdict = {
        'pyversion'         : 'python' + '.'.join(majorminor),
        'pypkg_var'         : 'PYTHON' + major + '_PACKAGES_PATH',
        'build_dname'       : build_dname,
        'cv_pyon_var'       : 'BUILD_opencv_python' + majorminor[0],
        'cv_pyoff_var'      : 'BUILD_opencv_python' + pyoff,
        'plat_spec'         : plat_spec,
        'source_dpath'      : '../..',
        'libext'            : ut.get_lib_ext(),
    }

    # define bash variables for different combinations of python distros and
    # virtual environments
    python_bash_setup = ut.codeblock(
        r'''
        # STARTBLOCK bash
        export PYTHON_EXECUTABLE=$(which {pyversion})

        if [[ "$VIRTUAL_ENV" == ""  ]]; then
            # If there is no virtual environment install to system
            # TODO: add support for mac conventions
            if [[ '$OSTYPE' == 'darwin'* ]]; then
                export LOCAL_PREFIX=/opt/local
                export {pypkg_var}=$($PYTHON_EXECUTABLE -c "import site; print(site.getsitepackages()[0])")
                export PYTHON_PACKAGES_PATH=${pypkg_var}
                export _SUDO="sudo"
            else
                export LOCAL_PREFIX=/usr/local
                export {pypkg_var}=$LOCAL_PREFIX/lib/{pyversion}/dist-packages
                export PYTHON_PACKAGES_PATH=${pypkg_var}
                export _SUDO="sudo"
            fi
        else
            export LOCAL_PREFIX=$VIRTUAL_ENV/local
            export {pypkg_var}=$LOCAL_PREFIX/lib/{pyversion}/site-packages
            export PYTHON_PACKAGES_PATH=${pypkg_var}
            export _SUDO=""
        fi

        echo "LOCAL_PREFIX = $LOCAL_PREFIX"
        echo "{pypkg_var} = ${pypkg_var}"
        # ENDBLOCK bash
        '''
    ).format(**script_fmtdict)
    script_fmtdict['python_bash_setup'] = python_bash_setup

    #===================
    # PYFLANN SETUP SCRIPTS
    #===================

    ibeis_rman['pyflann'].add_script('build', ut.codeblock(
        r'''
        # STARTBLOCK bash
        {python_bash_setup}

        cd {repo_dir}
        mkdir -p {build_dname}
        cd {build_dname}

        cmake -G "Unix Makefiles" \
            -DCMAKE_BUILD_TYPE="Release" \
            -DPYTHON_EXECUTABLE=$PYTHON_EXECUTABLE \
            -DBUILD_EXAMPLES=Off \
            -DBUILD_TESTS=Off \
            -DBUILD_PYTHON_BINDINGS=On \
            -DBUILD_MATLAB_BINDINGS=Off \
            -DBUILD_CUDA_LIB=Off\
            -DCMAKE_INSTALL_PREFIX=$LOCAL_PREFIX\
            {source_dpath}

        export NCPUS=$(grep -c ^processor /proc/cpuinfo)
        make -j$NCPUS

        # ENDBLOCK bash
        ''').format(repo_dir=ibeis_rman['pyflann'].dpath, **script_fmtdict)
    )

    ibeis_rman['pyflann'].add_script('install', ut.codeblock(
        r'''
        # STARTBLOCK bash
        # The pyflann source lives here
        cd {repo_dir}/src/python
        # Need to run build to move the libs to the build directory
        python setup.py build
        # Use pip to editable install
        pip install -e {repo_dir}/src/python

        # Old way of doing it
        # But the setup script is generated during build
        # python {repo_dir}/build/src/python/setup.py develop

        python -c "import pyflann; print(pyflann.__file__)" --verb-flann
        python -c "import pyflann; print(pyflann)" --verb-flann
        # ENDBLOCK bash
        ''').format(repo_dir=ibeis_rman['pyflann'].dpath)
    )

    #===================
    # HESAFF
    #===================

    ibeis_rman['hesaff'].add_script('build', ut.codeblock(
        r"""
        # STARTBLOCK bash
        {python_bash_setup}
        cd $CODE_DIR/hesaff
        mkdir -p {build_dname}
        cd {build_dname}

        echo 'Configuring with cmake'
        if [[ '$OSTYPE' == 'darwin'* ]]; then
            cmake -G "Unix Makefiles" \
                -DCMAKE_OSX_ARCHITECTURES=x86_64 \
                -DCMAKE_C_COMPILER=clang2 \
                -DCMAKE_CXX_COMPILER=clang2++ \
                -DCMAKE_INSTALL_PREFIX=$LOCAL_PREFIX \
                -DOpenCV_DIR=$LOCAL_PREFIX/share/OpenCV \
                {source_dpath}
        else
            cmake -G "Unix Makefiles" \
                -DCMAKE_INSTALL_PREFIX=$LOCAL_PREFIX \
                -DOpenCV_DIR=$LOCAL_PREFIX/share/OpenCV \
                {source_dpath}
        fi

        export NCPUS=$(grep -c ^processor /proc/cpuinfo)
        make -j$NCPUS

        export MAKE_EXITCODE=$?
        echo "MAKE_EXITCODE=$MAKE_EXITCODE"

        # Move the compiled library into the source folder
        if [[ $MAKE_EXITCODE == 0 ]]; then
            #make VERBOSE=1
            cp -v libhesaff{libext} {source_dpath}/pyhesaff/libhesaff{plat_spec}{libext}
        fi

        # ENDBLOCK
        """).format(**script_fmtdict))

    #===================
    # OPENCV SETUP SCRIPTS
    #===================

    tpl_rman['cv2'].add_script('build', ut.codeblock(
        r"""
        # STARTBLOCK bash
        {python_bash_setup}
        # Checkout opencv core
        cd $CODE_DIR
        # export REPO_DIR=$CODE_DIR/opencv
        export REPO_DIR={repo_dpath}
        # git clone https://github.com/Itseez/opencv.git
        cd $REPO_DIR
        # Checkout opencv extras
        git clone https://github.com/Itseez/opencv_contrib.git
        mkdir -p $REPO_DIR/{build_dname}
        cd $REPO_DIR/{build_dname}

        cmake -G "Unix Makefiles" \
            -D WITH_OPENMP=ON \
            -D CMAKE_BUILD_TYPE=RELEASE \
            -D {cv_pyoff_var}=Off \
            -D {cv_pyon_var}=On \
            -D {pypkg_var}=${pypkg_var} \
            -D CMAKE_INSTALL_PREFIX=$LOCAL_PREFIX \
            -D OPENCV_EXTRA_MODULES_PATH=$REPO_DIR/opencv_contrib/modules \
            -D WITH_CUDA=Off \
            $REPO_DIR
            # -D CXX_FLAGS="-std=c++11" \ %TODO

        export NCPUS=$(grep -c ^processor /proc/cpuinfo)
        make -j$NCPUS
        # ENDBLOCK
        """).format(repo_dpath=ut.unexpanduser(tpl_rman['cv2'].dpath),
                    **script_fmtdict))

    tpl_rman['cv2'].add_script('install', ut.codeblock(
        r"""
        # STARTBLOCK bash
        {python_bash_setup}

        cd $CODE_DIR/opencv/{build_dname}

        $_SUDO make install
        # Hack because cv2 does not want to be installed for some reason
        cp lib/cv2.so $PYTHON_PACKAGES_PATH
        # Test makesure things working
        python -c "import numpy; print(numpy.__file__)"
        python -c "import numpy; print(numpy.__version__)"
        python -c "import cv2; print(cv2.__version__)"
        python -c "import cv2; print(cv2.__file__)"
        #python -c "import vtool"
        # Check if we have contrib modules
        python -c "import cv2; print(cv2.xfeatures2d)"
        # ENDBLOCK
        """).format(**script_fmtdict))

    tpl_rman['libgpuarray'].add_script('build', ut.codeblock(
        r"""
        # STARTBLOCK bash
        {python_bash_setup}
        cd {repo_dpath}
        mkdir -p {repo_dpath}/{build_dname}
        cd {repo_dpath}/{build_dname}

        # First build the C library
        cmake {repo_dpath} -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$LOCAL_PREFIX
        export NCPUS=$(grep -c ^processor /proc/cpuinfo)
        make -j$NCPUS
        $_SUDO make install

        # Now build the python libarary
        cd {repo_dpath}
        python setup.py build_ext -L $LOCAL_PREFIX/lib -I $LOCAL_PREFIX/include
        python setup.py build
        # python setup.py install
        $_SUDO pip install -e {repo_dpath}

        # DEVICE="<test device>" python -c "import pygpu;pygpu.test()"
        # DEVICE="gpu0" python -c "import pygpu;pygpu.test()"
        cd ~
        DEVICE="cuda" python -c "import pygpu;pygpu.test()"

        # pip uninstall pygpu
        # ENDBLOCK
        """).format(repo_dpath=ut.unexpanduser(tpl_rman['libgpuarray'].dpath),
                    **script_fmtdict))

    #===================
    # PYQT SETUP SCRIPTS
    #===================

    if ut.in_virtual_env():
        fmtdict = {
            'sys_dist_packages': ut.get_global_dist_packages_dir(),
            'venv_site_packages': ut.get_site_packages_dir(),
            'pyqt'              : 'PyQt4' if PY2 else 'PyQt5',
            'debian-python-qt'  : 'python-qt4' if PY2 else 'qt5-default python3-pyqt5',
            'pip-python-qt'  : 'python-qt4' if PY2 else 'python-qt5'
        }
        # sys_dist_packages = ut.get_global_dist_packages_dir()
        # sys_pyqt_dir = sys_dist_packages + '/{pyqt}'
        # Allows us to use a system qt install in a virtual environment.
        system_to_venv = ut.codeblock(
            r'''
            # STARTBLOCK bash
            # Creates a symlink to the global PyQt in a virtual env
            export GLOBAL_DIST_PACKAGES="{sys_dist_packages}"
            export VENV_DIST_PACKAGES="{venv_site_packages}"
            if [ -d $GLOBAL_DIST_PACKAGES/{pyqt} ]; then
                echo "have qt"
                ls $GLOBAL_DIST_PACKAGES/{pyqt}
                ls $VENV_DIST_PACKAGES/{pyqt}
            else
                # Ensure PyQt is installed first (FIXME make this work for non-debian systems)
                sudo apt-get install {debian-python-qt}
                pip install {pip-python-qt}
            fi
            if [ -d $GLOBAL_DIST_PACKAGES/{pyqt} ]; then
                # Install system pyqt packages to virtual envirment via symlink
                ln -s $GLOBAL_DIST_PACKAGES/{pyqt}/ $VENV_DIST_PACKAGES/{pyqt}
                ln -s $GLOBAL_DIST_PACKAGES/sip*.so $VENV_DIST_PACKAGES/
                ln -s $GLOBAL_DIST_PACKAGES/sip*.py $VENV_DIST_PACKAGES/
            else
                echo "{pyqt} DOES NOT SEEM TO BE INSTALLED ON THE SYSTEM"
            fi
            echo "testing"
            python -c "import {pyqt}; print({pyqt})"
            # ENDBLOCK bash
            ''').format(**fmtdict)
        # TODO: add custom build alternative
        tpl_rman['PyQt'].add_script('system_to_venv', system_to_venv)


#-----------
# Verify TPL Dependencies
#-----------


def GET_ARGFLAG(arg, *args, **kwargs):
    import utool as ut
    return arg.lstrip('--') in sys.argv or ut.get_argflag(arg, *args, **kwargs)


def move_wildme(ibeis_rman, fmt):
    wildme_user = 'WildbookOrg'
    wildme_remote = 'wildme'
    for repo in ibeis_rman.repos:
        gitrepo = repo.as_gitpython()
        wildme_url = repo._new_remote_url(host='github.com', user=wildme_user, fmt=fmt)
        remotes = repo.remotes
        print('Checking %s for move to wildme' % (repo,))

        incorrect_version = repo._ensure_remote_exists(wildme_remote, wildme_url)

        if 'origin' in remotes:
            try:
                origin = remotes['origin']
                origin_user = origin['username']
                if origin_user != wildme_user or incorrect_version:
                    if origin_user not in remotes:
                        # first add a remote that is the original origin
                        origin_url = origin['url']
                        print('  * Create remote %r: %r' % (origin_user, origin_url,))
                        gitrepo.create_remote(origin_user, origin_url)
                    # change origin to use wildme url
                    gitorigin = gitrepo.remote('origin')
                    print('  * Change origin url to %r' % (wildme_url,))
                    gitorigin.set_url(wildme_url)
            except:
                print('\tWARNING: COULD NOT MIGRATE REPO = %r' % (repo, ))


def execute_commands(tpl_rman, ibeis_rman):
    import utool as ut

    GET_ARGVAL = ut.get_argval

    ut.init_catch_ctrl_c()

    if 0:
        print('Version Check Source:')
        for repo in tpl_rman.repos:
            print('python -c "import {0}; print({0}.__file__)"'.format(repo.modname))
            print('python -c "import {0}; print({0}.__version__)"'.format(repo.modname))

    #-----------
    # Execute Commands on Core Repos
    #-----------

    CODE_DIR, pythoncmd, WIN32, PY2, PY3 = get_sysinfo()

    print('ibeis_rman = %r' % (ibeis_rman,))

    wildme_ssh_flags = GET_ARGFLAG('--move-wildme') or GET_ARGFLAG('--move-wildme-ssh')
    wildme_https_flags = GET_ARGFLAG('--move-wildme-https') or GET_ARGFLAG('--move-wildme-http')
    if wildme_ssh_flags or wildme_https_flags:
        fmt = 'ssh' if wildme_ssh_flags else 'https'
        move_wildme(ibeis_rman, fmt)

    # Commands on global git repos
    if GET_ARGFLAG('--status'):
        ibeis_rman.issue('git status')
        sys.exit(0)

    ibeis_rman.ensure()

    if GET_ARGFLAG('--dump-scripts'):
        dpath = '_super_scripts/' + 'scripts' + get_plat_specifier()
        ut.ensuredir(dpath)
        dumps = [
            (tpl_rman, 'cv2', 'build'),
            (tpl_rman, 'cv2', 'install'),
            (tpl_rman, 'libgpuarray', 'build'),
            (ibeis_rman, 'flann', 'build'),
            (ibeis_rman, 'flann', 'install'),
            (ibeis_rman, 'hesaff', 'build'),
            (tpl_rman, 'PyQt', 'system_to_venv'),
        ]

        for rman, mod, sname in dumps:
            from os.path import join
            script = rman[mod].get_script(sname).text
            suffix = get_plat_specifier()
            sh_fpath = join(dpath, mod + '_' + sname + suffix + '.sh')
            ut.write_to(sh_fpath, script)

    if GET_ARGFLAG('--requirements'):
        ut.cmd('pip install -r requirements.txt')

    # HACKED IN SCRIPTS WHILE IM STILL FIGURING OUT TPL DEPS
    if GET_ARGFLAG('--opencv'):
        # There is now a pypi for opencv! Yay
        # ut.cmd('pip install opencv-python')
        # Bummer, but we need opencv source for pyhessaff
        # we should just make a wheel for pyhessaff
        cv_repo = tpl_rman['cv2']
        cv_repo.clone()
        script = cv_repo.get_script('build')
        script.exec_()
        cv_repo = tpl_rman['cv2']
        script = cv_repo.get_script('install')
        script.exec_()

    if GET_ARGFLAG('--pyqt'):
        script = tpl_rman['PyQt'].get_script('system_to_venv')
        script.exec_()

    if GET_ARGFLAG('--flann'):
        script = ibeis_rman['flann'].get_script('build')
        script.exec_()
        script = ibeis_rman['flann'].get_script('install')
        script.exec_()

    if GET_ARGFLAG('--libgpuarray'):
        tpl_rman['libgpuarray'].clone()
        script = tpl_rman['libgpuarray'].get_script('build')
        script.exec_()

    if GET_ARGFLAG('--dcnn'):
        tpl_rman['theano'].clone()
        tpl_rman['pylearn2'].clone()
        tpl_rman['lasagne'].clone()
        tpl_rman['theano'].issue('pip install -e .')
        tpl_rman['pylearn2'].issue('pip install -e .')
        tpl_rman['lasagne'].issue('pip install -e .')
        # tpl_rman['pylearn2'].python_develop()
        # tpl_rman['theano'].python_develop()
        # tpl_rman['lasagne'].python_develop()

    #_===

    if GET_ARGFLAG('--fix') or GET_ARGFLAG('--check'):
        missing_dynlib = tpl_rman.check_cpp_build()
        missing_dynlib += ibeis_rman.check_cpp_build()

        missing_install = tpl_rman.check_installed()
        missing_install += ibeis_rman.check_installed()

        problems = []
        problems += ibeis_rman.check_importable()
        problems += tpl_rman.check_importable()

    if GET_ARGFLAG('--fix'):
        print('Trying to fix problems')

        for repo in missing_dynlib:
            repo.custom_build()

        for repo, recommended_fix in problems:
            print('Trying to fix repo = %r' % (repo,))
            print(' * recommended_fix = %r' % (recommended_fix,))
            if recommended_fix == 'rebuild':
                repo.custom_build()
                print('Can currently only fix one module at a time. Please re-run')
                sys.exit(1)
            else:
                print('Not sure how to fix %r' % (repo,))

    if GET_ARGFLAG('--pull'):
        ibeis_rman.issue('git pull')

    if GET_ARGFLAG('--build'):
        # Build tpl repos
        tpl_rman.custom_build()
        ibeis_rman.custom_build()
        # Build only IBEIS repos with setup.py
        _rman = ibeis_rman.only_with_pysetup()
        _rman.issue('{pythoncmd} setup.py build'.format(pythoncmd=pythoncmd))

    # Like install, but better if you are developing
    if GET_ARGFLAG('--develop'):
        _rman = ibeis_rman.only_with_pysetup()
        # # _rman.issue('{pythoncmd} setup.py develop'.format(pythoncmd=pythoncmd),
        #               # sudo=not ut.in_virtual_env())
        _rman.issue('{pythoncmd} -m pip install -e .'.format(pythoncmd=pythoncmd),
                    sudo=not ut.in_virtual_env())

    if GET_ARGFLAG('--clean'):
        _rman = ibeis_rman.only_with_pysetup()
        _rman.issue('{pythoncmd} setup.py clean'.format(pythoncmd=pythoncmd))

    if GET_ARGFLAG('--install'):
        print('WARNING: Dont use install if you are a developer. Use develop instead.')
        _rman = ibeis_rman.only_with_pysetup()
        _rman.issue('python setup.py install'.format(pythoncmd=pythoncmd))

    if GET_ARGFLAG('--push'):
        ibeis_rman.issue('git push')

    if GET_ARGFLAG('--branch'):
        ibeis_rman.issue('git branch')
        sys.exit(0)

    if GET_ARGFLAG('--tag-status'):
        ibeis_rman.issue('git tag')

    # Tag everything
    tag_name = GET_ARGVAL('--newtag', type_=str, default=None)
    if tag_name is not None:
        ibeis_rman.issue('git tag -a "{tag_name}" -m "super_setup autotag {tag_name}"'.format(**locals()))
        ibeis_rman.issue('git push --tags')

    if GET_ARGFLAG('--bext'):
        ibeis_rman.issue('{pythoncmd} setup.py build_ext --inplace'.format(pythoncmd=pythoncmd))

    commit_msg = GET_ARGVAL('--commit', type_=str, default=None)
    if commit_msg is not None:
        ibeis_rman.issue('git commit -am "{commit_msg}"'.format(**locals()))

    # Change Branch
    branch_name = GET_ARGVAL('--checkout', type_=str, default=None)
    if branch_name is not None:
        try:
            ibeis_rman.issue('git checkout "{branch_name}"'.format(**locals()))
        except Exception:
            print('ERROR: Could not checkout branch: %r' % (branch_name, ))

    # Creates new branches
    newbranch_name = GET_ARGVAL('--newbranch', type_=str, default=None)
    if newbranch_name is not None:
        #rman.issue('git stash"'.format(**locals()))
        ibeis_rman.issue('git checkout -b "{newbranch_name}"'.format(**locals()))
        ibeis_rman.issue('git push --set-upstream origin {newbranch_name}'.format(**locals()))
        #rman.issue('git stash pop"'.format(**locals()))

    # Creates new branches
    newlocalbranch_name = GET_ARGVAL('--newlocalbranch', type_=str, default=None)
    if newlocalbranch_name is not None:
        #rman.issue('git stash"'.format(**locals()))
        ibeis_rman.issue('git checkout -b "{newlocalbranch_name}"'.format(**locals()))
        #rman.issue('git push --set-upstream origin {newlocalbranch_name}'.format(**locals()))
        #rman.issue('git stash pop"'.format(**locals()))

    # Creates new branches
    mergebranch_name = GET_ARGVAL('--merge', type_=str, default=None)
    if mergebranch_name is not None:
        ibeis_rman.issue('git merge "{mergebranch_name}"'.format(**locals()))

    # Change ownership
    if GET_ARGFLAG('--serverchmod'):
        ibeis_rman.issue('chmod -R 755 *')

    if GET_ARGFLAG('--chown'):
        # Fixes problems where repos are checked out as root
        username = os.environ.get('USERNAME', ut.get_argval('--username'))
        if username is None:
            username = os.environ.get('USER', None)
        if username is None:
            raise AssertionError('cannot find username in commandline or environment vars')
        usergroup = username
        ibeis_rman.issue('chown -R {username}:{usergroup} *'.format(**locals()),
                         sudo=True)

    upstream_branch = GET_ARGVAL('--set-upstream', type_=str, default=None)
    if upstream_branch is not None:
        # git 2.0
        ibeis_rman.issue('git branch --set-upstream-to=origin/{upstream_branch} {upstream_branch}'.format(**locals()))

    upstream_push = GET_ARGVAL('--upstream-push', type_=str, default=None)
    if upstream_push is not None:
        ibeis_rman.issue('git push --set-upstream origin {upstream_push}'.format(**locals()))

    if GET_ARGFLAG('--test'):
        failures = []
        for repo_dpath in ibeis_rman.repo_dirs:
            # ut.getp_
            mod_dpaths = ut.get_submodules_from_dpath(repo_dpath, recursive=False,
                                                      only_packages=True)
            modname_list = ut.lmap(ut.get_modname_from_modpath, mod_dpaths)
            print('Checking modules = %r' % (modname_list,))

            for modname in modname_list:
                try:
                    ut.import_modname(modname)
                    print(modname + ' success')
                except ImportError as ex:
                    failures += [modname]
                    print(modname + ' failure')

        print('failures = %s' % (ut.repr3(failures),))

    if False:
        try:
            from six.moves import input
        except ImportError:
            input = raw_input  # NOQA
        # General global git command
        gg_cmd = GET_ARGVAL('--gg', None)  # global command
        if gg_cmd is not None:
            ans = 'yes' if GET_ARGFLAG('-y') else input('Are you sure you want to run: %r on all directories? ' % (gg_cmd,))
            if ans == 'yes':
                ibeis_rman.issue(gg_cmd)


def is_running_as_root():
    """
    References:
        http://stackoverflow.com/questions/5721529/running-python-script-as-root
        http://stackoverflow.com/questions/2806897/checking-script-has-root
    """
    return os.getenv('USER') == 'root'


def get_sysinfo():
    print('USER = %r' % os.getenv("USER"))

    if is_running_as_root():
        print('Do not run super_setup.py as root')
        sys.exit(1)

    WIN32 = sys.platform.startswith('win32')

    print('[super_setup] __IBEIS_SUPER_SETUP__')

    if 'CODE_DIR' in os.environ:
        CODE_DIR = os.environ.get('CODE_DIR')
    else:
        CODE_DIR = dirname(dirname(realpath(__file__)))   # Home is where the .. is.  # '~/code'

    print('[super_setup] code_dir: %r' % CODE_DIR)
    (DISTRO, DISTRO_VERSION, DISTRO_TAG) = platform.dist()
    python_version = platform.python_version()

    PY2 = python_version.startswith('2.7')
    PY3 = python_version.startswith('3')
    # '--py3' in sys.argv
    # assert PY3 or
    #     'IBEIS currently supports python 2.7,  Instead got python=%r. use --py3 to override' % python_version

    pythoncmd = sys.executable
    # if PY2:
    #     pythoncmd = 'python' if WIN32 else 'python2.7'
    # elif PY3:
    #     pythoncmd = 'python3'
    return CODE_DIR, pythoncmd, WIN32, PY2, PY3


def main():
    print('''
    IBEIS Image Analysis (IA)
    ____ _  _ ___  ____ ____    ____ ____ ___ _  _ ___
    [__  |  | |__] |___ |__/    [__  |___  |  |  | |__]
    ___] |__| |    |___ |  \    ___] |___  |  |__| |
    ''')

    show_usage = len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']
    if show_usage:
        print(USAGE)

    CODE_DIR, pythoncmd, WIN32, PY2, PY3 = get_sysinfo()

    if '--bootstrap' in sys.argv or 'bootstrap' in sys.argv:
        bootstrap(WIN32)

    try:
        # HACK IN A WAY TO ENSURE UTOOL
        print('Checking utool')
        import utool as ut  # NOQA
    except Exception:
        ensure_utool(CODE_DIR, pythoncmd)

    tpl_rman, ibeis_rman = initialize_repo_managers(CODE_DIR, pythoncmd, PY2, PY3)
    execute_commands(tpl_rman, ibeis_rman)


if __name__ == '__main__':
    main()
