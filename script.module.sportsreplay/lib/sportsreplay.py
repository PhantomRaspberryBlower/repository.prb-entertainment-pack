#!/usr/bin/python

import re

import urlresolver # Resolves media file from url
import commontasks

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 21-08-2019
# Description: Web scraper for capturing sports streams

# Define local variables
__baseurl__ = 'http://fullmatchsports.com/'


def main_menu(title):
    # Shows menu items
    resp = commontasks.get_html(__baseurl__)
    content = commontasks.regex_from_to(resp, '<a title="' + title + '" ', '</ul></li>')
    menus = re.compile('<a target="_blank" rel="noopener noreferrer" href="(.+?)" '
                       'itemprop="url"><span itemprop="name">(.+?)</span></a></li>').findall(content)
    return menus


def main_menu_and_no_submenus(title):
    # Shows menu items and items with no submenus
    main_menus = []
    mode = 1
    resp = commontasks.get_html(__baseurl__)
    try:
        content = commontasks.regex_from_to(resp, '<a title="' + title + '" ', '<li id="menu-item-54"')
        menus = re.compile('<li id="(.+?)" class="(.+?)"><a(.+?)href="#" itemprop="url">'
                           '<span itemprop="name">(.+?)</span></a>').findall(content)
        nosubmenus = re.compile('<a target="_blank" rel="noopener noreferrer" href="(.+?)" itemprop="url">'
                           '<span itemprop="name">(.+?)</span></a>').findall(content)
        for menu_item, clss, url, name in menus:
            main_menus.append((url, name, mode))
    except:
        resp = commontasks.get_html('http://fullmatch.net/')
        content = commontasks.regex_from_to(resp, 'data-toggle="dropdown">' + title, 'data-toggle=')
        menus_content = commontasks.regex_from_to(content, '<ul class="dropdown-menu menu-depth-1">',
                                                               'parent dropdown-submenu">')
        nosubmenus_content = commontasks.regex_from_to(content, '<ul class="dropdown-menu menu-depth-2">',
                                                                  '</ul>')
        menus = re.compile('<a target="_blank" href="(.+?)" class="menu-link  sub-menu-link">(.+?)</a>').findall(menus_content)
        nosubmenus = re.compile('<a target="_blank" href="(.+?)" class="menu-link  sub-menu-link">(.+?)</a>').findall(nosubmenus_content)
        for url, name in menus:
            main_menus.append((url + 'page/1', name, mode))
    mode = 2
    for href, name in nosubmenus:
            main_menus.append((href, name, mode))
    return main_menus


def seasons(league):
    seasons = []
    resp = commontasks.get_html(__baseurl__)
    content = commontasks.regex_from_to(resp, league + '</span>', '</ul></li>')
    menus = re.compile('<li id="(.+?)" class="(.+?)"><a target="_blank" rel="noopener '
                       'noreferrer" href="(.+?)" itemprop="url"><span itemprop="name">'
                       '(.+?)</span></a></li>').findall(content)
    for menu_item, clss, url, name in menus:
        if url == '#':
            new_url = __baseurl__
            new_mode = None
            new_name = ''
        else:
            new_url = url
            new_mode = 2
            new_name = name
        seasons.append((new_name, new_url + 'page/1', new_mode))
    return seasons


def submenu(url, thumb, items_per_page=40):
    fmatches = []
    item = 0
    if url.find('page/') > 0:
        pgnumf = url.find('page/') + 5
        pgnum = int(url[pgnumf:])
    else:
      pgnum = 1
    url = url.replace('page/%d' % pgnum, '')
    while item < items_per_page:
        resp = commontasks.get_html(url + 'page/%d' % pgnum)
        try:
            articles = re.compile('<article(.+?)</article>').findall(resp)
        except:
            articles = ''
        if len(articles) > 0:
            for article in articles:
                item += 1
                matches = re.compile('<a href="(.+?)" itemprop="url" title="Permalink to: (.+?)" rel="bookmark">'
                                     '<img width="(.+?)" height="(.+?)" src="(.+?)" class="(.+?)" alt="(.+?)" '
                                     'itemprop="image" title="(.+?)" /></a>').findall(article)
                if matches:
                    for href, title, imgwidth, imgheight, img, clss, alt, img_title in matches:
                        title = title.replace('Full Match', '').replace('FULL MATCH', '').replace('Highlights', '').strip()
                        title = title.replace('  ', '').strip()
                        mode = None
                        fmatches.append((href, title, img, mode))
                else:
                    matches = re.compile('<div class="picture-content " data-post-id="(.+?)"> '
                                         '<a href="(.+?)" target="_self" title="(.+?)"> <img (.+?) '
                                         'data-src="(.+?)" data-srcset=').findall(article)
                    mode = 2
                    for dpi, href, title, junk, img in matches:
                        title = title.replace('Replay', '').replace('NBA', '').replace('  ', ' ').strip()
                        fmatches.append((href, title, img, mode))
        else:
            break
        pgnum += 1
    url = url + 'page/%d' % (pgnum - 1)
    if url.find('page/') > 0:
        pgnumf = url.find('page/') + 5
        pgnum = int(url[pgnumf:]) + 1
        nxtpgurl = url[:pgnumf]
        nxtpgurl = "%s%s" % (nxtpgurl, pgnum)
        if item < 1 and pagenum <= 1:
            fmatches.append((url, '[COLOR red]No streams available! :([/COLOR]', thumb, 0))
        if item >= items_per_page:
            fmatches.append((nxtpgurl, '[COLOR green]>> Next page[/COLOR]', thumb, 2))
        elif pgnum > 3:
            fmatches.append((url, "[COLOR orange]That's all folks!!![/COLOR]", thumb, 0))
    return fmatches


def get_links(url):
    linksmenus = []
    resp = commontasks.get_html(url)
    resp = commontasks.regex_from_to(resp, '<div class="streaming"', '<div class="tab-content"')
    matches = re.compile('<div class="tab-title(.+?)"><a href="(.+?)">(.+?)</a></div>').findall(resp)
    for junk, href, title in matches:
        if not ('720p' in title or '/' in title or 'LINKS' in title):
            title = title.replace(' HD 720p', '').replace(' HD 1080p', '').replace('HD', '').replace(' 1080p', '').replace('BTSport', '').replace('&#8211;', '')
            linksmenus.append((href, title))
    return linksmenus


def get_streams(url):
    streams = []
    format_text = {'1080P': '([COLOR orange]1080[/COLOR])',
                   '720P': '([COLOR orange]720[/COLOR])',
                   '480P': '([COLOR orange]480[/COLOR])',
                   '360P': '([COLOR orange]360[/COLOR])',
                   ' NA': ' ([COLOR red]No longer available![/COLOR])'}
    resp = commontasks.get_html(url)
    try:
        resp = commontasks.regex_from_to(resp, '<div class="tab-content">', '</div>')
        matches = re.compile('<iframe src="(.+?)"').findall(resp)
        resp = commontasks.get_html('https:' + str(matches[0]))
    except:
        try:
            resp = commontasks.regex_from_to(resp, '<div id="player-embed">', '</div>')
            matches = re.compile('<iframe (.+?) src="(.+?)"').findall(resp)
            resp = commontasks.get_html(matches[0][1])
        except:
            commontasks.notification('No Streams!', '[COLOR red]No streams available! :([/COLOR]', commontasks.xbmcgui.NOTIFICATION_INFO, 5000)
            return streams
    resp = commontasks.regex_from_to(resp, 'JuicyCodes.Run(', ');</script>')
    resp = 'JuicyCodes.Run%s)' % resp
    resp = commontasks.unjuice(resp)
    resp = commontasks.regex_from_to(resp, 'sources:', ',tracks:')
    matches = re.compile('{"file":"(.+?)","label":"(.+?)","type":"(.+?)"}').findall(resp)
    for url, label, stype in matches:
        for item in format_text:
            label = label.replace(item, format_text[item])
        streams.append((url, label))
    return streams


def play_stream(name, url, thumb):
    sources = []
    label = name
    format_text = [' ([COLOR orange]',
                   '[/COLOR])',
                   '1080',
                   '720',
                   '480',
                   '360']

    hosted_media = urlresolver.HostedMediaFile(url=url,title=name)
    sources.append(hosted_media)
    source = urlresolver.choose_source(sources)
    for item in format_text:
        name = name.replace(item, '')
    if source:
        vidlink = source.resolve()
        commontasks.play(name, vidlink, thumb)
    else:
        commontasks.play(name, url, thumb)


def quote_plus(text):
    resp = commontasks.quote_plus(text)
    return resp


def unquote_plus(text):
    resp = commontasks.unquote_plus(text)
    return resp


def unquote(text):
    resp = commontasks.urllib.unquote(text)
    return resp

