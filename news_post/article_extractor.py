# coding=utf-8
import cStringIO
import urllib2
from PIL import Image

from bs4 import BeautifulSoup
import ast
import requests
import datetime
import time
import pymysql.cursors
import pymysql
import xlwt
import json
from lxml import etree
from lxml import html


from urllib2 import quote
import string
import os




class GetBlockZoneNews(object):


    def get_links(self):
        url = "https://www.accesswire.com/articlereport.aspx?id=526208&token=z066ai9x25etnca9wc2g"
        r = requests.get(url)
        raw_text = r.text
        etree_text = etree.HTML(raw_text)
        div_path = etree_text.xpath('.//div[@id="accordion"]/div/ul/li/a/@href')

        div_path2 = etree_text.xpath('.//div[@id="accordion"]/div/ul')[2].xpath('li/a/@href')



        excel = xlwt.Workbook(encoding='utf-8')  # 创建一个Excel
        sheet = excel.add_sheet('通稿')

        for index in range(0, len(div_path)):
            sheet.write(index, 1, div_path[index])

        for index in range(0, len(div_path2)):
            sheet.write(index, 10, div_path2[index])
        excel.save('/Users/Eddy/BlockZone/sample.xls')




    #  url = 'https://blockzone.com/press/page/{page_num}/'
    #  url = 'https://blockzone.com/news/page/{page_num}/'
    #  url = 'https://blockzone.com/insights/page/{page_num}/'
    #   url = 'https://blockzone.com/companies/page/{page_num}/'
    # choose the different url for different categories and the page index is bonded with specific cate
    def get_news(self):

        for page_index in range(1, 3):
            url = 'https://blockzone.com/press/page/{page_num}/'.format(page_num = page_index)
            r = requests.get(url)
            demo = r.text
            entree_page = etree.HTML(demo)
            div_path = entree_page.xpath('.//a[contains(@class,"read_more")]/@href')
            if len(div_path) > 0:
                # div_path_first = div_path[0]

                for index in range(0, len(div_path)):
                    response = requests.get(div_path[index])
                    res_text = response.text
                    entree_text = etree.HTML(res_text)
                    try:
                        self.construct_res(entree_text, page_index)
                    except Exception as e:
                        print (entree_text.xpath('.//h1/text()')[0])
                        print  ("get news err : %s "  % e.message)

    def debug_news(self):
        url = "https://blockzone.com/2018/10/02/south-koreas-largest-venture-firm-backs-first-blockchain-startup/"
        response = requests.get(url)
        res_text = response.text
        entree_text = etree.HTML(res_text)
        self.construct_res(entree_text, 1)



    def construct_res(self, entree_text, page_index):
        print("now the page is %s: " %page_index)
        title_str = entree_text.xpath('.//h1/text()')[0]

        category_list = ['News', 'Insights', 'Companies', 'Events','Sponsored', 'Press Release']
        category_tag = entree_text.xpath('.//li[@class="meta-cat content-option-cat"]/a')
        category_and_region_str_list = entree_text.xpath('.//li[@class="meta-cat content-option-cat"]/a/text()')
        region_str = "Undefined"
        cate_str = ""
        for cate in category_and_region_str_list:
            if cate in category_list:
                cate_str = cate
                print ("cate str : %s" % cate_str)
            else:
                region_str = cate



        is_ad = 0
        pv = 0
        likes = 0

        #文章内容
        content_list = entree_text.xpath('.//div[@class="entry-content"]/p')
        content_str = "<content>"
        for cont in content_list:
            cont = html.tostring(cont).replace(', ','')
            content_str = content_str + cont
        #更多内容
        see_more_content_list = entree_text.xpath('.//div[@class="entry-content"]/p/em/a')
        if len(see_more_content_list) >= 1:
            see_more_str = html.tostring(see_more_content_list[0])
            content_str = content_str + see_more_str + "</content>"
        else:
            content_str = content_str + "</content>"

        #作者
        author_str = entree_text.xpath('.//a[contains(@class,"entry-byline-author content-option-author")]/text()')[0].strip()
        # author_str = html.tostring(author_str)
        status = 0

        #tag
        tag_list = entree_text.xpath('.//li[contains(@class,"meta-tag content-option-tag")]//a/text()')
        # tag_str = ""
        # for ele in tag_list:
        #     print ele


        #create_time
        months = [
            'January',
            'February',
            'March',
            'April',
            'May',
            'June',
            'July',
            'August',
            'September',
            'October',
            'November',
            'December'
        ]
        create_time = entree_text.xpath('.//span[@class="content-option-date"]/text()')[0].strip()
        time_format = datetime.datetime.strptime(create_time, '%B %d, %Y')
        create_time_stamp = time_format.strftime("%Y-%m-%d")


        # create_time_stamp = time.mktime(time_format.timetuple())
        # print create_time_stamp


        #update_time
        update_time = create_time_stamp

        # #本地
        # connection = pymysql.connect(host='localhost', user='root', password='', db='BlockZone',
        #                              charset='utf8',cursorclass  = pymysql.cursors.DictCursor)

        #服务器
        connection = pymysql.connect(host='167.99.238.182', user='blockzone_rw', password='Blockzone2018', db='blockzone',
                                     charset='utf8', cursorclass=pymysql.cursors.DictCursor)

        cursor = connection.cursor()

        #转化cate_id 和tag_str
        cate_id = self.transfer_catestr_to_id(connection, cursor, cate_str)
        # print ("saving cat_id: %s" % cate_id)
        tag_str = self.transfer_tagstr_to_id(connection, cursor, tag_list, "")
        print ("saving tag_str: %s" % tag_str)


        #下载图片
        img_src = entree_text.xpath('.//div[@class="featured-image"]/img/@src')[0]
        img_head_id = self.download_img(img_src)



        sql = "INSERT INTO posts ( title, category_id, is_ad, likes, pv, image_header_id, content, author, status, tag_ids, region, update_time, create_time) VALUES ( '%s', '%d', '%d', '%d', '%d', '%d', '%s', '%s', '%d', '%s', '%s', '%s', '%s' )"
        data = (title_str, cate_id, 0, 0, 0, img_head_id, content_str, author_str, 1, tag_str, region_str, update_time, create_time_stamp)
        # res_dic = {'title': title_str,
        #            'cat': cate_id,
        #            'content': content_str,
        #            'author': author_str,
        #            'tag_list': tag_str,
        #            'region': region_str,
        #            'update_time': update_time,
        #            'create_time': create_time_stamp }
        try:
            cursor.execute(sql % data)
            connection.commit()
        except Exception as e:
            print  ("data insert err : %s " % e.message)


        cursor.close()
        connection.close()






    def transfer_tagstr_to_id(self,connection,cursor, tag_list, tag_id_str):
        # print("the orginal tag_id_str is : %s"  % tag_id_str)
        for tag_ele in tag_list:
            sql = "SELECT id FROM tags WHERE name = '%s' "
            data = (tag_ele)
            cursor.execute(sql % data)
            result = cursor.fetchall()
            # print ("length of tag %s result: %d" % (tag_ele, len(result)))
            if len(result) == 0:
                sql_insert = "INSERT INTO tags (name) VALUES ('%s')"
                tmp_data = (tag_ele)
                cursor.execute((sql_insert % tmp_data))
                connection.commit()
                cursor.execute(sql % data)
                tmp_str = cursor.fetchall()[0].get('id')
                tag_id_str = tag_id_str + str(tmp_str) + ","
                # print ("tag_id_str is %s " % tag_id_str)
            else:
                # print type(result[0].get('id'))
                tag_id_str = tag_id_str + str(result[0].get('id')) + ","
            # print ("tag_str now equals to %s: " % tag_id_str)
        return tag_id_str[:len(tag_id_str) - 1]






    def transfer_catestr_to_id(self, connection, cursor, cate_str):
        # print("the original cate_str is : %s " %cate_str)
        sql = "SELECT id FROM categories WHERE name = '%s'"
        data = (cate_str)
        cursor.execute(sql % data)
        result = cursor.fetchall()
        # print ("length of cate %s result: %d" % (cate_str, len(result)))
        if len(result) == 0:
            sql_insert = "INSERT INTO categories (name) VALUES ('%s')"
            tmp_data = (cate_str,)
            try:
                cursor.execute((sql_insert % tmp_data))
                connection.commit()
            except Exception as e:
                print ("insert tag err: %s" % e.message)
            cursor.execute(sql % data)
            cate_id = cursor.fetchall()[0].get('id')
        else:
            cate_id = result[0].get('id')
        # print("finally cate_id is : %d" % cate_id)
        return cate_id


    def download_img(self, url):
        try:
            up_load_url = 'http://167.99.238.182:12580/api/v1/files/images'
            # up_load_url = 'http://192.168.0.41:5000/api/v1/files/images'
            file_obj = self.load_image(url)
            img_file = {"image": file_obj}
            file_id = self.transfer_url_to_id(url)
            file_name = str(file_id)+'.jpeg'
            print file_name
            files = {'image': (file_name, file_obj, 'image/jpeg')}

            data_result = requests.post(url= up_load_url, files=files)
            json_result = data_result.text.encode('utf-8')
            str_result = ast.literal_eval(json_result)
            print ("string_result is : %s" % str_result)
            # print type (dic_result)
            img_head_id = str_result['data']['id']
            print img_head_id
            if isinstance(file_obj, file):  # 这里load_image获得的是二进制流了，不是file对象。
                file_obj.close()
            return img_head_id
        except Exception as e:
            print ("download images failed")
            print ("message: %s "  %e.message )

    # APi for load image
    def load_image(self, url):
        try:
            # print type(url)
            url = url.encode('utf-8')
            url = quote(url,safe=string.printable)
            image_file = cStringIO.StringIO(urllib2.urlopen(url).read())
            image_data = Image.open(image_file)
            import io
            output = io.BytesIO()
            image_data.convert('RGB').save(output, format='JPEG')  # format=image_data.format
            image_data.close()
            data_bin = output.getvalue()
            output.close()
            return data_bin
        except Exception as e:
            print ("load image faild: %s"  % e.message)

    def transfer_url_to_id(self, url):
        identi_num = int(time.time())
        return identi_num


if __name__ == '__main__':
    bl_news = GetBlockZoneNews()
    bl_news.get_news()
    # bl_news.debug_news()
    # bl_news.get_links()
    # bl_news.download_img("https://i0.wp.com/blockzone.com/wp-content/uploads/2018/09/图片-1.png?w=899&ssl=1")

