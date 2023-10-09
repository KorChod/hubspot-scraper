from bs4 import BeautifulSoup
import requests
from collections import namedtuple
import re
# from keybert import KeyBERT
from rake_nltk import Rake
r = Rake()


SOURCE_URL = 'https://blog.hubspot.com/'
SOUP_PARSER = 'html.parser'
DATE_PATTERN = r'\d{1,2}/\d{1,2}/\d{2}'
LIMIT_BLOG_POSTS = 3


def date_sort_key(date_str):
    month, day, year = map(int, date_str.split('/'))
    return (year, month, day)


def get_soup(page_url):
    try:
        source = requests.get(page_url)
        source.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to get the page content for '{page_url}': {e}")
    return BeautifulSoup(source.text, SOUP_PARSER)

soup = get_soup(SOURCE_URL)

Selector = namedtuple('Selector', 'primary')
BlogPost = namedtuple('BlogPost', 'url date')
selectors = [Selector('blog-post-card'), Selector('blog-categories-card')]
articles1 = soup.find_all('div', class_='blog-post-card')
articles2 = soup.find_all('div', class_='blog-categories-card')

blog_posts = []

for article in articles1:
    blog_post_url = article.find(class_='blog-post-card-title').a.get('href')
    blog_post_date = article.find(class_='blog-post-card-date').get('datetime')
    if blog_post_url and blog_post_date:
        blog_posts.append(BlogPost(blog_post_url, blog_post_date))


for article in articles2:
    blog_post_url = article.find(class_='blog-categories-card-title').a.get('href')
    blog_post_date = article.find(class_='blog-categories-card-footer').find(string=re.compile(DATE_PATTERN)).strip()
    if blog_post_url and blog_post_date:
        blog_posts.append(BlogPost(blog_post_url, blog_post_date))

top_sorted_blog_posts = sorted(blog_posts, key= lambda x: (date_sort_key(x.date)), reverse=True)[:LIMIT_BLOG_POSTS]


for blog_post in top_sorted_blog_posts:
    blog_post_soup = get_soup(blog_post.url)
    blog_post_text = blog_post_soup.find(class_='hsg-rich-text').get_text()
    word_count = len(re.findall(r'\b\w+\b', blog_post_text))
    letter_count = len(re.findall(r'[a-zA-Z]', blog_post_text))
    # kw_model = KeyBERT()
    # keywords = kw_model.extract_keywords(blog_post_text, keyphrase_ngram_range=(1, 3))
    # print(keywords)
    r.extract_keywords_from_text(blog_post_text)
    for item in [keyword for keyword in r.get_ranked_phrases_with_scores() if len(keyword[1].split()) == 3]:
        print(item)





