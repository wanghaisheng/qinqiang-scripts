# https://www.sxlib.org.cn/was5/web/search
print('is starting=========')
from getbrowser import setup_chrome
import pandas as pd
import json
import time
import argparse
import os
import logging

# Configure logging
logging.basicConfig(
    filename='juben_scrape.log',  # Log file name
    level=logging.INFO,  # Log level (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

browser = setup_chrome()

def getlinks():
    urls = ['https://www.sxlib.org.cn/dfzy/qyqq/jmqqjm/jb/ctj/',
            'https://www.sxlib.org.cn/dfzy/qyqq/jmqqjm/jb/xdj/']
    all_links = []
    for url in urls:
        logging.info(f"Processing URL: {url}")  # Log URL
        tab = browser.new_tab()
        tab.get(url)
        time.sleep(2)

        try:
            c = tab.ele('.list_right_mid').text
            logging.info(f"  Raw text from .list_right_mid: {c}")  # Log raw text
            c = c.split('记录')[-1].split('条')[0]
            pagecount = int(int(c) / 20) + 1
            logging.info(f"  Calculated page count: {pagecount}")  # Log page count
        except Exception as e:
            logging.error(f"  Error getting page count: {e}")
            continue

        links = []
        for p in range(1, pagecount + 1):
            logging.info(f"  Processing page: {p} of {pagecount}")
            if p != 1:
                try:
                    tab.ele('.fya').children()[-3].click()
                    logging.info("    Clicked next page button")
                    time.sleep(2)
                except Exception as e:
                    logging.error(f"    Error clicking next page: {e}")
                    break

            try:
                lis = tab.eles('.list_right_ul_list li')
                logging.info(f"    Found {len(lis)} list items on this page")
                for i, li in enumerate(lis):
                    link = li.ele("t:b").ele("t:a").link
                    logging.info(f"      Link {i+1}: {link}")
                    links.append(link)
            except Exception as e:
                logging.error(f"    Error processing links on page {p}: {e}")

        all_links.extend(links)
        tab.close()

    return all_links

def getdetail(link):
    logging.info(f"Getting details for link: {link}")
    tab = browser.new_tab()
    tab.get(link)
    time.sleep(2)

    try:
        img = tab.ele('.article_main').ele("t:img").link
        logging.info(f"  Found image: {img}")
    except Exception as e:
        logging.warning(f"  Image not found: {e}")
        img = ''
    try:
        content = tab.ele('.article_main').text
        logging.info(f"  Content length: {len(content)} characters")
    except Exception as e:
        logging.error(f"  Error getting content: {e}")
        content = ''
    try:
        name = tab.ele('#article_title').text.replace("《", '').replace("》", '')
        logging.info(f"  Found name: {name}")
    except Exception as e:
        logging.error(f"  Error getting name: {e}")
        name = ''

    result = {
        "link": link,
        "img": img,
        "name": name,
        "content": content
    }
    tab.close()
    return result

def save_data(data, output_format, filename):
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        logging.info(f"Created results directory: {results_dir}")

    filepath = os.path.join(results_dir, filename)

    if output_format == 'csv':
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        logging.info(f"Data saved to {filepath} (CSV format)")
    elif output_format == 'json':
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data saved to {filepath} (JSON format)")
    else:
        logging.error(f"Invalid output format: {output_format}")

# Main execution
if __name__ == "__main__":
    # Get configuration from environment variables
    output_format = os.getenv('OUTPUT_FORMAT', 'json').lower()
    output_filename = os.getenv('OUTPUT_FILENAME', 'data')

    parser = argparse.ArgumentParser(description="Scrape data from sxlib.org.cn")
    parser.add_argument("-f", "--format", choices=['csv', 'json'],
                        help="Override OUTPUT_FORMAT environment variable")
    parser.add_argument("-o", "--output",
                        help="Override OUTPUT_FILENAME environment variable")
    args = parser.parse_args()

    if args.format:
        output_format = args.format
    if args.output:
        output_filename = args.output

    logging.info("Starting script")
    all_links = getlinks()
    logging.info(f"Found {len(all_links)} links in total.")

    results = []
    for i, link in enumerate(all_links):
        logging.info(f"Processing link {i+1} of {len(all_links)}")
        try:
            detail = getdetail(link)
            results.append(detail)
        except Exception as e:
            logging.error(f"Error processing link {link}: {e}")

    save_data(results, output_format, output_filename + '.' + output_format)
    logging.info("Script finished")

    browser.quit()
