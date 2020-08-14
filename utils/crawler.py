# -*- coding: utf-8 -*-
import json
import shutil
import requests
from bs4 import BeautifulSoup

dblp_url = "https://dblp.org/db/conf/"


def BS(url):
    """
    url에 request 보내 html을 beautifulsoup으로 parsing
    """
    return BeautifulSoup(requests.get(url).text, "lxml")


class DBLPCrawler:
    """
    DBLP를 크롤링하고 저장하는 클래스
    """

    def __init__(self, save_path="kcss/static/kcss/data/"):
        self.save_path = save_path  # publication save path
        self.author_url_dict = {}  # dblp author의 상세페이지 url 매칭
        self.author_dict = {}  # 여러가지 author의 name을 하나의 primary name으로 관리

    def save(self, conf, year, paper_list):
        """
        conf, year에 맞추어 paper_list를 json 파일 저장
        (ex. publications/ICLR/iclr2020.json)
        """
        path = self.save_path + "publications/" + conf.upper() + "/"
        if not os.path.isdir(path):
            os.mkdir(path)

        with open(path + conf + str(year) + ".json", "w") as f:
            json.dump(paper_list, f)

        print("success")

    def save_author_url_dict(self):
        """
        지금까지 update된 author_url_dict을 저장
        """
        path = self.save_path + "author_url_dict.json"
        if os.path.exists(path):
            with open(path, "r") as f:
                self.author_url_dict.update(json.load(f))
        with open(path, "w") as f:
            json.dump(self.author_url_dict, f)

    def get_conf2dblp(self):
        """
        각 학회의 dblp 축약어를 mapping한 dictionary 리턴
        """
        conf2dblp = {}
        for conf in get_file(self.save_path + "/conferences.txt"):
            conf2dblp[conf] = conf

        if "iclr" in conf2dblp:
            conf2dblp.pop("iclr")
        if "vis" in conf2dblp:
            conf2dblp.pop("vis")

        dblp_dict = {
            "ieee s&p": "sp",
            "usenix security": "uss",
            "usenix atc": "usenix",
            "fse": "sigsoft",
            "ase": "kbse",
            "ec": "sigecom",
            "ubicomp": "huc",
            "neurips": "nips",
        }
        for conf, dblp in dblp_dict.items():
            if conf in conf2dblp:
                conf2dblp[conf] = dblp

        return conf2dblp

    def parse_data(self, rawdata):
        """
        dblp의 하나의 paper에 대한 rawdata(beautifulsoup object)를 parsing
        제목, 저자리스트, url, 페이지수 리턴
        """
        data = rawdata.find("cite", {"class": "data"})

        author_list = []
        for elem in data.find_all("span", {"itemprop": "author"}):
            author = smooth(elem.find("span", {"itemprop": "name"}).text)
            # url = elem.find('a')['href']
            author_list.append(author)
            # self.author_url_dict[author] = url

        title = data.find("span", {"class": "title"}).text
        try:
            pagination = data.find("span", {"itemprop": "pagination"}).text
            if "-" in pagination:
                page_from, page_to = pagination.split("-")
                pages = int(page_to) - int(page_from) + 1
            else:
                pages = 1
        except:
            pages = 0

        try:
            paper_url = (
                rawdata.find("nav", {"class": "publ"})
                .find_all("li", {"class": "drop-down"})[0]
                .find("div", {"class": "body"})
                .find_all("a", {"itemprop": "url"})[0]["href"]
            )
        except:
            paper_url = ""

        return title, author_list, paper_url, pages

    def get_paper_list(self, url):
        """
        dblp 특정 연도/학회 url에서 paper 정보를 담은 list 리턴
        """
        html = BS(url)

        paper_list = []
        for data in html.find_all("li", {"class": "entry inproceedings"}):
            title, author_list, link_url, pages = self.parse_data(data)
            if title and author_list:
                paper_list.append([title, author_list, link_url, pages])

        if not paper_list:
            for data in html.find_all("li", {"class": "entry article"}):
                title, author_list, link_url, pages = self.parse_data(data)
                if title and author_list:
                    paper_list.append([title, author_list, link_url, pages])

        return paper_list

    def update_conf(self, conf, dblp, fromyear, toyear):
        """
        dblp에서 conf학회의 fromyear~toyear연도의 정보를 업데이트
        dblp 패턴 규칙에 따라 크롤링을 다양하게 시도함 (dblp 구조가 바뀔시 코드 업데이트 필요)
        """

        # conf should be in lower case.
        print(conf)
        path = self.save_path + conf.upper() + "/"
        if not os.path.isdir(path):
            os.mkdir(path)

        html = BS(dblp_url + dblp + "/").text

        success_years = []
        # exceptions = []
        for year in range(fromyear, toyear + 1):
            if os.path.exists(path + conf + str(year) + ".json") or not (
                str(year) in html
            ):
                continue

            print(year)
            url = dblp_url + dblp + "/" + dblp + str(year) + ".html"
            paper_list = self.get_paper_list(url)
            if paper_list:
                self.save(conf, year, paper_list)
                success_years.append(year)
                continue

            url = dblp_url + dblp + "/" + dblp + str(year)[2:] + ".html"
            paper_list = self.get_paper_list(url)
            if paper_list:
                self.save(conf, year, paper_list)
                success_years.append(year)
                continue

            url = dblp_url + dblp + "/" + dblp + str(year) + "-1.html"
            paper_list = self.get_paper_list(url)
            if paper_list:
                i = 2
                while True:
                    url = "{}{}/{}{}-{}.html".format(dblp_url, dblp, dblp, year, i)
                    temp = self.get_paper_list(url)
                    if temp:
                        paper_list += temp
                    else:
                        break
                    i += 1
                self.save(conf, year, paper_list)
                success_years.append(year)
                continue

            url = dblp_url + dblp + "/" + dblp + str(year)[2:] + "-1.html"
            paper_list = self.get_paper_list(url)
            if paper_list:
                i = 2
                while True:
                    url = "{}{}/{}{}-{}.html".format(
                        dblp_url, dblp, dblp, str(year)[2:], i
                    )
                    temp = self.get_paper_list(url)
                    if temp:
                        paper_list += temp
                    else:
                        break
                    i += 1
                self.save(conf, year, paper_list)
                success_years.append(year)
                continue

        return success_years

    def update(self, fromyear, toyear):
        """
        fromyear~toyear의 모든 학회를 dblp에서 업데이트
        """

        for conf, dblp in self.get_conf2dblp().items():
            self.update_conf(conf, dblp, fromyear, toyear)

    def update_exceptions(self):
        """
        dblp url의 convention을 따르지 않는 특정 학회/연도의 경우,
        data/corrections.txt에 예외 url을 저장하고 있음
        해당 url로 재 크롤링 및 저장
        """
        with open(self.save_path + "corrections.txt", "r") as f:
            for line in f.readlines():
                words = [word.strip() for word in line.strip().split()]
                conf = words[0].replace("-", " ")
                year = words[1]
                print(conf, year)

                paper_list = []
                for url in words[2:]:
                    paper_list += self.get_paper_list(url)
                self.save(conf, year, paper_list)

        # self.save_author_url_dict()
