import argparse
from bs4 import BeautifulSoup
import re
import requests
import urllib.parse
from nltk import sent_tokenize
import nltk
from markdownify import markdownify as md
from markdown import markdown
import markdown_link_extractor
from django.db import transaction
# nltk.download('punkt')
if __name__ != "__main__":
    from wiki.models import Page, Sentence, Hyperlink


def get_links(markdown_text):
    return [urllib.parse.unquote(link.split('/wiki/')[-1]).strip() for link in
            markdown_link_extractor.getlinks(markdown_text) if '/wiki/' in link]


def markdown_to_text(markdown_string):
    # md -> html -> text since BeautifulSoup can extract text cleanly
    html = markdown(markdown_string)

    # remove code snippets
    html = re.sub(r'<pre>(.*?)</pre>', ' ', html)
    html = re.sub(r'<code>(.*?)</code >', ' ', html)

    # extract text
    soup = BeautifulSoup(html, "html.parser")
    text = ''.join(soup.findAll(text=True))

    return text


def get_wiki_information(token=''):
    page_url = 'https://fa.wikipedia.org/wiki/' + token + ''
    html_content = requests.get(page_url).text
    soup = BeautifulSoup(html_content, "html.parser")
    title = soup.find('h1', {'id': 'firstHeading'}).text
    content = soup.find('div', {'class': 'mw-parser-output'})

    introductory_html = ""
    for child in content.children:
        if child.name == "p":
            for span in child.select('span'):
                span.extract()
            for sup in child.select('sup'):
                sup.extract()
            introductory_html += child.prettify()
        elif child.name == "h2":
            break

    sentences = {markdown_to_text(sentence): get_links(sentence)
                 for sentence in sent_tokenize(md(introductory_html))}

    introductory = ' '.join(list(sentences.keys())).strip()

    return token, title, introductory, introductory_html, sentences


def get_hyperlink_information(token=''):
    page_url = 'https://fa.wikipedia.org/wiki/' + token + ''
    html_content = requests.get(page_url).text
    soup = BeautifulSoup(html_content, "html.parser")
    title = soup.find('h1', {'id': 'firstHeading'}).text
    content = soup.find('div', {'class': 'mw-parser-output'})

    first_paragraph = ""
    for child in content.children:
        if child.name == "p":
            for span in child.select('span'):
                span.extract()
            parentheses = re.compile(r'(\(\)|\[\])')
            text = parentheses.sub('', child.text.strip())
            first_paragraph += text
            if first_paragraph:
                break

    brackets = re.compile(r'(\[\d+\])')
    first_paragraph = brackets.sub('', first_paragraph)

    return token, title, first_paragraph


@transaction.atomic
def crawl_wiki_page(token='', as_evidence=False):
    page = Page.objects.filter(token=token)
    if page.exists():
        return None
    token, title, introductory, introductory_html, sentences = get_wiki_information(token)
    page = Page.objects.create(token=token, title=title, page_content=introductory, page_content_html=introductory_html,
                               as_evidence=as_evidence)
    for sentence_text, hyperlinks in sentences.items():
        sentence = Sentence.objects.create(sentence_content=sentence_text, page=page)
        for hyperlink in hyperlinks:
            hyperlink_token, hyperlink_title, hyperlink_first_paragraph = get_hyperlink_information(hyperlink)
            hyperlink = Hyperlink.objects.filter(token=hyperlink_token)
            if hyperlink.exists():
                hyperlink = hyperlink.first()
            else:
                hyperlink = Hyperlink.objects.create(token=hyperlink_token, title=hyperlink_title,
                                                     first_paragraph=hyperlink_first_paragraph)
            hyperlink.pages.add(page)
            hyperlink.sentences.add(sentence)
            hyperlink.save()
    return page


if __name__ == '__main__':
    import sys
    sys.path.insert(1, './')
    import django
    from django.conf import settings
    import annotation_service.settings as app_settings

    settings.configure(INSTALLED_APPS=app_settings.INSTALLED_APPS, DATABASES=app_settings.DATABASES)
    django.setup()
    from wiki.models import Page, Sentence, Hyperlink

    parser = argparse.ArgumentParser()
    parser.add_argument('--page_tokens', required=True, type=str,
                        help='path to a text file contains page tokens one each line')
    parser.add_argument('--error_log', required=True, type=str,
                        help='path to file tracks errors')
    parser.add_argument('--count', required=False, type=int, default=None,
                        help='number of rows to crawl from pages token file')
    args = parser.parse_args()
    import pandas as pd

    print('Loading pages\' tokens...')
    df = pd.read_excel(args.page_tokens)
    page_tokens = [[row for row in rows] for column, rows in df.iteritems()][0]
    print('Done!')

    if args.count:
        count = args.count
    else:
        count = len(page_tokens)
    print('Crawling...')
    done = 0
    error = 0
    for i in range(count):
        try:
            page = crawl_wiki_page(page_tokens[i])
            if page:
                done += 1
                print(f'Page {page_tokens[i]} saved (total done: {done}, total error: {error}).')
            else:
                print(f'Page {page_tokens[i]} already exists!')
        except Exception as e:
            with open(args.error_log, 'a+', encoding='utf-8') as error_log_file:
                error_log_file.write(f'Page {str(page_tokens[i])} failed due to {str(e.args)}')
            error += 1
            print(f'Error on {page_tokens[i]}: {e.args} (total done: {done}, total error: {error}).')
