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
import numpy
import xlwt
import json
from lxml import etree
from lxml import html
import os


connection = pymysql.connect(host='167.99.238.182', user='blockzone_rw', password='Blockzone2018', db='blockzone',
                             charset='utf8', cursorclass=pymysql.cursors.DictCursor)

# #本地
# connection = pymysql.connect(host='localhost', user='root', password='', db='BlockZone',
#                              charset='utf8',cursorclass  = pymysql.cursors.DictCursor)

cursor = connection.cursor()


sql = "SELECT id, tag_ids FROM posts"
# sql = "INSERT INTO post_with_tag ( tag_id, post_id)" \
#               " VALUES ( '%s', '%d', '%d', '%d', '%d', '%d', '%s', '%s', '%d', '%s', '%s', '%s', '%s' )"
#         data = (title_str, cate_id, 0, 0, 0, img_head_id, content_str, author_str, 1, tag_str, region_str, update_time, create_time_stamp)

try:
    cursor.execute(sql)
    result = cursor.fetchall()
    for res in result:
        print res
        id = res.get('id')  
        tags = res.get('tag_ids').encode("utf-8")
        tag_list = tags.split(",")
        for ele in tag_list:
            if ele == "":
                continue
            sql1 = "INSERT INTO post_with_tag ( tag_id, post_id)" \
                  " VALUES ( '%d', '%d')"
            data = (int(ele), id)
            cursor.execute(sql1 % data)
            connection.commit()
except Exception as e:
    print e.message


cursor.close()
connection.close()