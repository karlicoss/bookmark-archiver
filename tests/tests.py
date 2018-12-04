#!/usr/bin/env python3
import json
import os
from os import listdir
from os.path import dirname, pardir, join, abspath
from subprocess import check_output, check_call
from tempfile import TemporaryDirectory
from typing import List

import pytest # type: ignore

ROOT = abspath(join(dirname(__file__), pardir))
ARCHIVER_BIN = join(ROOT, 'archive')

class Helper:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def run(self, links, env=None):
        if env is None:
            env = {}
        # we don't wanna spam archive.org witin our tests..
        env['SUBMIT_ARCHIVE_DOT_ORG'] = 'False'

        jj = []
        for url in links:
            jj.append({
                'href': url,
                'description': url,
            })
        input_json = join(self.output_dir, 'input.json')
        with open(input_json, 'w') as fo:
            json.dump(jj, fo)

        if env is None:
            env = {}
        env['OUTPUT_DIR'] = self.output_dir
        check_call(
            [ARCHIVER_BIN, input_json],
            env={**os.environ.copy(), **env},
        )


def extract_url(index_dir: str):
    ifile = join(index_dir, 'index.json')
    with open(ifile, 'r') as fo:
        j = json.load(fo)
        return j['url']


class TestArchiver:
    def setup(self):
        class DebugDir:
            name = 'debug'
        self.tdir = DebugDir()
        # self.tdir = TemporaryDirectory()
        self.helper = Helper(self.output_dir)

    def teardown(self):
        pass
        # self.tdir.cleanup()

    @property
    def output_dir(self):
        return self.tdir.name

    @pytest.mark.skip
    def test_fetch_favicon_false(self):
        """
        Regression test for crash on missing favicon https://github.com/pirate/bookmark-archiver/pull/114
        """
        self.helper.run(links=[
            'https://google.com',
        ], env={
            'FETCH_FAVICON': 'False',
        })
        # for now no asserts, good enough if it isn't failing

    # TODO for testing, just transform all my links to localhost??
    @pytest.mark.skip
    def test_3000_links(self):
        """
        The pages are deliberatly unreachable. The tool should gracefully process all of them even though individual links are failing.
        Regression test for https://github.com/pirate/bookmark-archiver/pull/115
        """
        links = [
            f'http://localhost:123/test_{i}.html' for i in range(3000)
        ]
        self.helper.run(links=links, env={
            # just try and fetch via wget
            'FETCH_FAVICON': 'False',
            'FETCH_SCREENSHOT': 'False',
            'FETCH_PDF': 'False',
            'FETCH_DOM': 'False',
            'CHECK_SSL_VALIDITY': 'False',
        })

        adir = join(self.output_dir, 'archive')
        archives = listdir(adir)
        assert len(archives) == len(links)

        archived = {extract_url(join(adir, a)) for a in sorted(archives)}
        assert archived == set(links)

    def test_double(self):
        links = [
            f'http://localhost:123/test_{i}.html' for i in range(10)
        ]
        self.helper.run(links=links, env={
            # just try and fetch via wget
            'FETCH_FAVICON': 'False',
            'FETCH_SCREENSHOT': 'False',
            'FETCH_PDF': 'False',
            'FETCH_DOM': 'False',
            'CHECK_SSL_VALIDITY': 'False',
        })

        self.helper.run(links=list(reversed(links)), env={
            # just try and fetch via wget
            'FETCH_FAVICON': 'False',
            'FETCH_SCREENSHOT': 'False',
            'FETCH_PDF': 'False',
            'FETCH_DOM': 'False',
            'CHECK_SSL_VALIDITY': 'False',
        })

        adir = join(self.output_dir, 'archive')
        archives = listdir(adir)
        assert len(archives) == len(links)

        archived = {extract_url(join(adir, a)) for a in sorted(archives)}
        assert archived == set(links)
        # TODO maybe, if we purge it gets overvritten??



if __name__ == '__main__':
    pytest.main([__file__])
