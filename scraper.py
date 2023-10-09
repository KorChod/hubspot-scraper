import re
import requests
import multiprocessing
from collections import namedtuple
from bs4 import BeautifulSoup
from rake_nltk import Rake


r = Rake()

SOURCE_URL = 'https://blog.hubspot.com/'
SOUP_PARSER = 'html.parser'
DATE_PATTERN = r'\d{1,2}/\d{1,2}/\d{2}'
LIMIT_BLOG_POSTS = 3
LIMIT_KEY_PHRASES = 5
MAX_NUMBER_WORDS_IN_PHRASE = 3

# Selector = namedtuple('Selector', 'primary')
BlogPost = namedtuple('BlogPost', 'url date')


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


def process_text(blog_post):
    blog_post_soup = get_soup(blog_post.url)
    blog_post_text = blog_post_soup.find(class_='hsg-rich-text').get_text()
    word_count = len(re.findall(r'\b\w+\b', blog_post_text))
    letter_count = len(re.findall(r'[a-zA-Z]', blog_post_text))
    r.extract_keywords_from_text(blog_post_text)
    ranked_phrases = [phrase for phrase in r.get_ranked_phrases_with_scores() if len(phrase[1].split()) <= MAX_NUMBER_WORDS_IN_PHRASE]
    top_ranked_phrases = ranked_phrases[:LIMIT_KEY_PHRASES]

    return blog_post.url, word_count, letter_count, top_ranked_phrases


def print_results(results):
    for result in results:
        blog_post_url, word_count, letter_count, ranked_phrases = result
        print(f"Blogpost: {blog_post_url}")
        print(f"Word count: {word_count}")
        print(f"Letter count: {letter_count}")
        print(f"Key phrases: {ranked_phrases}", end='\n\n')


soup = get_soup(SOURCE_URL)


# selectors = [Selector('blog-post-card'), Selector('blog-categories-card')]
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

num_processes = len(top_sorted_blog_posts)
pool = multiprocessing.Pool(processes=num_processes)

results = pool.map(process_text, top_sorted_blog_posts)
pool.close()
pool.join()

print_results(results)


