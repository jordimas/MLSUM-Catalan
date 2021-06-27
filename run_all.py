from bs4 import BeautifulSoup
import newspaper
import re
import time
from random import randint
from time import sleep

def clean_split_summary(summary):
    true_summary = summary
    if 4 * " " in summary:
        max_length = 0
        for candidate_summary in summary.split(4 * " "):
            if len(candidate_summary.split()) > max_length:
                true_summary = candidate_summary
                max_length = len(candidate_summary.split())
    return true_summary


def get_topic_from_url(url, lang):
    if lang == 'de':
        if 'www.sueddeutsche.de' in url:
            topic = url.split('/')[3]

    if lang == 'es':
        if 'elpais.com' in url:
            topic = url.split('/')[3] + ' ' + url.split('/')[7]

    if lang == 'tu':
        if 'www.internethaber.com' in url:
            if len(url.split('/')) > 4:
                topic = url.split('/')[3] + ' ' + url.split('/')[7]
            else:
                topic = 'unknown'
    if lang == 'ru':
        if 'www.mk.ru' in url:
            topic = url.split('/')[3]

    if lang == 'fr':
        if 'www.lemonde.fr' in url or 'abonnes.lemonde.fr' in url:
            topic = url.split('/')[3]
        elif 'blog.lemonde.fr' in url:
            topic = 'blog'
        elif 'www.courrierinternational.com' in url:
            topic = 'courrierinternational'
        else:
            topic = 'unknown'

    if lang == 'ca':
        return 'news'

    return topic


def get_newspaper_content(url, lang, date_archive='20200303'):
    web_archive_url = f'https://web.archive.org/web/{date_archive}/'

#    article = newspaper.Article(web_archive_url + url)
    article = newspaper.Article(url)
    article.download()
    article.parse()

    id_hash = article.link_hash
    title = article.title
    text = article.text
    summary = article.meta_description

    #print (f"text: '{text}'")

    if lang in ['ca']:

        if len(summary) == 0:
            soup = BeautifulSoup(article.html, 'html.parser')
            description = soup.find("meta",  {"property":"og:description"})
            summary = description["content"]

        remove_text = "Aquest diari existeix perquè més de vint mil lectors han decidit que poden i volen pagar cinc euros el mes perquè tots rebeu tota la informació amb accés obert. Però no n'hi ha prou. En necessitem més. Tu ho vols i pots? Fes-te'n subscriptor ací."
        text = text.replace(remove_text, '').strip()

    if lang in ['fr']:
        if 'Lire :' in text[:10]:
            text = text.split('Lire :')[0]

        # Remove the duplicated summary
        if summary in text:
            text = text[len(summary):]

    if lang in ['ru']:
        soup = BeautifulSoup(article.html, 'html.parser')
        summary = soup.find(class_="second_title").text

        if soup.find(class_="inread-content"):
            text = soup.find(class_="inread-content").text
        else:
            text = text[len(title):].strip()[len(summary):]

    if lang in ['tu']:
        text = text.replace(summary, "")

    return article, text, summary, title


def get_clean_content(url, lang):
    article, text, summary, title = get_newspaper_content(url, lang)
    topic = get_topic_from_url(url, lang)

    base_processing = lambda x: re.sub('\s+', ' ', re.sub('\n+', ' ', clean_split_summary(x.strip())))
    summary, title, text = base_processing(summary), base_processing(title), base_processing(text)

    return text, summary, title, topic


def main():
    path_urls = 'data/urls/%s.%s.txt.urls'
    path_output = 'data/processed/%s_%s.txt'
    path_output_bug = 'data/processed/%s_%s.errors.txt'

    sep = '\t'
    for lang in ['ca']:
        for mode in ['train']:
            too_small = 0
            with open(path_urls % (mode, lang), 'r') as f_urls, \
                    open(path_output % (lang, mode), 'w') as f_w, \
                    open(path_output_bug % (lang, mode), 'w') as f_w_bug:

                lines = f_urls.readlines()
                start = time.time()
                url_in_error = 0
                for i, line in enumerate(lines):
                    url = line.strip()
                    url_date = "24/06/2021"
                    #print(url)
                    #line = line.strip().split('\t')
                    #url, url_date = line[0], line[1]
                    

                    try:
                        text, summary, title, topic = get_clean_content(url, lang)

                        words = len(text.split(' '))
                        if words > 300:
                            f_w.write(
                                url + sep + url_date + sep + text + sep + summary + sep + title + sep + topic + sep + '\n')
                        else: 
                            too_small =  too_small + 1
                    except Exception as e:
                        print(e)
                        f_w_bug.write(url + '\n')
                        url_in_error += 1

                    if i % 15 == 0:
                        hours, rem = divmod(time.time() - start, 3600)
                        minutes, seconds = divmod(rem, 60)
                        duration = "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds)
                        print(lang, mode, ' | total #', len(lines), ' | processed:', i, ' | error:', url_in_error, ' | ', duration, ' | too_small: ', too_small, ' | written: ', i - too_small)
                    sleep(randint(1,100)/50)

                    #if i == 300:
                    #    break

if __name__ == '__main__':
    main()

