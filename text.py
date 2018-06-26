# coding=utf-8
import codecs
import requests
import re
import pymysql

# 调用百度地api
def search_bd(keywords):
    #http://api.map.baidu.com/geocoder/v2/?address=北京市海淀区上地十街10号&output=json&ak=您的ak&callback=showLocation

    try:
        apiKey = '9Rcrs3WWnGeIjaGzlbAQHq3SM5I2h7do'
        url = 'http://api.map.baidu.com/geocoder/v2/?address=' + keywords + '&output=json&ak=' + apiKey + '&callback=showLocation'
        try:
            rep = requests.get(url)
        except:
            pass
    except:
        print ('search_bd error')
        pass
    return rep.text

if __name__ == '__main__':
    global conn, cur
    conn = pymysql.connect(host='api.mzz.pub', user='root', passwd='miaoxiaojie', db='city_lianjia_data', port=3306,
                           charset='utf8')
    cur = conn.cursor()
    cur.execute(
        "select * from data_detail where page_id = '107001763241'"
    )
    if cur.rowcount != 0:
        print('xxxx')
    conn.commit()  # 将数据写入数据库
    cur.close()  # 关闭游标
    conn.close()  # 释放数据库资源
