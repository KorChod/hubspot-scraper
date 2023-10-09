#!/usr/bin/env python
import re
import requests
import multiprocessing
from collections import namedtuple
from bs4 import BeautifulSoup
from rake_nltk import Rake


SOURCE_URL = 'https://blog.hubspot.com/'
SOUP_PARSER = 'html.parser'
DATE_PATTERN = r'\d{1,2}/\d{1,2}/\d{2}'
LIMIT_BLOG_POSTS = 3
LIMIT_KEY_PHRASES = 5
MAX_NUMBER_WORDS_IN_PHRASE = 3

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


def get_blogposts(soup, selector):
    blogpost_list = []
    blogposts = soup.find_all('div', class_=selector)
    for blogpost in blogposts:
        secondary_selector = selector + '-title'
        blogpost_url = blogpost.find(class_=secondary_selector).a.get('href')

        blogpost_date = None
        if selector == 'blog-post-card':
            blogpost_date = blogpost \
                .find(class_='blog-post-card-date') \
                .get('datetime')
        elif selector == 'blog-categories-card':
            blogpost_date = blogpost \
                .find(class_='blog-categories-card-footer') \
                .find(string=re.compile(DATE_PATTERN)) \
                .strip()

        if blogpost_url and blogpost_date:
            blogpost_list.append(BlogPost(blogpost_url, blogpost_date))

    return blogpost_list


def extract_data(blog_post):
    blog_post_soup = get_soup(blog_post.url)
    blog_post_text = blog_post_soup.find(class_='hsg-rich-text').get_text()

    word_count = len(re.findall(r'\b\w+\b', blog_post_text))
    letter_count = len(re.findall(r'[a-zA-Z]', blog_post_text))

    r = Rake()
    r.extract_keywords_from_text(blog_post_text)

    words_condition = lambda x: len(x) <= MAX_NUMBER_WORDS_IN_PHRASE

    ranked_phrases = r.get_ranked_phrases_with_scores()
    ranked_phrases = [phrase for phrase in ranked_phrases if words_condition(phrase[1].split())]
    top_ranked_phrases = ranked_phrases[:LIMIT_KEY_PHRASES]

    return blog_post.url, word_count, letter_count, top_ranked_phrases


def process_data(blog_posts):
    num_processes = len(blog_posts)
    pool = multiprocessing.Pool(processes=num_processes)

    results = pool.map(extract_data, blog_posts)
    pool.close()
    pool.join()
    return results


def print_results(results):
    for result in results:
        blog_post_url, word_count, letter_count, ranked_phrases = result
        print(f"Blogpost: {blog_post_url}")
        print(f"Word count: {word_count}")
        print(f"Letter count: {letter_count}")
        print(f"Key phrases: {ranked_phrases}", end='\n\n')


def main():
    soup = get_soup(SOURCE_URL)

    blogposts = []
    blogposts += get_blogposts(soup, 'blog-post-card')
    blogposts += get_blogposts(soup, 'blog-categories-card')

    sorted_blogposts = sorted(blogposts, key=lambda x: (date_sort_key(x.date)), reverse=True)
    top_sorted_blogposts = sorted_blogposts[:LIMIT_BLOG_POSTS]

    results = process_data(top_sorted_blogposts)

    print_results(results)


if __name__ == "__main__":
    main()
