#!/usr/bin/env python
# TODO: ADD COPYRIGHT TAG
from __future__ import absolute_import, division, print_function
from ibeis.tests import __testing__
import multiprocessing
import utool
from ibeis import viz
from plottool import draw_func2 as df2
print, print_, printDBG, rrr, profile = utool.inject(__name__, '[TEST_VIZ]')


def TEST_VIZ(ibs):
    valid_gids = ibs.get_valid_gids()
    valid_rids = ibs.get_valid_rids()

    print('''
    * len(valid_rids) = %r
    * len(valid_gids) = %r
    ''' % (len(valid_rids), len(valid_gids)))
    assert len(valid_gids) > 0, 'database images cannot be empty for test'
    gindex = int(utool.get_arg('--gx', default=0))
    gid = valid_gids[gindex]
    rid_list = ibs.get_image_rids(gid)
    rindex = int(utool.get_arg('--rx', default=0))
    rid = rid_list[rindex]
    qrid = rid
    sel_rids = rid_list[1:3]
    rid = rid_list[-1]

    try:
        qres = ibs.query_database([qrid])[qrid]
        top_rids = qres.get_top_rids(ibs)
        assert len(top_rids) > 0, 'Results seems to be empty'
        rid2 = top_rids[0]  # 294
        query_failed = False
    except Exception as ex:
        query_failed = True
        utool.printex(ex, 'QUERY FAILED!')

    #----------------------
    #print('Show Image')
    viz.show_image(ibs, gid, sel_rids=sel_rids, fnum=1)
    df2.set_figtitle('Show Image')

    #----------------------
    #print('Show Chip')
    kpts_kwgs = dict(ell=True, ori=True, rect=True,
                     eig=True, pts=False, kpts_subset=10)
    viz.show_chip(ibs, rid, in_image=False, fnum=2, **kpts_kwgs)
    df2.set_figtitle('Show Chip (normal)')
    viz.show_chip(ibs, rid, in_image=True, fnum=3, **kpts_kwgs)
    df2.set_figtitle('Show Chip (in_image)')

    #----------------------
    if not query_failed:
        print('Show Query')
        viz.show_matches(ibs, qres, rid2, fnum=4)
        df2.set_figtitle('Show Chipres')

        viz.show_qres(ibs, qres, fnum=5)
        df2.set_figtitle('Show QRes')

    ##----------------------
    print('return test locals')
    return locals()


if __name__ == '__main__':
    multiprocessing.freeze_support()  # For windows
    main_locals = __testing__.main(defaultdb='testdb0')
    ibs = main_locals['ibs']    # IBEIS Control
    test_locals = __testing__.run_test(TEST_VIZ, ibs)
    execstr     = __testing__.main_loop(test_locals)
    exec(execstr)
