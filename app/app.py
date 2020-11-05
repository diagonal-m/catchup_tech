import os
import json
from time import sleep
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from consts import QIITA_WEBHOOK


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

    def culation(self, day_of_week: str) -> str:
        """
        曜日ごとに指定したタグの過去一週間のLGTMが多かった投稿を返す

        @param day_of_week: 曜日 e.g.) 'Sun'
        @return: 送信するメッセージ
        """
        base_url = 'https://qiita.com/tags/'
        urls = list()
        tags = self.tag_dict[day_of_week]['tags']
        for tag in tags:
            qiita_tag_url = base_url + tag
            soup = get_soup(qiita_tag_url)
            report_list = [
                report.find('div', class_='css-xofpgy eomqo7a3')
                for report in
                soup.find('div', class_='css-10v1rem e1mdkbz70').find_all('div', class_='css-bbe22u eomqo7a0')
            ]
            urls.extend([
                [report.find_all('a')[1].attrs['href'] for report in report_list]
            ])
            sleep(3)

        urls = list(set(urls))

        return '\n'.join(urls)


class CatchupTech(Qiita):
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
        slack(QIITA_WEBHOOK, self.culation(self.day_of_week))


if __name__ == '__main__':
    ct = CatchupTech()
    ct.exec()
