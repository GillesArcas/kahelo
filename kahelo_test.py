"""
Test suite for kahelo.
$ ./kahelo_test.py
"""

from __future__ import print_function

import os
import sys
import shutil
import subprocess

import kahelo


def main():
    if len(sys.argv) != 1:
        print(__doc__)
        exit(1)

    db_name = 'tests/easter.db'

    if os.name == 'nt':
        mode = 4
    else:
        mode = 3

    if mode == 1:
        # no window for subprocess, traces from server mixed with traces from client
        shell = False
        creationflags = 0
    elif mode == 2:
        # window for subprocess (windows only)
        shell = False
        creationflags = subprocess.CREATE_NEW_CONSOLE
    elif mode == 3:
        # no window for subprocess, traces from server mixed with traces from client
        shell = True
        creationflags = 0
    elif mode == 4:
        # no window for subprocess, no mixed traces (windows only)
        shell = True
        creationflags = subprocess.CREATE_NEW_CONSOLE

    p = subprocess.Popen('python ./kahelo.py -server tests/easter.db', shell=shell, creationflags=creationflags)
    url = kahelo.server_url() + '/{zoom}/{x}/{y}.jpg'

    # make sure tests are done with known configuration
    config_filename = kahelo.configfilename()
    shutil.move(config_filename, config_filename + '.backup')
    kahelo.createconfig(config_filename, kahelo.DEFAULTS)

    try:
        define_tile_sets()

        for db1 in ('kahelo', 'rmaps', 'folder', 'maverick'):
            for db2 in ('kahelo', 'rmaps', 'folder', 'maverick'):
                print('---', db1, db2)
                test_db(url, db1, 'server', db2, 'png', trace='-verbose') # jpg
        
        test_db(url, 'rmaps', 'server', 'maverick', 'jpg', trace='-quiet')
        test_db(url, 'rmaps', 'server', 'maverick', 'jpg', trace='-verbose')

        test_stat()
        test_view()
        test_contours()
        test_tile_coords(db_name)
        test_zoom_subdivision(url)
        test_inside()

        if test_result is True:
            print('All tests ok.')
        else:
            print('Failure...')

    finally:
        kahelo.stop_server()
        os.remove('test.gpx')
        os.remove('test2.gpx')
        os.remove('test.project')
        shutil.move(config_filename + '.backup', config_filename)


GPX1 = """\
<?xml version="1.0"?>
<gpx version="1.0" xmlns="http://www.topografix.com/GPX/1/0">
    <trk>
        <trkseg>
            <trkpt lat="-27.0572913" lon="-109.3805695"></trkpt>
            <trkpt lat="-27.1801341" lon="-109.4464874"></trkpt>
            <trkpt lat="-27.1068114" lon="-109.2312241"></trkpt>
        </trkseg>
    </trk>
</gpx>
"""

GPX2 = """\
<?xml version="1.0"?>
<gpx version="1.0" xmlns="http://www.topografix.com/GPX/1/0">
    <trk>
        <trkseg>
            <trkpt lat="-27.1401181" lon="-109.4351578"></trkpt>
            <trkpt lat="-27.1813558" lon="-109.4633102"></trkpt>
            <trkpt lat="-27.2067017" lon="-109.4258881"></trkpt>
            <trkpt lat="-27.1740257" lon="-109.3949890"></trkpt>
        </trkseg>
    </trk>
    <trk>
        <trkseg>
            <trkpt lat="-27.0863335" lon="-109.2755127"></trkpt>
            <trkpt lat="-27.0887788" lon="-109.2284775"></trkpt>
            <trkpt lat="-27.1260632" lon="-109.2350006"></trkpt>
            <trkpt lat="-27.1275910" lon="-109.2689896"></trkpt>
        </trkseg>
    </trk>
</gpx>
"""

PROJECT = """
-track test.gpx -zoom 10-11
-contour test.gpx -zoom 12
"""


def define_tile_sets():
    # for reference, number of tiles for test track
    #             10      11      12      13      14
    # track        4       9      11      23      41
    # contour      4       9      12      25      57

    with open('test.gpx', 'wt') as f:
        f.writelines(GPX1)

    with open('test2.gpx', 'wt') as f:
        f.writelines(GPX2)

    with open('test.project', 'wt') as f:
        f.writelines(PROJECT)


# Helpers


test_number = 0
test_result = True
def check(msg, boolean):
    global test_number, test_result
    test_number += 1
    if boolean is False:
        print('Error on test #%d: %s' % (test_number, msg))
        test_result = False
        sys.exit(1)
    else:
        print('Test #%d: %s OK' % (test_number, msg))


def compare_files(name1, name2):
    with open(name1, 'rb') as f:
        x1 = f.read()
    with open(name2, 'rb') as f:
        x2 = f.read()
    #return x1 == x2
    if len(x1) != len(x2):
        print('File sizes are different', name1, len(x1), name2, len(x2))
        return False
    else:
        r = True
        for i, c in enumerate(x1):
            if c != x2[i]:
                r = False
                print(i, c, x2[i])
        return r


def compare_texts(name1, name2):
    with open(name1) as f:
        lines1 = f.read().splitlines()
    with open(name2) as f:
        lines2 = f.read().splitlines()
    for index, (line1, line2) in enumerate(zip(lines1, lines2)):
        if line1 != line2:
            print('Lines #%d are different in file %s and file %s' % (index, name1, name2))
            return False
    return True


def remove_db(db):
    if os.path.isfile(db):
        os.remove(db)
    elif os.path.isdir(db):
        shutil.rmtree(db)
    else:
        pass
    if os.path.isfile(db + '.properties'):
        os.remove(db + '.properties')


def clean():
    remove_db('test.db')
    remove_db('test2.db')
    remove_db('test3.db')
    remove_db('test4.db')
    for x in ('test1.png', 'test2.png'):
        if os.path.isfile(x):
            os.remove(x)


# Tests


def test_db(url, db_format, tile_format, db_dest_format, tile_dest_format, trace=''):
    # be sure context is clean
    clean()

    # describe test databases
    kahelo.kahelo('-describe test.db  -db %s -tile_f %s -url %s %s' % (db_format, tile_format, url, trace))
    kahelo.kahelo('-describe test2.db -db %s -tile_f %s -url %s %s' % (db_dest_format, tile_dest_format, url, trace))
    kahelo.kahelo('-describe test3.db -db %s -tile_f %s -url %s %s' % (db_dest_format, tile_dest_format, url, trace))
    kahelo.kahelo('-describe test4.db -db %s -tile_f %s -url %s %s' % (db_dest_format, tile_dest_format, url, trace))

    # check counting on empty databases
    stat = kahelo.kahelo('-count test.db -zoom 10-11 -track test.gpx %s' % trace)
    check('test_db 1', stat == (13, 0, 0, 13))
    stat = kahelo.kahelo('-count test.db -zoom 12 -contour test.gpx %s' % trace)
    check('test_db 2', stat == (12, 0, 0, 12))
    stat = kahelo.kahelo('-count test.db -project test.project %s' % trace)
    check('test_db 3', stat == (25, 0, 0, 25))

    # insert some track and contour
    kahelo.kahelo('-insert test.db -zoom 10-11 -track test.gpx %s' % trace)
    kahelo.kahelo('-insert test.db -zoom 12 -contour test.gpx %s' % trace)

    # check counting after insertion
    stat = kahelo.kahelo('-count test.db -project test.project %s' % trace)
    check('test_db 4', stat == (25, 25, 0, 0))
    stat = kahelo.kahelo('-count test.db -records %s' % trace)
    check('test_db 5', stat == (25, 25, 0, 0))
    stat = kahelo.kahelo('-count test.db -records -zoom 10,11,12 %s' % trace)
    check('test_db 6', stat == (25, 25, 0, 0))

    # export using various tile sets
    kahelo.kahelo('-import test2.db -track test.gpx   -zoom 10-11 -source test.db %s' % trace)
    kahelo.kahelo('-import test2.db -contour test.gpx -zoom 12    -source test.db %s' % trace)
    kahelo.kahelo('-export test.db  -project test.project         -dest test3.db %s' % trace)
    kahelo.kahelo('-export test.db  -records                      -dest test4.db %s' % trace)

    # check counts by using count_tiles and list_tiles methods
    db2 = kahelo.db_factory('test2.db')
    db3 = kahelo.db_factory('test3.db')
    db4 = kahelo.db_factory('test4.db')
    zooms = list(range(0, 21))
    check('7', db2.count_tiles(zooms) == db3.count_tiles(zooms))
    check('8', db2.count_tiles(zooms) == db4.count_tiles(zooms))
    check('9', set(db2.list_tiles(zooms)) == set(db3.list_tiles(zooms)))
    check('10', set(db2.list_tiles(zooms)) == set(db4.list_tiles(zooms)))
    db2.close()
    db3.close()
    db4.close()

    # delete all tiles
    kahelo.kahelo('-delete test2.db -zoom 10-11 -track test.gpx %s' % trace)
    kahelo.kahelo('-delete test2.db -zoom 12  -contour test.gpx %s' % trace)
    kahelo.kahelo('-delete test3.db -project test.project %s' % trace)
    kahelo.kahelo('-delete test4.db -records %s' % trace)

    # check counts by using count_tiles and list_tiles methods
    db2 = kahelo.db_factory('test2.db')
    db3 = kahelo.db_factory('test3.db')
    db4 = kahelo.db_factory('test4.db')
    zooms = range(0, 21)
    check('12', db2.count_tiles(zooms) == db3.count_tiles(zooms))
    check('13', db2.count_tiles(zooms) == db4.count_tiles(zooms))
    check('14', set(db2.list_tiles(zooms)) == set(db3.list_tiles(zooms)))
    check('15', set(db2.list_tiles(zooms)) == set(db4.list_tiles(zooms)))
    db2.close()
    db3.close()
    db4.close()

    clean()


def test_view():
    kahelo.resetconfig()
    kahelo.setconfig('view', 'draw_tracks', 'False')
    kahelo.setconfig('view', 'draw_tile_limits', 'False')
    kahelo.setconfig('view', 'draw_tile_width', 'False')
    kahelo.setconfig('view', 'draw_circles', 'False')
    kahelo.kahelo('-view tests/easter.db -zoom 12 -project test.project -image test.png')
    check('check view 1', compare_files(os.path.join('tests', 'easter12a.png'), 'test.png'))
    kahelo.kahelo('-view tests/easter.db -zoom 12 -project test.project -image test.jpg')
    check('check view 1', compare_files(os.path.join('tests', 'easter12a.jpg'), 'test.jpg'))

    kahelo.setconfig('view', 'draw_tracks', 'True')
    kahelo.kahelo('-view tests/easter.db -zoom 12 -project test.project -image test.png')
    check('check view 1', compare_files(os.path.join('tests', 'easter12b.png'), 'test.png'))
    kahelo.kahelo('-view tests/easter.db -zoom 12 -project test.project -image test.jpg')
    check('check view 1', compare_files(os.path.join('tests', 'easter12b.jpg'), 'test.jpg'))

    kahelo.setconfig('view', 'draw_tile_limits', 'True')
    kahelo.kahelo('-view tests/easter.db -zoom 12 -project test.project -image test.png')
    check('check view 1', compare_files(os.path.join('tests', 'easter12c.png'), 'test.png'))
    kahelo.kahelo('-view tests/easter.db -zoom 12 -project test.project -image test.jpg')
    check('check view 1', compare_files(os.path.join('tests', 'easter12c.jpg'), 'test.jpg'))

    kahelo.setconfig('view', 'draw_tile_width', 'True')
    kahelo.kahelo('-view tests/easter.db -zoom 12 -project test.project -image test.png')
    check('check view 1', compare_files(os.path.join('tests', 'easter12d.png'), 'test.png'))
    kahelo.kahelo('-view tests/easter.db -zoom 12 -project test.project -image test.jpg')
    check('check view 1', compare_files(os.path.join('tests', 'easter12d.jpg'), 'test.jpg'))

    kahelo.setconfig('view', 'draw_circles', 'True')
    kahelo.kahelo('-view tests/easter.db -zoom 12 -project test.project -image test.png')
    check('check view 1', compare_files(os.path.join('tests', 'easter12e.png'), 'test.png'))
    kahelo.kahelo('-view tests/easter.db -zoom 12 -project test.project -image test.jpg')
    check('check view 1', compare_files(os.path.join('tests', 'easter12e.jpg'), 'test.jpg'))

    os.remove('test.png')
    os.remove('test.jpg')


def test_stat():
    temp = sys.stdout
    with open('test.txt', 'wt') as sys.stdout:
        try:
            kahelo.kahelo('-stat ./tests/easter.db -quiet -records')
            kahelo.kahelo('-stat ./tests/easter.db -quiet -project test.project')
            kahelo.kahelo('-stat ./tests/easter.db -quiet -track test.gpx -zoom 10-11')
            kahelo.kahelo('-stat ./tests/easter.db -quiet -track test2.gpx -zoom 10-12')
        finally:
            sys.stdout = temp
    check('check stat', compare_texts('tests/test_stat.txt', 'test.txt'))
    os.remove('test.txt')


def test_contours():
    # test -contour versus -contours
    kahelo.kahelo('-describe test.db -db kahelo')
    stat1 = []
    stat2 = []
    for zoom in range(10, 17):
        stat1.append(kahelo.kahelo('-count test.db -zoom %d -contour  test2.gpx' % zoom)[0])
        stat2.append(kahelo.kahelo('-count test.db -zoom %d -contours test2.gpx' % zoom)[0])

    check('-contour', stat1 == [4, 10, 12, 22, 51, 128, 384])
    check('-contours', stat2 == [4, 10, 12, 20, 35, 82, 225])

    remove_db('test.db')


def test_tile_coords(db_name):
    for zoom in range(1, 9):
        max = 2 ** zoom - 1
        stat1 = kahelo.kahelo('-count %s -quiet -records -zoom %d' % (db_name, zoom))
        stat2 = kahelo.kahelo('-count %s -quiet -tiles 0,0,%d,%d  -zoom %d' % (db_name, max, max, zoom))
        print(stat1, stat2)
        check('-tiles', stat1[1:-1] == stat2[1:-1])


def test_zoom_subdivision(url):
    kahelo.kahelo('-describe test.db -db kahelo -tile_ jpg -url %s' % url)
    kahelo.kahelo('-insert test.db -zoom 10-12 -track test.gpx')
    stat = kahelo.kahelo('-count test.db -zoom 10 -track test.gpx')
    check('subdiv1', stat == (4, 4, 0, 0))
    stat = kahelo.kahelo('-count test.db -zoom 11 -track test.gpx')
    check('subdiv2', stat == (9, 9, 0, 0))
    stat = kahelo.kahelo('-count test.db -zoom 12 -track test.gpx')
    check('subdiv3', stat == (11, 11, 0, 0))
    stat = kahelo.kahelo('-count test.db -zoom 11/10 -track test.gpx')
    check('subdiv4', stat == (16, 9, 0, 7))
    stat = kahelo.kahelo('-count test.db -zoom 12/10 -track test.gpx')
    check('subdiv5', stat == (64, 11, 0, 53))
    stat = kahelo.kahelo('-count test.db -zoom 12/11 -track test.gpx')
    check('subdiv6', stat == (36, 11, 0, 25))
    stat = kahelo.kahelo('-count test.db -zoom 12/12 -track test.gpx')
    check('subdiv7', stat == (11, 11, 0, 0))
    remove_db('test.db')


def test_inside():
    """
    -inside limits de tile set to the tiles defined by the tile set in the 
    command line and already in the datebase.
    """
    temp = sys.stdout
    with open('test.txt', 'wt') as sys.stdout:
        try:
            # define tile coordinates of the test database
            kahelo.kahelo('-count ./tests/easter.db -quiet -zoom 14 -tiles 3210,9471,3221,9479')
            # one tile more on each side
            kahelo.kahelo('-count ./tests/easter.db -quiet -zoom 14 -tiles 3209,9470,3222,9480')
            # limiting to content, should be the same as first count
            kahelo.kahelo('-count ./tests/easter.db -quiet -zoom 14 -tiles 3209,9470,3222,9480 -inside')
        finally:
            sys.stdout = temp
    check('check inside', compare_texts('tests/test_inside.txt', 'test.txt'))
    os.remove('test.txt')

    
if __name__ == '__main__':
    main()
