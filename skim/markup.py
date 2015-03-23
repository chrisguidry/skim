# coding: utf-8
from html import unescape
import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
import html2text
import markdown
from pyembed.core import PyEmbed

html2text.config.UNICODE_SNOB = 1
html2text.config.SINGLE_LINE_BREAK = False
HTML2TEXT_CONFIG = {'bodywidth': 0}

PYEMBED = PyEmbed()

def to_text(base, entry_url, html):
    soup = BeautifulSoup(html)

    if entry_url:
        parsed = urlparse(entry_url)
        if 'youtube.com' in parsed.netloc:
            return youtube_entry(base, entry_url, soup)

    vice_com_internal_markup(base, soup)

    absolutize(base, soup)
    invert_linked_elements(base, soup)
    tighten_inlines(base, soup)
    remove_trailer_parks(base, soup)

    text = html2text.html2text(str(soup), baseurl=base, **HTML2TEXT_CONFIG)
    text = unescape(text)

    text = vice_com_video_markup(base, text)

    return text.strip()


def youtube_entry(base, entry_url, soup):
    try:
        video, description, *_ = soup.find_all('td')
        video_href = video.find('a')['href']
        description = description.find('span').text
    except ValueError:
        video_href = entry_url
        description = str(soup)

    embed = PYEMBED.embed(video_href, max_width=1280)
    return '\n\n'.join([embed, description])


def invert_linked_elements(base, soup):
    for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em', 'i', 'b']:
        for element in soup.find_all(tag_name):
            if element.parent.name == 'a':
                anchor = element.parent
                unwrapped = element.unwrap()
                anchor.wrap(unwrapped)

def tighten_inlines(base, soup):
    for tag_name in ['em', 'strong', 'i', 'b']:
        for element in soup.find_all(tag_name):
            if element.text.endswith(' '):
                element.string = element.text.rstrip()
                element.insert_after(' ')

def absolutize(base, soup):
    for anchor in soup.find_all('a', href=True):
        anchor['href'] = urljoin(base, anchor['href'])
    for image in soup.find_all('img', src=True):
        image['src'] = urljoin(base, image['src'])

def remove_trailer_parks(base, soup):
    SHARING_IMAGES = [
        ('feeds.feedburner.com', ''),
        ('.feedsportal.com', ''),
        ('a.fsdn.com', 'twitter_icon'),
        ('a.fsdn.com', 'facebook_icon'),
        ('www.gstatic.com', 'images/icons/gplus-16.png'),
        ('', 'social-media-feather/synved-social')
    ]
    for image in soup.find_all('img', src=True):
        parsed = urlparse(image['src'])
        for domain, path in SHARING_IMAGES:
            if parsed.netloc.endswith(domain) and path in parsed.path:
                if image.parent.name == 'a':
                    image.parent.decompose()
                else:
                    image.decompose()
                break

    SHARING_LINKS = [
        ('.feedsportal.com', '.htm', ''),
        ('facebook.com', 'sharer.php', 'url'),
        ('facebook.com', 'share.php', 'u='),
        ('twitter.com', 'home', 'status'),
        ('plus.google.com', 'share', 'url'),
        ('reddit.com', 'submit', 'url'),
        ('pinterest.com', 'pin/create', 'url'),
        ('linkedin.com', 'shareArticle', 'url'),
        ('synved.com', 'wordpress-social-media-feather', ''),
        ('sharetodiaspora.github.com', '', 'url')
    ]
    for anchor in soup.find_all('a', href=True):
        parsed = urlparse(anchor['href'])
        for domain, path, query in SHARING_LINKS:
            if parsed.netloc.endswith(domain) and path in parsed.path and query in parsed.query:
                anchor.decompose()
                break

def _parse_vice_com_markup(markup):
    return {m.group(1): m.group(2) for m in re.finditer(r"([\w]+?)='(.+?)'", markup)}

def vice_com_internal_markup(base, soup):
    if not base or 'www.vice.com/rss' not in base:
        return

    for imagep in soup.find_all('p', class_='has-image'):
        info = _parse_vice_com_markup(imagep.text.strip())
        try:
            url = 'https://assets2.vice.com/%s%s' % (info['path'], info['filename'])
        except KeyError:
            continue
        imagep.replace_with(soup.new_tag('img', src=url))

def vice_com_video_markup(base, text):
    if not base or 'www.vice.com/rss' not in base:
        return text

    lines = []
    for line in text.split('\n'):
        for match in re.finditer(r"\[youtube src.+?\]", line):
            info = _parse_vice_com_markup(match.group())
            try:
                url = 'http://www.youtube.com/watch?v=' + info['src'].split('/')[-1]
            except KeyError:
                continue

            line = line.replace(match.group(), PYEMBED.embed(url, max_width=1280))
        lines.append(line)
    return '\n'.join(lines)



class TargetBlankAnchors(markdown.treeprocessors.Treeprocessor):
    def run(self, root):
        for child in root:
            if child.tag == 'a':
                child.set('target', '_blank')
            self.run(child)

class ImageAltsToTitles(markdown.treeprocessors.Treeprocessor):
    def run(self, root):
        for child in root:
            if child.tag == 'img':
                if child.get('alt') and not child.get('title'):
                    child.set('title', child.get('alt'))
            self.run(child)

class SkimExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md, md_globals):
        md.treeprocessors.add('targetblankanchors', TargetBlankAnchors(md), '_end')
        md.treeprocessors.add('imagealtstotitles', ImageAltsToTitles(md), '_end')

MARKDOWN = markdown.Markdown(output_format='html5',
                             smart_emphasis=True,
                             safe_mode=False,
                             extensions=['markdown.extensions.abbr',
                                         'markdown.extensions.codehilite',
                                         'markdown.extensions.meta',
                                         'markdown.extensions.smart_strong',
                                         'markdown.extensions.smarty',
                                         'markdown.extensions.tables',
                                         SkimExtension()])

def to_html(text, unwrap=False):
    html = MARKDOWN.convert(text)
    if unwrap:
        html = html[3:-4]  # nixes the containing <p> and </p>
    return html
