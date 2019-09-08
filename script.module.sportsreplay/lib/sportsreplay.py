#!/usr/bin/python

import re
import urlresolver # Resolves media file from url
import commontasks as ct

# Written by: Phantom Raspberry Blower (The PRB)
# Date: 21-08-2019
# Description: Web scraper for capturing sports streams

# Define local variables
__baseurl__ = 'http://fullmatchsports.com/'
__alturl__ = 'https://fullmatch.net/'

sport_links = {'MotoGP Race': __baseurl__,
               'Formula 1 Race': __baseurl__,
               'Full Match Replay': __baseurl__,
               'MLB': __alturl__,
               'NBA': __alturl__,
               'NFL': __alturl__,
               'UFC': __alturl__}

def _menus(url, expstart, expend, regexp):
    resp = ct.get_html(url)
    content = ct.regex_from_to(resp, expstart, expend)
    return re.compile(regexp).findall(content)


def main_menu(title):
    # Shows menu items
    if (title == 'MotoGP Race') or (title == 'Formula 1 Race'):
        # Used for F1 and MotoGP
        return _menus(__baseurl__,
                       '<a title="%s" ' % title,
                       '</ul></li>',
                       '<a target="_blank" rel="noopener noreferrer"'
                       ' href="(.+?)" itemprop="url"><span itemprop='
                       '"name">(.+?)</span></a></li>')
    else:
        # Used for Full Match, MLB, NBA, NFL and UFC
        return _alt_main_menu(title)


def _alt_main_menu(title):
    main_menu = []
    sub_menu = []
    my_menus =[]
    mode = 1
    if title == 'Full Match Replay':
        # Full Match streams
        menus = _menus(__baseurl__,
                       '<a title="' + title + '" ',
                       '<li id="menu-item-54"',
                       '<li id="(.+?)" class="(.+?)"><a(.+?)href="#" '
                       'itemprop="url"><span itemprop="name">(.+?)</span></a>')
        nosubmenus = _menus(__baseurl__,
                       '<a title="' + title + '" ',
                       '<li id="menu-item-54"',
                       '<a target="_blank" rel="noopener noreferrer" href='
                       '"(.+?)" itemprop="url"><span itemprop="name">(.+?)</span></a>')
        for menu_item, clss, url, name in menus:
            main_menu.append((url, name, mode))
        mode = 2
        for href, name in nosubmenus:
            main_menu.append((href, name, mode))
    else:
        # NBA, NFL, MLB and UFC streams
        resp = ct.get_html(__alturl__)
        content = ct.regex_from_to(resp, '<div class="cactus-main-menu navigation-font">', '</div>')
        match1 = _menus(__alturl__,
                        '<div class="cactus-main-menu navigation-font">',
                        '</div>',
                        'main-menu-item menu-item-depth-0(.+?)</li>')
        for item in match1:
            content1 = ct.regex_from_to(item, '<a', '/a')
            match2 = re.compile('href="(.+?)" class="(.+?)>(.+?) <').findall(content1)
            for href1, junk1, title1 in match2:
                if '#' in href1:
                    content2 = ct.regex_from_to(content, title1 + ' <', '</ul>') + '</ul>'
                    content2 = ct.regex_from_to(content2, '<ul class="dropdown-menu menu-depth-1">', '</li></ul>')
                    match3 = re.compile('<a target="_blank" href="(.+?)" class="(.+?)">(.+?) </a>').findall(content2)
                    sub_menu = []
                    for href2, junk2, title2 in match3:
                        sub_menu.append({'title': title2, 'url': href2})
                if (title1 in title) or (title == 'All'):
                    my_menus.append((title1, href1, sub_menu))

    for item in my_menus:
        if item[1] == '#':
            for title in item[2]:
                main_menu.append((title['url'], title['title'], 1))
        else:
            main_menu.append((item[1], item[0], 2))

    return main_menu


def seasons(league):
    seasons = []
    menus = _menus(__baseurl__,
                   league + '</span>',
                   '</ul></li>',
                   '<li id="(.+?)" class="(.+?)"><a target="_blank" '
                   'rel="noopener noreferrer" href="(.+?)" itemprop='
                   '"url"><span itemprop="name">(.+?)</span></a></li>')
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


def submenu(url, thumb, items_per_page=40, currmode=2):
    fmatches = []
    item = 0
    nxtmode = currmode + 1
    if url.find('page/') > 0:
        pgnumf = url.find('page/') + 5
        pgnum = int(url[pgnumf:])
    else:
      pgnum = 1
    url = url.replace('page/%d' % pgnum, '')
    while item < items_per_page:
        resp = ct.get_html(url + 'page/%d' % pgnum)
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
                        fmatches.append((href, title, img, nxtmode))
                else:
                    matches = re.compile('<div class="picture-content " data-post-id="(.+?)"> '
                                         '<a href="(.+?)" target="_self" title="(.+?)"> <img (.+?) '
                                         'data-src="(.+?)" data-srcset=').findall(article)
                    for dpi, href, title, junk, img in matches:
                        title = title.replace('Replay', '').replace('NBA', '').replace('UFC', '')
                        title = title.replace('  ', ' ').strip()
                        fmatches.append((href, title, img, nxtmode))
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
            fmatches.append((nxtpgurl, '[COLOR green]>> Next page[/COLOR]', thumb, currmode))
        elif pgnum > 3:
            fmatches.append((url, "[COLOR orange]That's all folks!!![/COLOR]", thumb, 0))
    return fmatches


def get_links(url):
    linksmenus = []
    links = _menus(url,
                   '<div class="streaming"',
                   '<div class="tab-content"',
                   '<div class="tab-title(.+?)"><a href="(.+?)">(.+?)</a></div>')
    for junk, href, title in links:
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
                   ' NA': '([COLOR red]No longer available![/COLOR])',
                   'NA': ' ([COLOR red]No longer available![/COLOR])',
                   '  ': ' '}
    resp = ct.get_html(url)
    try:
        resp = ct.regex_from_to(resp, '<div class="tab-content">', '</div>')
        matches = re.compile('<iframe src="(.+?)"').findall(resp)
        resp = ct.get_html('https:' + str(matches[0]))
    except:
        try:
            resp = ct.regex_from_to(resp, '<div id="player-embed">', '</div>')
            matches = re.compile('<iframe (.+?) src="(.+?)"').findall(resp)
            resp = ct.get_html(matches[0][1])
            link = resp
        except:
            ct.notification('No Streams!',
                                     '[COLOR red]No streams available! :([/COLOR]',
                                     ct.xbmcgui.NOTIFICATION_INFO, 5000)
            return streams

    try:
        resp = ct.regex_from_to(resp, 'JuicyCodes.Run(', ');</script>')
        resp = 'JuicyCodes.Run%s)' % resp
        resp = ct.unjuice(resp)
        resp = ct.regex_from_to(resp, 'sources:', ',tracks:')
        matches = re.compile('{"file":"(.+?)","label":"(.+?)","type":"(.+?)"}').findall(resp)
        for url, label, stype in matches:
            for item in format_text:
                label = label.replace(item, format_text[item])
            streams.append((url, label))
    except:
        streams.append((matches[0][1], "Test"))
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
        ct.play(name, vidlink, thumb)
    else:
        ct.play(name, url, thumb)


def quote_plus(text):
    resp = ct.quote_plus(text)
    return resp


def unquote_plus(text):
    resp = ct.unquote_plus(text)
    return resp


def unquote(text):
    resp = ct.urllib.unquote(text)
    return resp

