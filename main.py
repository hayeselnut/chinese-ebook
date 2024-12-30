import argparse
import opencc
import os
import pypub
import requests
import time
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from natsort import natsorted

converter = opencc.OpenCC("s2t.json")

root_url = "https://www.zhaoshuyuan.net"

# Create a session with retry support
session = requests.Session()
retries = Retry(
    total=5,  # Total number of retries
    backoff_factor=1,  # Exponential backoff factor (1s, 2s, 4s, etc.)
    status_forcelist=[500, 502, 503, 504],  # Retry on these HTTP status codes
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)


def scrape_and_write_chapter_to_file(url):
    time.sleep(5)

    response = session.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        chapter_title = converter.convert(
            soup.find('div', class_="booktitle").text.strip())
        chapter_content_paragraphs = soup.find(
            id="chaptercontent").find_all('p')
        next_url = soup.find('a', id="next_url")['href']

        filename = 'chapters/' + chapter_title + '.txt'

        with open(filename, 'w', encoding='utf-8') as file:
            for p in chapter_content_paragraphs:
                text = converter.convert(p.text.strip())
                file.write(text + '\n')

        print("Content has been written to " + filename)

        if next_url != 'javascript:void(0);':
            print("Next: " + root_url + next_url)
            scrape_and_write_chapter_to_file(root_url + next_url)
        else:
            print("No more next urls")
    else:
        print(
            f"Failed to retrieve the webpage. Status code: {response.status_code}")


def write_epub_file(dir, epub_filename):
    epub = pypub.Epub('穿成冷宫废后靠系统养娃逆袭')

    for filename in natsorted(os.listdir(dir)):
        print(filename)
        filepath = os.path.join(dir, filename)
        chapter = pypub.create_chapter_from_file(filepath)
        chapter.title = filename.removesuffix('.txt')
        epub.add_chapter(chapter)

    epub.create(epub_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-first-chapter-url",
        type=str,
        required=True,
        help="URL of the first chapter, e.g. https://www.zhaoshuyuan.net/read/njinij/tbtqg.html")
    args = parser.parse_args()
    first_chapter_url = args.first_chapter_url

    scrape_and_write_chapter_to_file(first_chapter_url)
    epub_filename = "output.epub"
    try:
        os.remove(epub_filename)
    except FileNotFoundError:
        pass

    write_epub_file("chapters/", epub_filename)
