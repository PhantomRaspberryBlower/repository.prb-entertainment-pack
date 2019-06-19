#!/bin/python

from threading import Thread
import os
from mutagen.easyid3 import EasyID3
import mutagen
import commontasks

# Written by: Phantom Raspberry Blower
# Date: 21-08-2017
# Description: Add ID3 Tags to songs

class Setid3Tags(Thread):
    def __init__(self, file):
        self.file = file
        Thread.__init__(self)


    def run(self):
        if os.path.isfile(self.file):
            s = commontasks.read_from_file(self.file)
            search_list = s.split('\n')
            for list in search_list:
                if list != '':
                    splitlist = list.split('<>')
                    # Remove invalid characters from file name
                    file_name = commontasks.validate_filename(str(splitlist[4]))
                    filename = os.path.join(splitlist[0], file_name).strip()
                    artist = splitlist[1]
                    album = splitlist[2]
                    track = splitlist[3].strip()
                    trackname = splitlist[4]
                    year = splitlist[5]
                    genre =  splitlist[6].strip()
                    tracktitle = trackname
                    if os.path.isfile(filename):
                        try:
                          tag = EasyID3(filename)
                        except:
                          tag = mutagen.File(filename, easy=True)
                          tag.add_tags()
                        tag["title"] = tracktitle.replace(track + '. ','').replace('.mp3', '')
                        tag["artist"] = artist
                        tag["album"] = album
                        tag["date"] = year
                        tag["genre"] = genre
                        tag["tracknumber"] = track
                        tag.save(v2_version=3)
                        commontasks.remove_from_list(list, self.file)
