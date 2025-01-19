# https://www.sxlib.org.cn/was5/web/search

from getbrowser import setup_chrome
browser = setup_chrome()



url='https://www.sxlib.org.cn/dfzy/qyqq/'

urls=['https://www.sxlib.org.cn/dfzy/qyqq/jmqqjm/jb/ctj/',
    'https://www.sxlib.org.cn/dfzy/qyqq/jmqqjm/jb/xdj/'
    ]
for url in urls:
  tab=browser.new_tab()
  tab.get(url)
  c=tab.ele('.list_right_mid').text
  print('==',c)
  uls=tab.ele('.list_right_ul_list').children()
  for e in uls:
    link=e.ele("t:a").link
    print('urls',link)
    
  
