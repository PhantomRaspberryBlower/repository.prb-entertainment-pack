import urllib2
import json

# Written by: Phantom Raspberry Blower
# Date: 21-02-2017
# Description: Module for downloading information about music artists

FANART_URL = 'http://www.theaudiodb.com/api/v1/json/1/search.php?s='
#FANART_URL = 'https://www.theaudiodb.com/api/195003/json/1/search.php?s='


class ArtistInfo:

    def __init__(self, artist=None):
        self.clear()
        self.__artist_name = artist
        print str(artist)
        if artist is not None:
            self.get_artist_info(artist)
            print str(artist)

    @property
    def artist_id(self):
        return self.__artist_id

    @property
    def artist_name(self):
        return self.__artist_name

    @property
    def artist_aka(self):
        return self.__artist_aka

    @property
    def rec_label(self):
        return self.__rec_label

    @property
    def rec_label_id(self):
        return self.__rec_label_id

    @property
    def year_formed(self):
        return self.__year_formed

    @property
    def year_born(self):
        return self.__year_born

    @property
    def year_died(self):
        return self.__year_died

    @property
    def disbanded(self):
        return self.__disbanded

    @property
    def style(self):
        return self.__style

    @property
    def genre(self):
        return self.__genre

    @property
    def mood(self):
        return self.__mood

    @property
    def website(self):
        return self.__website

    @property
    def facebook(self):
        return self.__facebook

    @property
    def twitter(self):
        return self.__twitter

    @property
    def biography_en(self):
        return self.__biography_en

    @property
    def biography_de(self):
        return self.__biography_de

    @property
    def biography_fr(self):
        return self.__biography_fr

    @property
    def biography_cn(self):
        return self.__biography_cn

    @property
    def biography_it(self):
        return self.__biography_it

    @property
    def biography_jp(self):
        return self.__biography_jp

    @property
    def biography_ru(self):
        return self.__biography_ru

    @property
    def biography_es(self):
        return self.__biography_es

    @property
    def biography_pt(self):
        return self.__biography_pt

    @property
    def biography_se(self):
        return self.__biography_se

    @property
    def biography_nl(self):
        return self.__biography_nl

    @property
    def biography_hu(self):
        return self.__biography_hu

    @property
    def biography_no(self):
        return self.__biography_np

    @property
    def biography_il(self):
        return self.__biography_il

    @property
    def biography_pl(self):
        return self.__biography_pl

    @property
    def gender(self):
        return self.__gender

    @property
    def members(self):
        return self.__members

    @property
    def country(self):
        return self.__country

    @property
    def country_code(self):
        return self.__country_code

    @property
    def artist_thumb(self):
        return self.__artist_thumb

    @property
    def artist_logo(self):
        return self.__artist_logo

    @property
    def fanart(self):
        return self.__fanart

    @property
    def fanart2(self):
        return self.__fanart2

    @property
    def fanart3(self):
        return self.__fanart3

    @property
    def banner(self):
        return self.__banner

    @property
    def music_brainz_id(self):
        return self.__music_brainz_id

    @property
    def last_fm_chart(self):
        return self.__last_fm_chart

    @property
    def locked(self):
        return self.__locked

    def clear(self):
        self.__artist_id = None
        self.__artist_name = None
        self.__artist_aka = None
        self.__rec_label = None
        self.__rec_label_id = None
        self.__year_formed = None
        self.__year_born = None
        self.__year_died = None
        self.__disbanded = None
        self.__style = None
        self.__genre = None
        self.__mood = None
        self.__website = None
        self.__facebook = None
        self.__twitter = None
        self.__biography_en = None
        self.__biography_de = None
        self.__biography_fr = None
        self.__biography_cn = None
        self.__biography_it = None
        self.__biography_jp = None
        self.__biography_ru = None
        self.__biography_es = None
        self.__biography_pt = None
        self.__biography_se = None
        self.__biography_nl = None
        self.__biography_hu = None
        self.__biography_no = None
        self.__biography_il = None
        self.__biography_pl = None
        self.__gender = None
        self.__members = None
        self.__country = None
        self.__country_code = None
        self.__artist_thumb = None
        self.__artist_logo = None
        self.__fanart = None
        self.__fanart2 = None
        self.__fanart3 = None
        self.__banner = None
        self.__fanart = None
        self.__music_brainz_id = None
        self.__last_fm_chart = None
        self.locked = None

    def _common_tasks(self, url):
        """
        Download url and return result
        """
#        req = urllib2.urlopen(url)
        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding': 'none',
               'Accept-Language': 'en-US,en;q=0.8',
               'Connection': 'keep-alive'}
        req = urllib2.Request(url, headers=hdr)
        response = urllib2.urlopen(req)
        json_string = response.read()
        parsed_json = json.loads(json_string)
        return parsed_json

    def _url_encode(self, text):
        """
        Encode html ie. %26 = &
        """
        return (urllib2.quote(text.replace('and', '&'), safe='')
                .replace('%20', '+'))

    def _artist_info(self, artist):
        """
        Parse artist information and return a dictionary of items
        """
        url = (FANART_URL + self._url_encode(artist))
        try:
            parsed_json = self._common_tasks(url)
            self.__artist_id = parsed_json['artists'][0]['idArtist']
            self.__artist_name = parsed_json['artists'][0]['strArtist']
            self.__artist_aka = parsed_json['artists'][0]['strArtistAlternate']
            self.__rec_label = parsed_json['artists'][0]['strLabel']
            self.__rec_label_id = parsed_json['artists'][0]['idLabel']
            self.__year_formed = parsed_json['artists'][0]['intFormedYear']
            self.__year_born = parsed_json['artists'][0]['intBornYear']
            self.__year_died = parsed_json['artists'][0]['intDiedYear']
            self.__disbanded = parsed_json['artists'][0]['strDisbanded']
            self.__style = parsed_json['artists'][0]['strStyle']
            self.__genre = parsed_json['artists'][0]['strGenre']
            self.__mood = parsed_json['artists'][0]['strMood']
            self.__website = parsed_json['artists'][0]['strWebsite']
            self.__facebook = parsed_json['artists'][0]['strFacebook']
            self.__twitter = parsed_json['artists'][0]['strTwitter']
            self.__biography_en = parsed_json['artists'][0]['strBiographyEN']
            if self.__biography_en is not None:
                self.__biography_en = (parsed_json['artists'][0]
                                       ['strBiographyEN'].encode('utf-8'))
            self.__biography_de = parsed_json['artists'][0]['strBiographyDE']
            if self.__biography_de is not None:
                self.__biography_de = (parsed_json['artists'][0]
                                       ['strBiographyDE'].encode('utf-8'))
            self.__biography_fr = parsed_json['artists'][0]['strBiographyFR']
            if self.__biography_fr is not None:
                self.__biography_fr = (parsed_json['artists'][0]
                                       ['strBiographyFR'].encode('utf-8'))
            self.__biography_cn = parsed_json['artists'][0]['strBiographyCN']
            if self.__biography_cn is not None:
                self.__biography_cn = (parsed_json['artists'][0]
                                       ['strBiographyCN'].encode('utf-8'))
            self.__biography_it = parsed_json['artists'][0]['strBiographyIT']
            if self.__biography_it is not None:
                self.__biography_it = (parsed_json['artists'][0]
                                       ['strBiographyIT'].encode('utf-8'))
            self.__biography_jp = parsed_json['artists'][0]['strBiographyJP']
            if self.__biography_jp is not None:
                self.__biography_jp = (parsed_json['artists'][0]
                                       ['strBiographyJP'].encode('utf-8'))
            self.__biography_ru = parsed_json['artists'][0]['strBiographyRU']
            if self.__biography_ru is not None:
                self.__biography_ru = (parsed_json['artists'][0]
                                       ['strBiographyRU'].encode('utf-8'))
            self.__biography_es = parsed_json['artists'][0]['strBiographyES']
            if self.__biography_es is not None:
                self.__biography_es = (parsed_json['artists'][0]
                                       ['strBiographyES'].encode('utf-8'))
            self.__biography_pt = parsed_json['artists'][0]['strBiographyPT']
            if self.__biography_pt is not None:
                self.__biography_pt = (parsed_json['artists'][0]
                                       ['strBiographyPT'].encode('utf-8'))
            self.__biography_se = parsed_json['artists'][0]['strBiographySE']
            if self.__biography_se is not None:
                self.__biography_se = (parsed_json['artists'][0]
                                       ['strBiographySE'].encode('utf-8'))
            self.__biography_nl = parsed_json['artists'][0]['strBiographyNL']
            if self.__biography_nl is not None:
                self.__biography_nl = (parsed_json['artists'][0]
                                       ['strBiographyNL'].encode('utf-8'))
            self.__biography_hu = parsed_json['artists'][0]['strBiographyHU']
            if self.__biography_hu is not None:
                self.__biography_hu = (parsed_json['artists'][0]
                                       ['strBiographyHU'].encode('utf-8'))
            self.__biography_no = parsed_json['artists'][0]['strBiographyNO']
            if self.__biography_no is not None:
                self.__biography_no = (parsed_json['artists'][0]
                                       ['strBiographyNO'].encode('utf-8'))
            self.__biography_il = parsed_json['artists'][0]['strBiographyIL']
            if self.__biography_il is not None:
                self.__biography_il = (parsed_json['artists'][0]
                                       ['strBiographyIL'].encode('utf-8'))
            self.__biography_pl = parsed_json['artists'][0]['strBiographyPL']
            if self.__biography_pl is not None:
                self.__biography_pl = (parsed_json['artists'][0]
                                       ['strBiographyPL'].encode('utf-8'))
            self.__gender = parsed_json['artists'][0]['strGender']
            self.__members = parsed_json['artists'][0]['intMembers']
            self.__country = parsed_json['artists'][0]['strCountry']
            self.__country_code = parsed_json['artists'][0]['strCountryCode']
            self.__artist_thumb = parsed_json['artists'][0]['strArtistThumb']
            self.__artist_logo = parsed_json['artists'][0]['strArtistLogo']
            self.__fanart = parsed_json['artists'][0]['strArtistFanart']
            self.__fanart2 = parsed_json['artists'][0]['strArtistFanart2']
            self.__fanart3 = parsed_json['artists'][0]['strArtistFanart3']
            self.__banner = parsed_json['artists'][0]['strArtistBanner']
            self.__music_brainz_id = (parsed_json['artists'][0]
                                      ['strMusicBrainzID'])
            self.__last_fm_chart = parsed_json['artists'][0]['strLastFMChart']
            self.__locked = parsed_json['artists'][0]['strLocked']
            return {'artist_id': self.__artist_id,
                    'artist': self.__artist_name,
                    'artist_aka': self.__artist_aka,
                    'rec_label': self.__rec_label,
                    'rec_label_id': self.__rec_label_id,
                    'year_formed': self.__year_formed,
                    'year_born': self.__year_born,
                    'year_died': self.__year_died,
                    'disbanded': self.__disbanded,
                    'style': self.__style,
                    'genre': self.__genre,
                    'mood': self.__mood,
                    'website': self.__website,
                    'facebook': self.__facebook,
                    'twitter': self.__twitter,
                    'biography_en': self.__biography_en,
                    'biography_de': self.__biography_de,
                    'biography_fr': self.__biography_fr,
                    'biography_cn': self.__biography_cn,
                    'biography_it': self.__biography_it,
                    'biography_jp': self.__biography_jp,
                    'biography_ru': self.__biography_ru,
                    'biography_es': self.__biography_es,
                    'biography_pt': self.__biography_pt,
                    'biography_se': self.__biography_se,
                    'biography_nl': self.__biography_nl,
                    'biography_hu': self.__biography_hu,
                    'biography_no': self.__biography_no,
                    'biography_il': self.__biography_il,
                    'biography_pl': self.__biography_pl,
                    'gender': self.__gender,
                    'members': self.__members,
                    'country': self.__country,
                    'country_code': self.__country_code,
                    'artist_thumb': self.__artist_thumb,
                    'artist_logo': self.__artist_logo,
                    'fanart': self.__fanart,
                    'fanart2': self.__fanart2,
                    'fanart3': self.__fanart3,
                    'banner': self.__banner,
                    'music_brainz_id': self.__music_brainz_id,
                    'last_fm_chart': self.__last_fm_chart,
                    'locked': self.__locked
                    }
        except:
            return 0

    def get_artist_info(self, artist):
        """
        Return artist information as dictionary. If no result try either
        removing or prefixing the 'the' word.
        """
        self.clear()
        ai = self._artist_info(artist)
        if ai != 0:
            return ai
        else:
            if 'the ' in artist:
                ai = self._artist_info(artist.replace('the ', ''))
            else:
                ai = self._artist_info('the ' + artist)
            if ai == 0:
                if 'junior' in artist:
                  ai = self._artist_info(artist.replace('junior', 'jr.'))
                if ai == 0:
                  if '-' in artist:
                    ai = self._artist_info(artist.replace('-', ' '))
        return ai
