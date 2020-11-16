import os
import json
from time import sleep
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

from consts import QIITA_WEBHOOK, BLOG_WEBHOOK, NEWS_WEBHOOK


def slack(webhook: str, message: str):
    """
    スラックにメッセージを送信する関数
    @param webhook: webhook
    @param message: 送信するメッセージ
    """
    requests.post(webhook, data=json.dumps({
        "text": message
    }))


def get_soup(url: str) -> BeautifulSoup:
    """

    @param url:
    @return:
    """
    response = requests.get(url, timeout=(5.0, 30)).text
    return BeautifulSoup(response, 'html.parser')


class TechNews:
    """
    テックニュースサイトキャッチアップクラス
    """
    def ai_scholar_culation(self, to_day: datetime) -> str:
        """
        AI-SCHOLARからキュレーションする関数
        @param to_day: 実行日時のdatetime
        @return: 送信するメッセージ
        """
        ai_scholar = 'https://ai-scholar.tech/'
        urls, titles = list(), list()
        message = ''
        yesterday = (to_day - timedelta(days=1)).strftime('%Y年%m月%d日')
        soup = get_soup(ai_scholar)

        for report in soup.find('main', class_='main main--index').find_all('article'):
            if yesterday == report.find('time').text.strip():
                titles.append(report.find('h3').text.strip())
                urls.append(report.find('a').attrs['href'])
            else:
                break
        if len(titles) == 0:
            return message

        message_list = [f'<{u}|{t}>' for u, t in zip(urls, titles)]

        return '\n'.join(message_list)


class TechBlog:
    """
    テックブログキャッチアップクラス
    """
    def hatena_culation(self, to_day: datetime) -> str:
        """
        Hatena Developer Blogからキュレーションする関数
        @return: 送信するメッセージ
        """
        hatena = 'https://developer.hatenastaff.com/archive'
        urls, titles = list(), list()
        message = ''
        yesterday = (to_day - timedelta(days=1)).strftime('%Y-%m-%d')
        soup = get_soup(hatena)

        for report in soup.find('div', id='main-inner').find_all('section'):
            if yesterday == report.find('time').text.strip():
                titles.append(report.find('h1').text.strip())
                urls.append(report.find('a', class_='entry-title-link').attrs['href'])
            else:
                break

        if len(titles) == 0:
            return message

        message_list = [f'<{u}|{t}>' for u, t in zip(urls, titles)]

        return '\n'.join(message_list)

    def dena_culation(self, to_day: datetime) -> str:
        """
        DeNA Engineer's Blogからキュレーションする関数
        @param to_day: 実行日時
        @return: 送信するメッセージ
        """
        dena = 'https://engineer.dena.com'
        urls, titles = list(), list()
        message = ''
        yesterday = (to_day - timedelta(days=1)).strftime('%B %d, %Y')
        soup = get_soup(dena)

        for report in soup.find('div', class_='list-content').find_all('article', class_='article-list'):
            if yesterday == report.find_all('div')[1].text.split('|')[1].strip():
                titles.append(report.find('h2').text)
                urls.append(dena + report.find('div').find('a').attrs['href'])
            else:
                break

        if len(titles) == 0:
            return message

        message_list = [f'<{u}|{t}>' for u, t in zip(urls, titles)]

        return '\n'.join(message_list)


class Qiita:
    """
    qiitaキャッチアップクラス
    """
    def __init__(self):
        """
        初期化メソッド
        """
        self.tag_dict = {
            'Sun': {'tags': ['AWS', 'lambda', 'インフラ', 'Linux', 'ec2']},
            'Mon': {'tags': ['python', 'Django']},
            'Tue': {'tags': ['HTML5', 'CSS', 'JavaScript']},
            'Wed': {'tags': ['Docker', 'docker-compose']},
            'Thu': {'tags': ['新人プログラマ応援', '初心者']},
            'Fri': {'tags': ['論文読み', '機械学習']},
            'Sat': {'tags': ['GoogleCloudPlatform', 'GitHubActions']}
        }

    def qiita_culation(self, day_of_week: str) -> str:
        """
        曜日ごとに指定したタグの過去一週間のLGTMが多かった投稿を返す

        @param day_of_week: 曜日 e.g.) 'Sun'
        @return: 送信するメッセージ
        """
        base_url = 'https://qiita.com/tags/'
        urls, titles = list(), list()
        tags = self.tag_dict[day_of_week]['tags']
        for tag in tags:
            qiita_tag_url = base_url + tag
            soup = get_soup(qiita_tag_url)
            report_list = [
                report.find('div', class_='css-xofpgy eomqo7a3')
                for report in
                soup.find('div', class_='css-10v1rem e1mdkbz70').find_all('div', class_='css-bbe22u eomqo7a0')
            ]
            titles.extend([
                report.text for report in report_list
            ])
            urls.extend([
                report.find_all('a')[1].attrs['href'] for report in report_list
            ])
            sleep(3)

        message_list = [f'<{u}|{t}>' for u, t in zip(urls, titles)]

        message_list = list(set(message_list))

        return '\n'.join(message_list)


class CatchupTech(Qiita, TechBlog, TechNews):
    """
    キャッチアップテッククラス
    """
    def __init__(self):
        """
        初期化メソッド
        """
        super().__init__()
        self.today = datetime.today()
        self.day_of_week = self.today.strftime('%a')  # e.g.) 'Mon'

    def exec(self):
        """
        """
        functions = {
            'Qiita': {
                'func': self.qiita_culation,
                'args': self.day_of_week,
                'webhook': QIITA_WEBHOOK,
            },
            'Hatena Developer Blog': {
                'func': self.hatena_culation,
                'args': self.today,
                'webhook': BLOG_WEBHOOK
            },
            "DeNA Developer's Blog": {
                'func': self.dena_culation,
                'args': self.today,
                'webhook': BLOG_WEBHOOK
            },
            "AI-SCHOLAR": {
                'func': self.ai_scholar_culation,
                'args': self.today,
                'webhook': NEWS_WEBHOOK
            }
        }
        for site, func in functions.items():
            message = func['func'](func['args'])
            if message:
                slack(func['webhook'], f'{site}\n{message}')


if __name__ == '__main__':
    ct = CatchupTech()
    ct.exec()
