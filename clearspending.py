# -*- coding: utf-8 -*-
import urllib.parse
import urllib.request
import http
import json
from pathlib import Path
import time


class ClearspendingSearch(object):
    """Класс для полнотекстового поиска госконтрактов посредством API Госзатрат.
    Источник данных: "Проект КГИ "Госзатраты" (clearspending.ru).
    Документация по API, связанному с поиском контрактов:
    https://github.com/clearspending/clearspending-examples/wiki/Описание-API-Контракты
    """

    # URL к API Госзатрат
    search_url = 'http://openapi.clearspending.ru/restapi/v3/contracts/search/?'
    # количество контрактов на страницу
    per_page = 50
    # статистика по обращениеям к URL для скачивания
    resp_stat = []
    # максимальное количество засыпаний программы, если получены неполные данные
    max_sleep_count = 3

    def __init__(self, **kwargs):
        """
        Инициализация класса.

        :param kwargs:
            downloads_dir: каталог, куда скачивать данные в JSON-формате
            file_prefix: префикс для имён файлов, в которые сохранять данные контрактов
        """

        self._downloads_stat = None
        self._search_params = None
        self._search_resp = None
        self._filter_search_resp_func = None
        self.downloads_dir = kwargs.get('downloads_dir', None)
        self.file_prefix = kwargs.get('file_prefix', None)
        self._prepare_dir(self.downloads_dir)

    @staticmethod
    def _prepare_dir(dir_path):
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def search(search_url, params):
        """
        Поиск контрактов в API Госзатрат.

        :param search_url: URL к API
        :param params: параметры для поиска
        """

        while True:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
                data = urllib.parse.urlencode(params)
                url = search_url + str(data)
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=60) as response:
                    return {'url': url, 'response': response.read(), 'status': 'success'}
            except urllib.request.HTTPError as e:
                return {'url': url, 'response': str(e), 'status': 'http_error'}
            except http.client.IncompleteRead as e:
                return {'url': url, 'response': str(e), 'status': 'incomplete_data'}
            except (ConnectionError, TimeoutError) as e:
                {'url': url, 'response': str(e), 'status': 'connection_error'}

    @staticmethod
    def save(data, filename):
        """
        Сохранение JSON-данных в файле.

        :param data: данные в JSON-формате, которые сохранить
        :param filename: имя файла, куда сохранить
        """

        if data is not None:
            try:
                with open(filename, 'w+', encoding='utf8') as f:
                    json.dump(data, f, ensure_ascii=False)
                    f.close()
            except Exception as e:
                raise Exception("Error on saving:", str(e))
        else:
            print("Nothing to save")

    def generate_filename(self, page):
        """
        Генерирует имя файла для сохранения данных
        на основе номера скачиваемой страницы и префикса для имён файлов.

        :param page: номер страницы
        """

        filename_chunks = []
        if self.file_prefix is not None and len(self.file_prefix) > 0:
            filename_chunks.append(self.file_prefix)
        filename_chunks = filename_chunks + ['page', str(page)]
        return '_'.join(filename_chunks) + ".json"

    def download_page(self, page):
        """Скачивание одной страницы данных из API.

        :param page: номер страницы
        """

        resp = self.search(self.search_url,
                           {**self.search_params,
                            'page': page,
                            'perpage': self.per_page})
        # если нашлись контракты, то записываем их
        if resp['status'] == 'success':
            self._search_resp = json.loads(resp['response'])
            del resp['response']
            self._prepare_dir(self.downloads_dir)
            filename = '/'.join([self.downloads_dir, self.generate_filename(page)])
            if len(self.last_search_resp) > 0:
                self.save(self.last_search_resp, filename)
                resp['message'] = ''
                return {**resp, 'filename': filename}
            resp['message'] = 'empty'
            return {**resp, 'filename': None}
        self._search_resp = None
        resp['message'] = resp['response']
        del resp['response']
        return {**resp, 'filename': None}

    def download_all(self):
        """Поиск и постраничное скачивание всех контрактов."""

        self._downloads_stat = list()
        page = 1
        sleep_count = 0
        while True:
            download_res = self.download_page(page)
            self._downloads_stat.append(download_res)
            # Если на текущей странице данных нет,
            # то завершаем цикл скачивания.
            if download_res['status'] == 'http_error':
                break
            if download_res['status'] in ['incomplete_data', 'connection_error']:
                if sleep_count < self.max_sleep_count:
                    print('sleep...', sleep_count)
                    time.sleep(10)
                    sleep_count += 1
                else:
                    break
            if download_res['status'] == 'success':
                sleep_count = 0
                page += 1

    @property
    def filter_search_resp_func(self):
        return self._filter_search_resp_func

    @filter_search_resp_func.setter
    def filter_search_resp_func(self, func):
        self._filter_search_resp_func = func

    @property
    def last_search_resp(self):
        if self.filter_search_resp_func is not None:
            try:
                return self.filter_search_resp_func(self._search_resp)
            except Exception as e:
                raise Exception('Невозможно отфильтровать данные.', str(e))
        return self._search_resp

    @property
    def downloads_stat(self):
        return self._downloads_stat

    @property
    def page(self):
        try:
            return self.last_search_resp['contracts']['page']
        except:
            return None

    @property
    def search_params(self):
        return self._search_params

    @search_params.setter
    def search_params(self, value):
        self._search_params = value

    @property
    def downloads_dir(self):
        return self._downloads_dir

    @downloads_dir.setter
    def downloads_dir(self, value):
        self._downloads_dir = value
        if self._downloads_dir is not None:
            if self._downloads_dir[-1] != '/':
                self._downloads_dir = self._downloads_dir + '/'


if __name__ == "__main__":

    print('Поиск и скачивание контрактов.')
    print('Источник данных:', '"Проект КГИ "Госзатраты" (clearspending.ru)')
    cs = ClearspendingSearch(downloads_dir='pushkin', file_prefix='data')
    cs.search_params = {'productsearchlist': 'Пушкин'}
    cs.download_all()
