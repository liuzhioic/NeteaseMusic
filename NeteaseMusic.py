import json
import base64
import requests
import math
from Crypto.Cipher import AES


class NeteaseMusic:
    """
    网易云相关访问接口和API
    """

    __headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Host": "music.163.com",
        "Origin": "https://music.163.com",
        "Referer": "https://music.163.com",
        "User-Agent": (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
        )
    }

    __listening_list_api = 'http://music.163.com/weapi/v1/play/record'
    __comment_api = 'http://music.163.com/weapi/v1/resource/comments/R_SO_4_%s'
    __hot_comment = 'http://music.163.com/api/v1/resource/comments/R_SO_4_%s'

    __encseckey = (
        '257348aecb5e556c066de214e531faadd1c55d814'
        'f9be95fd06d6bff9f4c7a41f831f6394d5a3fd2e3'
        '881736d94a02ca919d952872e7d0a50ebfa1769a7'
        'a62d512f5f1ca21aec60bc3819a9c3ffca5eca9a0'
        'dba6d6f7249b06f5965ecfff3695b54e1c28f3f62'
        '4750ed39e7de08fc8493242e26dbc4484a01c76f7'
        '39e135637c'
    )

    @staticmethod
    def __aes_encrypt(text, key, iv) -> str:
        """
        AES加密参数
        :param text: dict 具体参数
        :param key:  key
        :param iv:   iv
        :return:     加密数据
        """
        text = json.dumps(text)
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        encryptor = AES.new(key.encode(), AES.MODE_CBC, iv)
        encrypt_text = encryptor.encrypt(text.encode())
        encrypt_text = str(base64.b64encode(encrypt_text))[2:-1]
        return encrypt_text

    def __encrypt_param(self, first_param) -> str:
        """
        对请求参数进行加密，生成可验证通过的合法请求参数
        :param first_param:
        :return:
        """
        iv = b'0102030405060708'
        first_key = '0CoJUm6Qyw8W8jud'
        second_key = 16 * 'F'

        h_enctext = self.__aes_encrypt(first_param, first_key, iv)
        h_enctext = self.__aes_encrypt(h_enctext, second_key, iv)

        return h_enctext

    @staticmethod
    def __params_listening_list(user_id) -> dict:
        """
        获取听歌排行需要的参数
        :return: dict
        """

        return {'uid': user_id, 'type': -1, 'limit': 1000, 'offset': 0, 'total': True, 'csrf_token': ''}

    @staticmethod
    def __params_comments(page, pagesize) -> dict:
        """
        获取所有评论需要的参数
        :param page:     第几页
        :param pagesize: 页大小
        :return:
        """
        offset = int(page - 1) * pagesize
        return {'rid': '', 'offset': offset, 'total': False, 'limit': pagesize, 'csrf_token': ''}

    def __get_data(self, url, params) -> dict:
        """
        向网易发送请求
        :param params: 参数字符串
        :return: 请求结果
        """

        data = {
            'params': params,
            'encSecKey': self.__encseckey
        }

        return requests.post(url, headers=self.__headers, data=data).json()

    def get_listening_list(self, user_id) -> dict:
        """
        获取听歌排行
        :param user_id: 要获取的用户id
        :return:  排行榜数据
        """
        first_param = self.__params_listening_list(user_id)
        first_param = self.__encrypt_param(first_param)
        response = self.__get_data(self.__listening_list_api, first_param)

        response.update({'status': '1', 'msg': 'OK'})

        if response['code'] != 200:
            response.update({'status': '-2', 'msg': '该用户的听歌排行不可见。'})

        return response

    def get_hot_comment(self, song_id) -> dict:
        """
        获取精彩评论
        :song_id :    歌曲id
        :return: dict 数据
        """
        return requests.get(self.__hot_comment % song_id, headers=self.__headers).json()

    def __get_comment(self, song_id, page=1, pagesize=100) -> dict:
        """
        获取评论
        :param song_id:歌曲id
        :param page: 第几页
        :param pagesize: 页大小
        :return: 数据
        """
        first_param = self.__params_comments(page, pagesize)
        first_param = self.__encrypt_param(first_param)

        return self.__get_data(self.__comment_api % song_id, first_param)

    def get_all_comment(self, song_id) -> list:
        """
        获取一首歌的全部评论
        :param song_id: 歌曲id
        :return:  dict  数据
        """

        the_first = self.__get_comment(song_id, 610, 100)

        total = the_first['total']

        if total <= 100:
            return [the_first]

        data = list()

        last_page = math.ceil(total / 100)
        page_size = 100

        # 第一页的余数
        first_page_remainder = total % 100

        print('共有：%d条数据，按照100页每条分%d页，第一页余数%d，正在抓取……' % (total, last_page, first_page_remainder))

        # 这个循环是从后往前循环的，为的是处理出现新增的数据重叠的情况
        while last_page:
            print('正在抓取%d页……' % last_page)

            if last_page == 1:
                page_size = first_page_remainder

            data_raw = self.__get_comment(song_id, last_page, page_size)

            if data_raw['total'] != total:
                first_page_remainder += data_raw['total'] - total
                total = data_raw['total']

                if first_page_remainder >= 100:
                    first_page_remainder = total % 100
                    last_page += int(first_page_remainder / 100)

                print("新增评论：总条数：%d\t第一页余数：%d\t当前last_page：%d\t" % (total, first_page_remainder, last_page))

            data.append(data_raw)
            last_page = last_page - 1

        return data
