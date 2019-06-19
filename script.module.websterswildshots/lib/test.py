#!/usr/bin/python
# -*- coding: utf-8 -*-

from websterswildshots import get_scrapers


def test():
    for scraper in get_scrapers():
        try:
            albums = scraper.get_albums()
        except Exception, e:
            print '=' * 80
            print 'get_albums Exception: %s' % e
            print '=' * 80
            continue
        for album in albums:
            try:
                scraper.get_photos(album.get('album_url'))
            except Exception, e:
                print '=' * 80
                print 'get_photos Exception: %s' % e
                print '=' * 80
                continue


if __name__ == '__main__':
    test()
