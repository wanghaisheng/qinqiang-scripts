from getbrowser import setup_chrome
import pandas as pd
import json
import time
import argparse
import os
from threading import Thread
import queue

browser = setup_chrome()

def getlinks():
    urls = ['https://www.sxlib.org.cn/dfzy/qyqq/jmqqjm/jb/ctj/'
            # ,'https://www.sxlib.org.cn/dfzy/qyqq/jmqqjm/jb/xdj/'
           ]
    all_links = []
    for url in urls:
        tab = browser.new_tab()
        tab.get(url)
        time.sleep(2)  # Allow time for page to load

        # Get the total number of records and calculate the number of pages
        try:
            c = tab.ele('.list_right_mid').text
            print('==', c)
            c = c.split('记录')[-1].split('条')[0]
            pagecount = int(int(c) / 20) + 1
        except:
            continue

        links = []
        # pagecount=25
        for p in range(1, pagecount + 1):
            time.sleep(3)
            
            if p != 1:
                try:
                    # Find the second to last 'a' element within '.fya' and click it
                    tab.ele('.fya').children()[-3].click()
                    time.sleep(2)  # Allow time for page to load
                except Exception as e:
                    print(f"Error clicking next page: {e}")
                    break

            try:
                uls = tab.ele('.list_right').ele('.list_right_ul_list').children()
                # print('00000',t.text)
                # ulrs=t.children()
                # print('111',urls.text)
                # return 
                for index,e in enumerate(uls):
                    print('====page=',p,index,e,e.text)
                    if '名称' in e.text and '责任者' in e.text:
                        continue
                    link = e.ele("t:b").ele("t:a").link
                    if link:
                    # print('url', link)
                        links.append(link)
            except Exception as e:
                print(f"Error on page {p}: {e}")

        all_links.extend(links)
        tab.close()

    return all_links

def get_detail_single(link, browser_queue, results_queue):
    """Process a single detail page."""
    try:
        tab = browser_queue.get()
        tab.get(link)
        time.sleep(2)
        print('process page', link)
        try:
            img = tab.ele('.article_main').ele("t:img").link
        except:
            img = ''
        try:
            content = tab.ele('.article_main').text
        except:
            content = ''
        try:
            name = tab.ele('#article_title').text.replace("《", '').replace("》", '')
        except:
            name = ''
        result = {
            "link": link,
            "img": img,
            "name": name,
            "content": content
        }
        results_queue.put(result)
    except Exception as e:
        print(f"Error processing link {link}: {e}")
    finally:
        browser_queue.put(tab) # put the browser back
def getdetail_threaded(links, num_threads=5):
    """Get details concurrently using threads."""
    browser_queue = queue.Queue()
    for _ in range(num_threads):
        browser_queue.put(browser.new_tab()) # create browsers
    results_queue = queue.Queue()
    threads = []
    
    for link in links:
        thread = Thread(target=get_detail_single, args=(link,browser_queue, results_queue))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join() # wait for all to complete
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())
    
    while not browser_queue.empty(): # close all browser tabs
        tab = browser_queue.get()
        tab.close()
    return results
def save_data(data, output_format, filename):
    if output_format == 'csv':
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename} (CSV format)")
    elif output_format == 'json':
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Data saved to {filename} (JSON format)")
    else:
        print("Invalid output format. Supported formats are 'csv' and 'json'.")


if __name__ == "__main__":
     # Get configuration from environment variables
    output_format = os.getenv('OUTPUT_FORMAT', 'csv').lower()  # Default: csv
    output_filename = os.getenv('OUTPUT_FILENAME', 'data')  # Default: data

    # You can still override with command-line arguments if needed
    parser = argparse.ArgumentParser(description="Scrape data from sxlib.org.cn and save it as CSV or JSON.")
    parser.add_argument("-f", "--format", choices=['csv', 'json'],
                        help="Override OUTPUT_FORMAT environment variable")
    parser.add_argument("-o", "--output",
                        help="Override OUTPUT_FILENAME environment variable")
    args = parser.parse_args()

    if args.format:
        output_format = args.format
    if args.output:
        output_filename = args.output
    
    all_links = getlinks()
    print(f"Found {len(all_links)} links.")
    
    results = getdetail_threaded(all_links)

    save_data(results, output_format, output_filename + '.' + output_format)

    browser.quit()
