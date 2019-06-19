#!/usr/bin/python
# -*- coding: utf-8 -*-

import random
from scrapers import ALL_SCRAPERS, get_scrapers

try:
    import xbmc
    XBMC_MODE = True
except ImportError:
    XBMC_MODE = False


class ScraperManager(object):

    def __init__(self, enabled_scrapers=None):
        self.log('__init__ with enabled_scrapers: %s' % enabled_scrapers)
        self._scrapers = get_scrapers(enabled_scrapers)
        self._current_index = 0
        self._num_scrapers = len(self._scrapers)

    def __del__(self):
        self.log('__del__')

    def next(self):
        if self._current_index + 1 < self._num_scrapers:
            self._current_index += 1
        else:
            self._current_index = 0
        self.log('switch_to_next id=%d' % self._current_index)

    def previous(self):
        if self._current_index > 0:
            self._current_index -= 1
        else:
            self._current_index = self._num_scrapers - 1
        self.log('switch_to_previous id=%d' % self._current_index)

    def switch(self, given_id):
        if given_id > 0 and given_id < self._num_scrapers:
            self._current_index = given_id
        self.log('switch_to_given_id id=%d' % self._current_index)

    def shuffle(self):
        random.shuffle(self._scrapers)

    def get_scrapers(self):
        scrapers = [{
            'id': scraper.id,
            'title': scraper.title
        } for scraper in self._scrapers]
        return scrapers

    def get_albums(self, scraper_id=None):
        if scraper_id is not None:
            self._current_index = scraper_id
        albums = self.current_scraper.get_albums()
        self.log('get_albums got %d items' % len(albums))
        return albums

    def get_photos(self, album_url, scraper_id=None):
        if scraper_id is not None:
            self._current_index = scraper_id
        photos = self.current_scraper.get_photos(album_url)
        self.log('get_photos got %d items' % len(photos))
        return photos

    @property
    def current_scraper_id(self):
        return self._current_index

    @property
    def num_scrapers(self):
        return self._num_scrapers

    @property
    def current_scraper(self):
        return self._scrapers[self._current_index]

    def log(self, msg):
        if XBMC_MODE:
            xbmc.log('WebstersWildshots Manager: %s' % msg)
        else:
            print('WebstersWildshots Manager: %s' % msg)


def test():
    scraper_manager = ScraperManager()
    for i in xrange(scraper_manager.num_scrapers):
        scraper_manager.switch(i)
        for album in scraper_manager.get_albums():
            album_url = album['album_url']
            photos = scraper_manager.get_photos(album_url)
