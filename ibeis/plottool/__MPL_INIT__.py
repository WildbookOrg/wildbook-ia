# -*- coding: utf-8 -*-
"""
Notes:
    To use various backends certian packages are required

    PyQt
    ...

    Tk
    pip install
    sudo apt-get install tk
    sudo apt-get install tk-dev

    Wx
    pip install wxPython

    GTK
    pip install PyGTK
    pip install pygobject
    pip install pygobject

    Cairo
    pip install pycairo
    pip install py2cairo
    pip install cairocffi
    sudo apt-get install libcairo2-dev


CommandLine:
    python -m plottool.draw_func2 --exec-imshow --show --mplbe=GTKAgg
    python -m plottool.draw_func2 --exec-imshow --show --mplbe=TkAgg
    python -m plottool.draw_func2 --exec-imshow --show --mplbe=WxAgg
    python -m plottool.draw_func2 --exec-imshow --show --mplbe=WebAgg
    python -m plottool.draw_func2 --exec-imshow --show --mplbe=gdk
    python -m plottool.draw_func2 --exec-imshow --show --mplbe=cairo

"""
from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import os
import utool as ut
ut.noinject(__name__, '[plottool.__MPL_INIT__]')


__IS_INITIALIZED__ = False
__WHO_INITIALIZED__ = None


VERBOSE_MPLINIT = ut.get_argflag(('--verb-mpl', '--verbose'))
TARGET_BACKEND = ut.get_argval(('--mpl-backend', '--mplbe'), type_=str, default=None)
FALLBACK_BACKEND = ut.get_argval(('--mpl-fallback-backend', '--mplfbbe'), type_=str, default='agg')


def print_all_backends():
    import matplotlib.rcsetup as rcsetup
    print(rcsetup.all_backends)
    valid_backends = [u'GTK', u'GTKAgg', u'GTKCairo', u'MacOSX', u'Qt4Agg',
                      u'Qt5Agg', u'TkAgg', u'WX', u'WXAgg', u'CocoaAgg',
                      u'GTK3Cairo', u'GTK3Agg', u'WebAgg', u'nbAgg', u'agg',
                      u'cairo', u'emf', u'gdk', u'pdf', u'pgf', u'ps', u'svg',
                      u'template']
    del valid_backends


def get_target_backend():
    if (not sys.platform.startswith('win32') and
        not sys.platform.startswith('darwin') and
         os.environ.get('DISPLAY', None) is None):
        # Write to files if we cannot display
        # target_backend = 'PDF'
        target_backend = FALLBACK_BACKEND
    else:
        target_backend = TARGET_BACKEND
        if target_backend is None:
            try:
                # This might be the cause of some issues
                try:
                    from guitool import __PYQT__  # NOQA
                except ImportError:
                    import PyQt4  # NOQA
                target_backend = 'Qt4Agg'
            except ImportError:
                print('[!plotttool] WARNING backend fallback to %s' % (FALLBACK_BACKEND, ))
                target_backend = FALLBACK_BACKEND
    return target_backend


def _init_mpl_rcparams():
    import matplotlib as mpl
    #from matplotlib import style
    if ut.get_argflag('--notoolbar'):
        toolbar = 'None'
    else:
        toolbar = 'toolbar2'
    mpl.rcParams['toolbar'] = toolbar
    #mpl.rc('text', usetex=False)
    #mpl.rc('text', usetex=True)
    mpl_keypress_shortcuts = [key for key in mpl.rcParams.keys() if key.find('keymap') == 0]
    for key in mpl_keypress_shortcuts:
        mpl.rcParams[key] = ''
    #mpl.style.use('ggplot')
    #mpl.rcParams['text'].usetex = False
    #for key in mpl_keypress_shortcuts:
    #    print('%s = %s' % (key, mpl.rcParams[key]))
    # Disable mpl shortcuts
    #    mpl.rcParams['toolbar'] = 'None'
    #    mpl.rcParams['interactive'] = True


def _mpl_set_backend(target_backend):
    import matplotlib as mpl
    if ut.get_argflag('--leave-mpl-backend-alone'):
        print('[pt] LEAVE THE BACKEND ALONE !!! was specified')
        print('[pt] not changing mpl backend')
    else:
        #mpl.use(target_backend, warn=True, force=True)
        mpl.use(target_backend, warn=True, force=False)
        #mpl.use(target_backend, warn=False, force=False)
        current_backend = mpl.get_backend()
    if not ut.QUIET and ut.VERBOSE:
        print('[pt] current backend is: %r' % current_backend)


def _init_mpl_mainprocess(verbose=VERBOSE_MPLINIT):
    global __IS_INITIALIZED__
    global __WHO_INITIALIZED__
    import matplotlib as mpl
    #mpl.interactive(True)
    current_backend = mpl.get_backend()
    target_backend = get_target_backend()
    if __IS_INITIALIZED__ is True:
        if verbose:
            print('[!plottool] matplotlib has already been initialized.  backend=%r' % current_backend)
            print('[!plottool] Initially initialized by %r' % __WHO_INITIALIZED__)
            print('[!plottool] Trying to be init by %r' % (ut.get_caller_name(N=range(0, 5))))
        return False
    __IS_INITIALIZED__ = True

    if verbose:
        print('[plottool] matplotlib initialized by %r' % __WHO_INITIALIZED__)
        __WHO_INITIALIZED__ = ut.get_caller_name(N=range(0, 5))
    if verbose:
        print('--- INIT MPL---')
        print('[pt] current backend is: %r' % current_backend)
        print('[pt] mpl.use(%r)' % target_backend)
    if current_backend != target_backend:
        _mpl_set_backend(target_backend)
    _init_mpl_rcparams()


def init_matplotlib(verbose=VERBOSE_MPLINIT):
    if ut.in_main_process():
        try:
            # This might be the cause of some issues
            from guitool import __PYQT__  # NOQA
        except ImportError:
            print('[!plotttool] WARNING guitool does not have __PYQT__')
            pass
        return _init_mpl_mainprocess(verbose=verbose)
