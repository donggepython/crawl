# -*- coding: utf-8 -*-
# requests、json、lxml、urllib、bs4、fake_useragent
import random
import re
import time
import urllib
import requests
from retrying import retry

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

try:
    from lxml import etree
except Exception as e:
    import lxml.html
    # 实例化一个etree对象（解决通过from lxml import etree导包失败）
    etree = lxml.html.etree

# 实例化UserAgent对象，用于产生随机UserAgent
ua = UserAgent()


class BlogSpider(object):
    """
    Increase the number of CSDN blog visits.
    """
    def __init__(self):
        self.url = "https://blog.csdn.net/PY0312/article/list/{}"
        self.headers = {
            "Referer": "https://blog.csdn.net/PY0312/",
            "User-Agent": ua.random
        }
        self.sougouHead = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36 SE 2.X MetaSr 1.0"}
        #这是IP地址的正则表达式
        self.IPRegular = r"(([1-9]?\d|1\d{2}|2[0-4]\d|25[0-5]).){3}([1-9]?\d|1\d{2}|2[0-4]\d|25[0-5])"

    def send_request(self, num, proxy):
        """
        模拟浏览器发起请求
        :param num: num
        :return: html_str
        """
        html_str = requests.get(self.url.format(num), timeout=3, headers=self.headers, proxies=proxy).content.decode()
        #print(html_str)
        return html_str

    @retry(stop_max_attempt_number=3)  # 让被装饰的函数反复执行三次，三次全部报错才会报错，中间有一次正常都会继续往后执行程序
    def parse_data(self, html_str):
        """
        用于解析发起请求返回的数据
        :param html_str:
        :return: each_page_urls
        """
        try:
            # 将返回的 html字符串 转换为 element对象，用于xpath操作
            element_obj = etree.HTML(html_str)
            # print(element_obj)

            # 获取每一页所有blog的url
            each_page_urls = element_obj.xpath(
                '//*[@id="mainBox"]/main/div[2]/div/h4/a/@href')
            print(each_page_urls)
            print('本页文章数：' + str(len(each_page_urls)))

            return each_page_urls
        except:
            return "产生异常"

    def parseIPList(self, url="http://www.xicidaili.com/"):
        """
        爬取最新代理ip，来源：西刺代理
        注意：西刺代理容易被封，如遇到IP被封情况，采用以下两种方法即可解决：
        方法一： 喜欢研究的同学，可参考对接此接口
        方法二：直接屏蔽掉此接口，不使用代理也能正常使用
        :param url: "http://www.xicidaili.com/"
        :return: 代理IP列表ips
        """
        ips = []
        request = urllib.request.Request(url, headers=self.headers)
        response = urllib.request.urlopen(request)
        soup = BeautifulSoup(response, "lxml")
        tds = soup.find_all("td")
        for td in tds:
            string = str(td.string)
            if re.search(self.IPRegular, string):
                ips.append(string)
        print(ips)
        return ips

    def main(self, total_page, loop_times, each_num):
        """
        调度方法
        :param total_page: 设置博客总页数
        :param loop_times: 设置循环次数
        :param each_num: 设置每一页要随机挑选文章数
        :return:
        """
        jishu = 0
        i = 0
        # 根据设置次数，打开循环
        while i < loop_times:
            # 遍历，得到每一页的页码
            for j in range(total_page):

                # 调用parseIPList随机产生代理IP，防反爬
                ips = self.parseIPList()
                proxy = {"http": "{}:8080".format(
                ips[random.randint(0, 40)])}
                print(proxy)

                # 拼接每一页的url，并模拟发送请求, 返回响应数据
                html_str = self.send_request(j + 1, proxy)
                # 解析响应数据，得到每一页所有博文的url
                each_page_urls = self.parse_data(html_str)

                #如果列表为空，则跳出本循环
                if len(each_page_urls) == 0:
                    continue
                # 遍历，每一页随机挑选each_num篇文章
                for x in range(each_num):
                    # 随机抽取每一页的一篇博文进行访问，防反爬
                    current_url = random.choice(each_page_urls)
                    status = True if requests.get(
                        current_url, headers=self.headers).content.decode() else False
                    print("当前正在访问的文章是：{}，访问状态：{}".format(current_url, status))
                    time.sleep(1)   # 延时1秒，防反爬
                time.sleep(1)   # 延时1秒，防反爬
                jishu += 1
                print('访问对象次数：' + str(jishu))
            i += 1


if __name__ == '__main__':
    bs = BlogSpider()
    bs.main(3, 3, 2)  # 参数参照main方法说明，酌情设置  (总页数、循环次数、每页随机文章数量),