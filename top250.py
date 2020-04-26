# --*-- coding: utf-8 --*--

import requests
from lxml import etree
import csv
import re
import time
import os
from fake_useragent import UserAgent
import urllib
import random
from bs4 import BeautifulSoup
from retrying import retry
import datetime

# 实例化UserAgent对象，用于产生随机UserAgent
ua = UserAgent()
headers = {"User-Agent": ua.random}

#存储每一页中的25部电影链接
def index_pages(number, proxy):
    url = 'https://movie.douban.com/top250?start=%s&filter=' % number
    index_response = requests.get(url=url, headers=headers, timeout=3, proxies=proxy).content.decode()
    tree = etree.HTML(index_response)
    m_urls = tree.xpath("//li/div/div/a/@href")
    return m_urls

@retry(stop_max_attempt_number=3)  # 让被装饰的函数反复执行三次，三次全部报错才会报错，中间有一次正常都会继续往后执行程序
def parse_pages(url, proxy):
    movie_pages = requests.get(url=url, headers=headers, timeout=3, proxies=proxy)
    parse_movie = etree.HTML(movie_pages.text)

    # 排名
    ranking = parse_movie.xpath("//span[@class='top250-no']/text()")

    # 电影名
    name = parse_movie.xpath("//h1/span[1]/text()")

    # 评分
    score = parse_movie.xpath("//div[@class='rating_self clearfix']/strong/text()")

    # 参评人数
    value = parse_movie.xpath("//span[@property='v:votes']/text()")
    number = [" ".join(['参评人数：'] + value)]
    # value = parse_movie.xpath("//a[@class='rating_people']")
    # string = [value[0].xpath('string(.)')]
    # number = [a.strip() for a in string]
    # print(number)

    # 类型
    value = parse_movie.xpath("//span[@property='v:genre']/text()")
    types = [" ".join(['类型：'] + value)]

    # 制片国家/地区
    value = re.findall('<span class="pl">制片国家/地区:</span>(.*?)<br/>', movie_pages.text)
    country = [" ".join(['制片国家:'] + value)]

    # 语言
    value = re.findall('<span class="pl">语言:</span>(.*?)<br/>', movie_pages.text)
    language = [" ".join(['语言:'] + value)]

    # 上映时期
    value = parse_movie.xpath("//span[@property='v:initialReleaseDate']/text()")
    date = [" ".join(['上映日期：'] + value)]

    # 片长
    value = parse_movie.xpath("//span[@property='v:runtime']/text()")
    time = [" ".join(['片长：'] + value)]

    # 又名
    value = re.findall('<span class="pl">又名:</span>(.*?)<br/>', movie_pages.text)
    other_name = [" ".join(['又名:'] + value)]

    # 导演
    value = parse_movie.xpath("//div[@id='info']/span[1]/span[@class='attrs']/a/text()")
    director = [" ".join(['导演:'] + value)]

    # 编剧
    value = parse_movie.xpath("//div[@id='info']/span[2]/span[@class='attrs']/a/text()")
    screenwriter = [" ".join(['编剧:'] + value)]

    # 主演
    value = parse_movie.xpath("//div[@id='info']/span[3]")
    performer = [value[0].xpath('string(.)')]

    # URL
    m_url = ['豆瓣链接：' + movie_url]

    # IMDb链接
    value = parse_movie.xpath("//div[@id='info']/a/@href")
    imdb_url = [" ".join(['IMDb链接：'] + value)]

    # 保存电影海报
    poster = parse_movie.xpath("//div[@id='mainpic']/a/img/@src")
    response = requests.get(poster[0])
    name2 = re.sub(r'[A-Za-z\:\s]', '', name[0])
    poster_name = str(ranking[0]) + ' - ' + name2 + '.jpg'
    dir_name = 'douban_poster'
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
    poster_path = dir_name + '/' + poster_name
    with open(poster_path, "wb")as f:
        f.write(response.content)

    return zip(ranking, name, score, number, types, country, language, date, time, other_name, director, screenwriter, performer, m_url, imdb_url)


# def save_results(data):
#     #now_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')  # 取现在的时间
#     now_str = datetime.datetime.now().strftime('%Y%m%d')  # 取现在的时间
#     file_name = f'doubantop250.csv_{now_str}.csv'
#     with open(file_name, 'a', newline = '', encoding="utf-8-sig") as fp:
#         writer = csv.writer(fp)
#         writer.writerow(data)

IPRegular = r"(([1-9]?\d|1\d{2}|2[0-4]\d|25[0-5]).){3}([1-9]?\d|1\d{2}|2[0-4]\d|25[0-5])"     #这是IP地址的正则表达式
def parseIPList(url="http://www.xicidaili.com/"):
    """
    爬取最新代理ip，来源：西刺代理
    注意：西刺代理容易被封，如遇到IP被封情况，采用以下两种方法即可解决：
    方法一： 喜欢研究的同学，可参考对接此接口
    方法二：直接屏蔽掉此接口，不使用代理也能正常使用
    :param url: "http://www.xicidaili.com/"
    :return: 代理IP列表ips
    """
    ips = []
    request = urllib.request.Request(url, headers=headers)
    response = urllib.request.urlopen(request)
    soup = BeautifulSoup(response, "lxml")
    tds = soup.find_all("td")
    for td in tds:
        string = str(td.string)
        if re.search(IPRegular, string):
            ips.append(string)
    #print(ips)
    return ips


if __name__ == '__main__':
    #创建用于存储数据的csv文件，清空原有数据，并写入标题
    now_str = datetime.datetime.now().strftime('%Y%m%d')  # 取现在的时间
    file_name = f'doubantop250_{now_str}.csv'
    with open(file_name, 'w', newline='', encoding="utf-8-sig") as fp:
        head = ['排名', '电影名', '评分', '参评人数', '类型', '国家', '语言', '上映日期', '时长',\
                '别名', '导演', '编剧', '主演', '豆瓣链接', 'IMDb链接']
        writer = csv.writer(fp)
        # 写入一行数据
        writer.writerow(head)

    num = 0
    for i in range(0, 250, 25):

        # 调用parseIPList随机产生代理IP，防反爬
        ips = parseIPList()
        proxy = {"http": "{}:8080".format(ips[random.randint(0, 40)])}
        print('IP地址为：'+str(proxy))

        movie_urls = index_pages(i, proxy)
        print(movie_urls)
        print('本页电影数量：'+str(len(movie_urls)))
        for movie_url in movie_urls:
            results = parse_pages(movie_url, proxy)
            for result in results:   #这个循环其实只执行1次，只是提取results中的内容进行存储
                # save_results(result)
                with open(file_name, 'a', newline='', encoding="utf-8-sig") as fp:
                    writer = csv.writer(fp)
                    writer.writerow(result)
            print(result)

            num += 1
            print('第' + str(num) + '条电影信息保存完毕！')
            time.sleep(2)   # 延时2秒，防反爬
        time.sleep(2)      # 延时2秒，防反爬