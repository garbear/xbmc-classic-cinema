# Copyright 2011 Jonathan Beluch. 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from common import download_page, parse_qs, parse_url_qs, unhex
import urllib
from BeautifulSoup import BeautifulSoup as BS, SoupStrainer as SS
import urlparse
import re
try:
    import json
except ImportError:
    import simplejson as json

'''
This module is meant to abstract the parsing of flash video URLs out of plugins.

Each class represents a video site and should implement a @staticmethod named
get_flashvide_url. The method should take 1 argument, a string, usually corresponding
to HTML source code. The method should return a url for a video resource or None if
the page wasn't able to be parsed.
'''

def get_flashvideo_url(src=None, url=None):
    if not url and not src:
        print 'At least src or url required.'

    if url:
        src = download_page(url)

    #there are 2 kinds of videos on the site, google video and archive.org
    if src.find('googleplayer') > 0:
        flash_url = GoogleVideo.get_flashvideo_url(src)
    elif src.find('flowplayer') > 0:
        flash_url = ArchiveVideo.get_flashvideo_url(src)
    else:
        print 'no handler implementd for this url.'

    return flash_url

class GoogleVideo(object):
    @staticmethod
    def get_flashvideo_url(src):
        embed_tags = BS(src, parseOnlyThese=SS('embed'))
        url = embed_tags.find('embed')['src']
        docid = parse_url_qs(url).get('docid')
        url = 'http://video.google.com/videoplay?docid=%s&hl=en' % docid

        #load the googlevideo page for a given docid or googlevideo swf url
        src = download_page(url)
        flvurl_pattern = re.compile(r"preview_url:'(.+?)'")
        m = flvurl_pattern.search(src)
        if not m:
            return
        previewurl = m.group(1)

        #replace hex things
        # videoUrl\x3dhttp -> videoUrl=http
        previewurl = unhex(previewurl)
        #parse querystring and return the videoUrl
        params = parse_url_qs(previewurl)
        return urllib.unquote_plus(params['videoUrl'])

class ArchiveVideo(object):
    @staticmethod
    def get_flashvideo_url(src):
        if src.find('http://www.archive.org/flow/flowplayer.commercial-3.2.1.swf') > -1:
            print src.find('http://www.archive.org/flow/flowplayer.commercial-3.2.1.swf')
            return ArchiveVideo.swf_3_21(src)
        elif src.find('http://www.archive.org/flow/flowplayer.commercial-3.0.5.swf') > -1:
            return ArchiveVideo.swf_3_05(src)
        else:
            print 'Unknown swf version for ArchiveVideo.'
        return None

    @staticmethod
    def swf_3_05(src):
        embed_tags = BS(src, parseOnlyThese=SS('embed'))
        flashvars = embed_tags.find('embed')['flashvars']
        obj = json.loads(flashvars.split('=', 1)[1].replace("'", '"'))
        path = obj['playlist'][1]['url'] 
        return path

    @staticmethod
    def swf_3_21(src):
        embed_tags = BS(src, parseOnlyThese=SS('embed'))
        flashvars = embed_tags.find('embed')['flashvars']
        obj = json.loads(flashvars.split('=', 1)[1].replace("'", '"'))
        base_url = obj['clip']['baseUrl']
        path = obj['playlist'][1]['url'] 
        return urlparse.urljoin(base_url, path)

