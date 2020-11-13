import requests
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, urlunsplit, urljoin
import time
import re
import uuid
import sqlite3


class TVPInfo:

    def __init__(self, crawler_name, url, delay=0.01, user_agent=None):

        self.name = crawler_name
        self.start_url = url
        self.delay = delay
        self.user_agent = user_agent
        self.sites_crawled = set()
        self.sites_to_crawl = [self.start_url]
        self.request_session = requests.Session()
        self.sites_length = 0
        self.parser_data = []
        self.main_page = self.get_site(self.start_url)
        self.a_list = []
        self.run_moment = time.time()
        self.db_file = 'news_diff.db'

    def normalize_url(self, url):

        return urlunsplit(urlsplit(url))

    def get_url(self, url):

        time.sleep(self.delay)

        headers = {}

        if self.user_agent:
            headers['User-Agent'] = self.user_agent

        return self.request_session.get(url, headers=headers)

    def get_site(self, url):

        normalized_url = self.normalize_url(url)

        site_request = self.get_url(normalized_url)

        if site_request.status_code == 200:

            return BeautifulSoup(site_request.text,'lxml')

        else:

            return None

    def get_meta_data(self, bs_obj):

        all_meta = bs_obj.find_all('meta')

        return all_meta


    def get_all_a(self):

        find_all_a = self.main_page.find_all('a', href=True)

        for a_ in find_all_a:
            if re.search('/\d+/', a_.attrs['href']) \
                    and 'title' not in a_.attrs.keys()\
                    and a_.attrs.get('class', [''])[0] != 'nav__reference'\
                    and a_.attrs['href'] != 'http://www.tvp.info/284879/kontakt':
                self.a_list.append(a_)

        return self.a_list

    def prepare_a_to_db(self):

        dic_articles = {}

        for a_ in self.a_list:

            a_route = a_.attrs['href'] if 'http' in a_.attrs['href'] else 'https://www.tvp.info/'+ a_.attrs['href']
            a_id = re.findall('/(\d+)/', a_.attrs['href'], 0)[0]
            a_txt = re.sub(r'\s+', ' ', a_.text.strip().replace('\n', '').replace('"', "'"))

            dic_articles[a_id] = {'a_id': a_id,
                                  'a_route': a_route,
                                  'a_txt': a_txt if len(a_txt) > 0 else ''
                                  }

        return dic_articles

    def save_a_to_db(self):

        connection = sqlite3.connect(self.db_file)
        cursor = connection.cursor()

        table_columns = """
                        id_,
                        epoch_app_start,
                        date_app_start,
                        epoch_app_save,
                        date_app_save,
                        page,
                        art_id,
                        art_route,
                        art_txt,
                        change
                        """

        batch_identifier = str(uuid.uuid4())
        save_time = time.time()
        sql_format_run_moment = time.strftime('%Y-%m-%d %H:%M:%S.000', time.localtime(self.run_moment))
        sql_format_save_time = time.strftime('%Y-%m-%d %H:%M:%S.000', time.localtime(save_time))

        a_to_save = self.prepare_a_to_db()
        progress_count = 1
        len_a = len(a_to_save)

        for art_ in a_to_save.keys():

            sql_set = (
                       batch_identifier,
                       self.run_moment,
                       sql_format_run_moment,
                       save_time,
                       sql_format_save_time,
                       self.name,
                       a_to_save[art_]['a_id'],
                       a_to_save[art_]['a_route'],
                       a_to_save[art_]['a_txt'],
                       ''
                       )

            try:

                cursor.execute("INSERT INTO {table_name} ({table_columns}) VALUES ({table_values})". \
                               format(table_name='tvp_news', table_columns=table_columns,
                                      table_values=','.join(['"'+str(value_)+'"' for value_ in sql_set])))

                connection.commit()

            except sqlite3.IntegrityError:

                print('ERROR: ID already exists in PRIMARY KEY column {}'.format
                      (sql_set))

            print(progress_count/len_a)
            progress_count += 1




if __name__ == '__main__':
    tvp_info = TVPInfo(crawler_name='tvp_info', url='http://www.tvp.info')
    tvp_info.get_all_a()
    tvp_info.save_a_to_db()
