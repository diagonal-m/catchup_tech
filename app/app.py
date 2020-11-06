import os
import json
from time import sleep
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

from consts import QIITA_WEBHOOK, BLOG_WEBHOOK


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


class TechBlog:
    """
    テックブログキャッチアップクラス
    """
    def __init__(self):
        """
        初期化メソッド
        """
        self.td = timedelta(days=1)

    def hatena_culation(self, to_day: datetime) -> str:
        """
        Hatena Developer Blogからキュレーションする関数
        @return: 送信するメッセージ
        """
        hatena = 'https://developer.hatenastaff.com/archive'
        urls, titles = list(), list()
        message = ''
        yesterday = (to_day - self.td).strftime('%Y-%m-%d')
        soup = get_soup(hatena)

        for report in soup.find('div', id='main-inner').find_all('section'):
            if yesterday == report.find('time').text.strip():
                titles.append(report.find('h1').text_strip())
                urls.append(report.find('a', class_='entry-title-link').attrs['href'])
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


class CatchupTech(Qiita, TechBlog):
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
            'qiita': {
                'func': self.qiita_culation,
                'args': self.day_of_week,
                'webhook': QIITA_WEBHOOK,
            },
            'tech_blog': {
                'func': self.hatena_culation,
                'args': self.today,
                'webhook': BLOG_WEBHOOK
            }
        }
        for _, func in functions.items():
            message = func['func'](func['args'])
            if message:
                slack(func['webhook'], message)


if __name__ == '__main__':
    ct = CatchupTech()
    ct.exec()
