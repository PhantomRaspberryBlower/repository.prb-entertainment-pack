import re

import urlresolver # Resolves media file from url
import commontasks

__baseurl__ = 'http://fullmatchsports.com/'


def main_menu(title):
    # Shows menu items
    resp = commontasks.get_html(__baseurl__)
    content = commontasks.regex_from_to(resp, '<a title="' + title + '" ', '</ul></li>')
    menus = re.compile('<a target="_blank" rel="noopener noreferrer" href="(.+?)" '
                       'itemprop="url"><span itemprop="name">(.+?)</span></a></li>').findall(content)
    return menus


def submenu(url):
    submenus = []
    page = 1
    loop = True
    while loop == True:
        resp = commontasks.get_html(url + 'page/%d' % page)
        try:
            articles = re.compile('<article(.+?)</article>').findall(resp)
        except:
            articles = ''
            loop = False
        if len(articles) > 0:
            for article in articles:
                matches = re.compile('<a href="(.+?)" itemprop="url" title="Permalink to: (.+?)" '
                                     'rel="bookmark"><img width="(.+?)" height="(.+?)" src="(.+?)" '
                                     'class="(.+?)" alt="(.+?)" itemprop="image" title="(.+?)" /></a>').findall(article)
                for href, title, imgwidth, imgheight, img, clss, alt, img_title in matches:
                    title = title.replace('  ', '').strip()
                    submenus.append((href, title, img))
        page += 1
    return submenus


def get_links(url):
    linksmenus = []
    resp = commontasks.get_html(url)
    resp = commontasks.regex_from_to(resp, '<div class="streaming"', '<div class="tab-content"')
    matches = re.compile('<div class="tab-title(.+?)"><a href="(.+?)">(.+?)</a></div>').findall(resp)
    for junk, href, title in matches:
        if not ('720p' in title or '/' in title or 'LINKS' in title):
            title = title.replace(' HD 720p', '').replace(' HD 1080p', '')
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
    resp = commontasks.regex_from_to(resp, '<div class="tab-content">', '</div>')
    matches = re.compile('<iframe src="(.+?)"').findall(resp)
    try:
        resp = commontasks.get_html('https:' + str(matches[0]))
    except:
        commontasks.notification('No Streams! :(', 'No streams available!', xbmcgui.NOTIFICATION_INFO, 5000)
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

