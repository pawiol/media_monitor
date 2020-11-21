
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, urlunsplit
import time
import re
import uuid
import hashlib
import dataset
import collections
from simplediff import html_diff
from selenium import webdriver
from PIL import Image
from instapy_cli import client

class TVPInfo:

    def __init__(self, crawler_name, url, insta_user, insta_pass, delay=0.01, user_agent=None):

        self.name = crawler_name
        self.start_url = url
        self.delay = delay
        self.user_agent = user_agent
        self.request_session = requests.Session()
        self.insta_user = insta_user
        self.insta_pass = insta_pass

        self.run_moment = time.time()
        self.main_page = self.get_site(self.start_url)
        self.anchor_list = []
        self.anchor_dict = {}

        self.db_file = dataset.connect('sqlite:///mmonitor.db')
        self.article_db = self.db_file['tvp_news']

        self.media_filename = str()
        self.media_filenames = list()


    def insta_msg(self, insta_txt):

        with client(self.insta_user, self.insta_pass) as cli:
            cli.upload('./output/' + self.media_filename + '.png', insta_txt)

    def inst_stories(self):

        if len(self.media_filenames) < 1:
            return True
        else:
            with client(self.insta_user, self.insta_pass) as cli:
                for i in range(0, len(self.media_filenames)):
                    cli.upload(self.media_filenames[i], story=True)
                    time.sleep(5)

        return True

    def prepare_img(self, article_id, tag):

        html = """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <link rel="stylesheet" href="./css/styles.css">
          </head>
          <body>
          <p>
          {}
          </p>
          </body>
        </html>
        """.format(html_diff(self.anchor_dict[article_id][tag]))
        with open('tmp.html', 'w') as f:
            f.write(html)

        driver = webdriver.PhantomJS()
        driver.get('tmp.html')
        e = driver.find_element_by_xpath('//p')
        start_height = e.location['y']
        block_height = e.size['height']
        end_height = start_height
        start_width = e.location['x']
        block_width = e.size['width']
        end_width = start_width
        total_height = start_height + block_height + end_height
        total_width = start_width + block_width + end_width
        timestamp = str(int(time.time()))
        driver.save_screenshot('./tmp.png')
        img = Image.open('./tmp.png')
        img2 = img.crop((0, 0, total_width, total_height))
        if int(total_width) > int(total_height * 2):
            background = Image.new('RGBA', (total_width, int(total_width / 2)),
                                   (255, 255, 255, 0))
            bg_w, bg_h = background.size
            offset = (int((bg_w - total_width) / 2),
                      int((bg_h - total_height) / 2))
        else:
            background = Image.new('RGBA', (total_width, total_height),
                                   (255, 255, 255, 0))
            bg_w, bg_h = background.size
            offset = (int((bg_w - total_width) / 2),
                      int((bg_h - total_height) / 2))
        background.paste(img2, offset)
        self.media_filename = timestamp + '_' + self.anchor_dict[article_id]['article_hash'] + '_' + article_id
        self.media_filenames.append(self.media_filename)
        background.save('./output/' + self.media_filename + '.png')

        return True

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

    def get_all_anchor_frontpage(self):

        find_all_a = self.main_page.find_all('a', href=True)

        for a_ in find_all_a:
            if re.search('/\d+/', a_.attrs['href']) \
                    and 'title' not in a_.attrs.keys() \
                    and a_.attrs.get('class', [''])[0] != 'nav__reference' \
                    and a_.attrs['href'] != 'http://www.tvp.info/284879/kontakt':
                self.anchor_list.append(a_)

        return self.anchor_list

    def transform_anchor_to_dict(self):

        save_time = time.time()
        sql_format_run_moment = time.strftime('%Y-%m-%d %H:%M:%S.000', time.localtime(self.run_moment))
        sql_format_save_time = time.strftime('%Y-%m-%d %H:%M:%S.000', time.localtime(save_time))

        for a_ in self.anchor_list:

            a_route = a_.attrs['href'] if 'http' in a_.attrs['href'] else 'https://www.tvp.info/'+ a_.attrs['href']
            a_id = re.findall('/(\d+)/', a_.attrs['href'], 0)[0]
            a_txt = re.sub(r'\s+', ' ', a_.text.strip().replace('\n', '').replace('"', "'"))

            self.anchor_dict[a_id] = {'art_id': a_id,
                                  'art_route': a_route,
                                  'art_route_txt': a_txt if len(a_txt) > 0 else ''
                                  }

            self.anchor_dict[a_id]['id_'] = str(uuid.uuid4())
            self.anchor_dict[a_id]['epoch_app_start'] = self.run_moment
            self.anchor_dict[a_id]['date_app_start'] = sql_format_run_moment
            self.anchor_dict[a_id]['epoch_app_save'] = save_time
            self.anchor_dict[a_id]['date_app_save'] = sql_format_save_time
            self.anchor_dict[a_id]['mm_name'] = self.name
            self.anchor_dict[a_id]['last_checkup'] = self.run_moment


        return self.anchor_dict

    def get_article_data(self, art_id, url_):

        obj = self.get_site(url_)

        headline = ''
        article = ''

        for head_ in obj.find_all('p', {'class': 'am-article__heading article__width'}):
            headline += re.sub(r'\s+', ' ', head_.text.strip().replace('\n', '').replace('"', "'"))
            article += re.sub(r'\s+', ' ', head_.text.strip().replace('\n', '').replace('"', "'"))

        for paragraph_ in obj.find_all('p', {'class': 'am-article__text article__width'}):
            article += re.sub(r'\s+', ' ', paragraph_.text.strip().replace('\n', '').replace('"', "'"))

        self.anchor_dict[art_id]['headline_txt'] = article
        self.anchor_dict[art_id]['article_txt'] = article

        return (headline, article)

    def get_data(self):

        # load all of anchores
        self.get_all_anchor_frontpage()
        # transform anchors to dict form
        self.transform_anchor_to_dict()
        # check data in db
        for article_id in self.anchor_dict.keys():

            print(article_id, self.anchor_dict[article_id]['art_route'])
            self.get_article_data(article_id, self.anchor_dict[article_id]['art_route'])
            temp_ord_dict = collections.OrderedDict(sorted(self.anchor_dict[article_id].items()))

            del temp_ord_dict['id_']
            del temp_ord_dict['epoch_app_start']
            del temp_ord_dict['date_app_start']
            del temp_ord_dict['epoch_app_save']
            del temp_ord_dict['date_app_save']
            del temp_ord_dict['last_checkup']

            self.anchor_dict[article_id]['article_hash'] = hashlib.sha224(
                repr(temp_ord_dict.items()).encode('utf-8')).hexdigest()

            if self.article_db.find_one(art_id=article_id) is None:
                # save new data
                logging.info('Adding new article: {article_url}'.format(article_url=self.anchor_dict[article_id]))

                self.anchor_dict[article_id]['article_version'] = 1
                self.article_db.insert(self.anchor_dict[article_id])

            else:

                logging.info('Updating article: {article_url}'.format(article_url=self.anchor_dict[article_id]))
                # update article if there is a reason
                check_last_version = self.db_file.query("""SELECT rowid, *
                                                            FROM tvp_news
                                                            WHERE art_id = "{art_id}"
                                                            ORDER BY epoch_app_save DESC
                                                            LIMIT 1""".format(art_id=article_id))

                for row_ in check_last_version:

                    if row_['article_hash'] != self.anchor_dict[article_id]['article_hash']:
                        logging.info('Logging change for: {article_url}'.format(article_url=self.anchor_dict[article_id]))
                        self.anchor_dict[article_id]['article_version'] = int(row_['article_version']) + 1

                        if row_['art_route'] != self.anchor_dict[article_id]['art_route']:

                            self.anchor_dict[article_id]['art_route_change'] = html_diff(row_['art_route'],
                                                                                         self.anchor_dict[article_id]['art_route'])

                            self.prepare_img(article_id, 'art_route_change')

                            insta_txt = 'Change in link' +  \
                                        + '\r\n' \
                                        + '#tvp #tvpinfo #monitormedia'

                            self.insta_msg(insta_txt)



                        if row_['art_route_txt'] != self.anchor_dict[article_id]['art_route_txt']:
                            self.anchor_dict[article_id]['art_route_txt_change'] = html_diff(row_['art_route_txt'],
                                                                                         self.anchor_dict[article_id][
                                                                                             'art_route_txt'])

                            self.prepare_img(article_id, 'art_route_txt_change')

                            insta_txt = 'Change in link text' + \
                                        + '\r\n' \
                                        + '#tvp #tvpinfo #monitormedia'

                            self.insta_msg(insta_txt)

                        if row_['headline_txt'] != self.anchor_dict[article_id]['headline_txt']:
                            self.anchor_dict[article_id]['headline_change'] = html_diff(row_['headline_txt'],
                                                                                         self.anchor_dict[article_id][
                                                                                             'headline_txt'])

                            self.prepare_img(article_id, 'headline_change')

                            insta_txt = 'Change in article headline' + \
                                        + '\r\n' \
                                        + '#tvp #tvpinfo #monitormedia'

                            self.insta_msg(insta_txt)

                        if row_['article_txt'] != self.anchor_dict[article_id]['article_txt']:
                            self.anchor_dict[article_id]['art_txt_change'] = html_diff(row_['article_txt'],
                                                                                         self.anchor_dict[article_id][
                                                                                             'article_txt'])

                            self.prepare_img(article_id, 'art_txt_change')

                            insta_txt = 'Change in article text' + \
                                        + '\r\n' \
                                        + '#tvp #tvpinfo #monitormedia'

                            self.insta_msg(insta_txt)

                        self.article_db.insert(self.anchor_dict[article_id])


                    else:
                        logging.info('Update with no change for: {article_url}'.format(article_url=self.anchor_dict[article_id]))
                        update_data = dict(id=row_['id'], last_checkup=self.anchor_dict[article_id]['last_checkup'])
                        self.article_db.update(update_data, ['id'])

        self.inst_stories()










    # def gogo_mmonitor(self):
    #
    #     self.get_all_anchor_frontpage()
    #     self.transform_anchor_to_dict()





    # def save_a_to_db(self):
    #
    #     connection = sqlite3.connect(self.db_file)
    #     cursor = connection.cursor()
    #
    #     table_columns = """
    #                     id_,
    #                     epoch_app_start,
    #                     date_app_start,
    #                     epoch_app_save,
    #                     date_app_save,
    #                     page,
    #                     art_id,
    #                     art_route,
    #                     art_txt,
    #                     change
    #                     """
    #
    #     batch_identifier = str(uuid.uuid4())
    #     save_time = time.time()
    #     sql_format_run_moment = time.strftime('%Y-%m-%d %H:%M:%S.000', time.localtime(self.run_moment))
    #     sql_format_save_time = time.strftime('%Y-%m-%d %H:%M:%S.000', time.localtime(save_time))
    #
    #     a_to_save = self.prepare_a_to_db()
    #     progress_count = 1
    #     len_a = len(a_to_save)
    #
    #     for art_ in a_to_save.keys():
    #
    #         sql_set = (
    #                    batch_identifier,
    #                    self.run_moment,
    #                    sql_format_run_moment,
    #                    save_time,
    #                    sql_format_save_time,
    #                    self.name,
    #                    a_to_save[art_]['a_id'],
    #                    a_to_save[art_]['a_route'],
    #                    a_to_save[art_]['a_txt'],
    #                    ''
    #                    )
    #
    #         try:
    #
    #             cursor.execute("INSERT INTO {table_name} ({table_columns}) VALUES ({table_values})". \
    #                            format(table_name='tvp_news', table_columns=table_columns,
    #                                   table_values=','.join(['"'+str(value_)+'"' for value_ in sql_set])))
    #
    #             connection.commit()
    #
    #         except sqlite3.IntegrityError:
    #
    #             print('ERROR: ID already exists in PRIMARY KEY column {}'.format
    #                   (sql_set))
    #
    #         print(progress_count/len_a)
    #         progress_count += 1


# tvp_info = TVPInfo(crawler_name='tvp_info', url='https://www.tvp.info/50798794/koronawirus-duza-liczba-zgonow-ekspert-to-wynik-wczesniejszych-rekordow-zakazen')
# tvp_info.get_article_data()
