# coding: utf-8
from html import unescape
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import html2text
import markdown


html2text.config.UNICODE_SNOB = 1
html2text.config.SINGLE_LINE_BREAK = False
HTML2TEXT_CONFIG = {'bodywidth': 0}


def to_text(base, html):
    soup = BeautifulSoup(html)

    absolutize(base, soup)
    invert_linked_elements(base, soup)
    remove_trailer_parks(base, soup)

    text = html2text.html2text(str(soup), baseurl=base, **HTML2TEXT_CONFIG)
    text = unescape(text)
    return text.strip()

def invert_linked_elements(base, soup):
    for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em', 'i', 'b']:
        for element in soup.find_all(tag_name):
            if element.parent.name == 'a':
                anchor = element.parent
                unwrapped = element.unwrap()
                anchor.wrap(unwrapped)

def absolutize(base, soup):
    for anchor in soup.find_all('a'):
        anchor['href'] = urljoin(base, anchor['href'])
    for image in soup.find_all('img'):
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
    for image in soup.find_all('img'):
        parsed = urlparse(image['src'])
        for domain, path in SHARING_IMAGES:
            if parsed.netloc.endswith(domain) and path in parsed.path:
                if image.parent.name == 'a':
                    image.parent.decompose()
                else:
                    image.decompose()

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
    for anchor in soup.find_all('a'):
        parsed = urlparse(anchor['href'])
        for domain, path, query in SHARING_LINKS:
            if parsed.netloc.endswith(domain) and path in parsed.path and query in parsed.query:
                anchor.decompose()
                break


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
        md.treeprocessors.add('targetblankanchors', ImageAltsToTitles(md), '_end')

MARKDOWN = markdown.Markdown(output_mode='html5',
                             smart_emphasis=True,
                             safe_mode='escape',
                             extensions=['markdown.extensions.abbr',
                                         'markdown.extensions.codehilite',
                                         'markdown.extensions.meta',
                                         'markdown.extensions.smart_strong',
                                         'markdown.extensions.smarty',
                                         'markdown.extensions.tables',
                                         SkimExtension()])

def to_html(text):
    return MARKDOWN.convert(text)
