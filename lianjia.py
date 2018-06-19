# _*_coding:utf-8_*_
# 网站反爬虫：一个IP频繁访问就先将该IP加入黑名单
# 反爬虫策略：限制IP访问频率，超过频率就自动断开：降低爬虫的速度，在每个请求前加time.sleep,或更换IP
# 策略二：后台对访问进行统计，如果单个userAgent访问超过阈值，予以封锁：误伤较大，一般网站不使用
# 策略三：针对cookies：一般网站不使用

# 设置延时时间防止取速度过快

import time
import re
import random
import datetime
# coding:utf8
import requests
from bs4 import BeautifulSoup
import pymysql

def getCurrentTime():
    return time.strftime('[%Y-%m-%d %H:%M:%S]', time.localtime(time.time()))


def getURL(url, tries_num=10, sleep_time=0, time_out=10):
    headers = {'content-type': 'text/html;charset=UTF-8',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'}
    # proxies = {"http": "120.77.201.46:8080"}
    sleep_time_p = sleep_time
    time_out_p = time_out
    tries_num_p = tries_num
    try:
        res = requests.Session()
        res = requests.get(url, headers=headers, timeout=time_out)
        # if isproxy == 1:
        #     res = requests.get(url, headers=headers, timeout=time_out)
        # else:
        #     res = requests.get(url, headers=headers, timeout=time_out, proxies=proxies)
        res.raise_for_status()  # 如果响应状态码不是 200，就主动抛出异常
    except requests.RequestException as e:
        sleep_time_p = sleep_time_p + 10
        time_out_p = time_out_p + 10
        tries_num_p = tries_num_p - 1
        # 设置重试次数，最大timeout 时间和 最长休眠时间
        # print tries_num_p
        if tries_num_p > 0:
            time.sleep(sleep_time_p)
            print(getCurrentTime(), url, 'URL Connection Error: 第', max_retry - tries_num_p, u'次 Retry Connection', e)
            res = getURL(url, tries_num_p, sleep_time_p, time_out_p)
            if res.status_code == 200:
                print(
                    getCurrentTime(), url, 'URL Connection Success: 共尝试', max_retry - tries_num_p, u'次', ',sleep_time:',
                    sleep_time_p, ',time_out:', time_out_p)
            else:
                print(getCurrentTime(), url, 'URL Connection Error: 共尝试', max_retry - tries_num_p, u'次', ',sleep_time:',
                      sleep_time_p, ',time_out:', time_out_p)
        pass
    return res



def get_s_reion(url):
    '''
    取该城市区域列表
    :param list: 链接list
    :return:
    '''
    try:
        list = []
        html = requests.get(url + '/ershoufang').text
        soup = BeautifulSoup(html, 'html.parser')
        reions = soup.select('div.position')[0].select('div')[0].select('a')
        # reions = soup.select('div.m-filter')[0].select('div[data-role="ershoufang"]')[0].select('a')[1:]
        for reion in reions:
            city = reion.text
            city_href = url + reion.get('href')
            list.append(city_href)
        return list
    except:
        pass

def get_url_s(url, html_city):
    '''
    取二级区域列表（镇、乡）
    :param url:
    :param html_city:
    :return: 链接list
    '''
    try:
        gethtml = []
        get1 = []
        html = requests.get(html_city)
        respons = html.content
        soup = BeautifulSoup(respons, 'html.parser')
        d = soup.select('div.m-filter')[0].select('div[data-role="ershoufang"]')[0].select('div')[1].select('a')
        for d2 in d:
            diqu = d2.text
            href = d2.get('href')
            get1.append(str(href))
        for i in range(0, len(get1)):
            html = url + get1[i]
            gethtml.append(html)
        return gethtml
    except:
        pass

def Get_url_s(url):
    '''
    取某二级区域页面的房子页数及每页链接
    :param url:
    :return: 各页码链接list
    '''
    list = []
    html = getURL(url)
    respons = html.content
    try:
        try:
            soup = BeautifulSoup(respons, 'html.parser')
            num = int(soup.select('h2[class="total fl"]')[0].select('span')[0].text.strip())
        except:
            pass
        alist = int(num / 30 + (1 if num % 30 != 0 else 0))
        for i in range(1, alist + 1):
            list.append('%spg%s' % (url, i))
        return list
    except:
        pass

def Get_Date(url):
    html = getURL(url).content
    soup = BeautifulSoup(html, 'html.parser')
    list = []
    try:
        citys = soup.select('#areaTab')[0].get('title')
        try:
            infos = soup.select('ul.sellListContent')[0].select('li')
        except:
            pass
        for info in infos:
            data = {}
            # pageId
            Url = info.select('div.title')[0].select('a')[0].get('href')
            pageId = re.findall(r"\d+",str(Url))[0]
            data['pageId'] = pageId
            data_url = getURL(Url).content
            soup1 = BeautifulSoup(data_url,'html.parser')

            # City
            City = citys.replace('二手房', '')
            data['City'] = City

            # Area
            Area = soup.select('div[data-role="ershoufang"]')[0].select('a.selected')[0].text
            data['Area'] = Area

            # SecArea
            SecArea = info.select('div.flood')[0].select('div')[0].select('a')[0].text
            data['SecArea'] = SecArea

            # Title
            Title = info.select('div.title')[0].select('a')[0].text.strip()
            data['Title'] = Title

            # CommunityName HouseType Square Toward Decoration Lift
            dd = info.select('div.address')[0].select('div')[0]
            features = dd.text.split(' | ')
            CommunityName = features[0].strip()
            data['CommunityName'] = CommunityName
            for feature in features:  # 4小区名、5几室几厅、6面积平米、7朝向、8装修情况、9有无电梯
                try:
                    if (feature.find("室") != -1):
                        HouseType = feature.strip()
                        data['HouseType'] = HouseType
                        continue
                    if (feature.find("平米") != -1):
                        Square = float(feature[:-2])
                        data['Square'] = Square
                        continue
                    if(feature=='南' or feature=='北'):
                        Toward = feature.strip()
                        data['Toward'] = Toward
                        continue
                    if (feature == '精装' or feature == '简装' or feature == '毛坯' or feature == '其他'):
                        Decoration = feature.strip()
                        data['Decoration'] = Decoration
                        continue
                    if (feature.find("电梯") != -1):
                        Lift = feature.strip()
                        data['Lift'] = Lift
                        continue
                except:
                    pass

            # Flood
            Flood = info.select('div.flood')[0].select('div')[0].text
            data['Flood'] = Flood

            # TotalPace UnitPrice
            totalPrice = info.select('div.priceInfo')[0].select('div')
            TotalPace = int(totalPrice[0].select('span')[0].text.strip())
            UnitPrice = int(totalPrice[1].select('span')[0].text.replace('单价', '').replace('元/平米', '').strip())
            data['TotalPace'] = TotalPace
            data['UnitPrice'] = UnitPrice

            # Image
            Image = info.select('img.lj-lazy')[0].get('data-original')
            data['Image']= Image

            # Star Visit PublishTime
            Fows = info.select('div.followInfo')[0].text.split(' / ')
            Star = int(re.findall(r"\d+", str(Fows[0]))[0])
            Visit = int(re.findall(r"\d+", str(Fows[1]))[0])
            data['Star'] = Star
            data['Visit'] = Visit
            times = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
            try:
                con = int(re.findall(r"\d+", Fows[2])[0])
                num = int(times[4:6])
                num1 = int(times[6:])
                if num > con:
                    timecount = int(times) - con * 100000000
                    PublishTime = datetime.datetime.strptime(str(timecount), "%Y%m%d%H%M%S")
                    data['PublishTime'] = PublishTime
                else:
                    timecount = 20171200000000 + num1 - con * 100000000
                    PublishTime = datetime.datetime.strptime(str(timecount), "%Y%m%d%H%M%S")
                    data['PublishTime'] = PublishTime
            except:
                timecount = '20170506023037'
                PublishTime = datetime.datetime.strptime(str(timecount), "%Y%m%d%H%M%S")
                data['PublishTime'] = PublishTime

            info_data1 = soup1.select('div.introContent')[0].select('li')
            info_data2 = soup1.select('div.transaction')[0].select('li')
            info_data3 = soup1.select('div.content')[1]
            info_data4 = soup1.select('div.thumbnail')[0].select('li')


            # BuildingType
            BuildingType = info_data1[5].text.replace('建筑类型', '')
            data['BuildingType'] = BuildingType

            # Ownership
            Ownership = info_data2[1].text.replace('交易权属', '').strip()
            data['Ownership'] = Ownership

            # DownPaymentBudget
            DownPaymentBudget = info_data3.select('div.tax')[0].text.replace('详情', '')
            data['DownPaymentBudget'] = DownPaymentBudget

            # HouseUse
            HouseUse = info_data2[3].text.replace('房屋用途', '').strip()
            data['HouseUse'] = HouseUse

            # CompletionDate
            CompletionDate = int(re.findall(r"\d+", str(info_data3.select('div.subInfo')[2].text))[0])
            data['CompletionDate'] = CompletionDate

            # Floor
            Floor = info_data3.select('div.subInfo')[0].text
            data['Floor'] = Floor

            # Visit7
            Visit7 = random.randint(0,10)
            data['Visit7'] = Visit7

            # Visit30
            Visit30 = random.randint(10,30)
            data['Visit30'] = Visit30

            # CarouselImages
            CarouselImages= []
            for info_data in info_data4:
                CarouselImages.append(info_data.get('data-src'))
            images = ",".join(CarouselImages)
            data['CarouselImages'] = images

            try:
                Time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                global conn, cur
                # 获取一个数据库连接，注意如果是UTF-8类型的，需要制定数据库
                conn = pymysql.connect(host='api.mzz.pub', user='root', passwd='miaoxiaojie', db='city_lianjia_data',port=3306, charset='utf8')
                cur = conn.cursor()
                cur.execute(
                    "insert into data_detail (created_at,updated_at,page_id, city, area, sec_area, title, community_name,house_type,square,toward,decoration,lift,flood,total_price,unit_price,image, star, visit,publish_time,building_type,ownership,down_payment_budget,house_use,completion_date,floor,visit7,visit30,carousel_images) " +
                    "VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s',%d,'%s','%s','%s','%s',%d,%d,'%s',%d,%d,'%s','%s','%s','%s','%s',%d,'%s',%d,%d,'%s');"
                    % (Time,Time,pageId, City, Area, SecArea, Title,CommunityName,HouseType,Square,Toward,Decoration,Lift,Flood, TotalPace, UnitPrice,Image, Star, Visit,PublishTime,BuildingType,Ownership,DownPaymentBudget,HouseUse,CompletionDate,Floor,Visit7,Visit30,images)
                )
                cur.execute(
                    "insert into data_list (created_at,updated_at,page_id, city, area, sec_area, title, community_name,house_type,square,toward,decoration,lift,flood,total_price,unit_price,image, star, visit,publish_time) " +
                    "VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s',%d,'%s','%s','%s','%s',%d,%d,'%s',%d,%d,'%s');"
                    % (Time, Time, pageId, City, Area, SecArea, Title, CommunityName, HouseType, Square, Toward,Decoration, Lift, Flood, TotalPace, UnitPrice, Image, Star, Visit, PublishTime)
                )
                conn.commit()  # 将数据写入数据库
                cur.close()  # 关闭游标
                conn.close()  # 释放数据库资源
            except Exception :
                print("写入数据库异常")
            print(data)

    except:
        pass


if __name__ == '__main__':
    url = "https://sh.lianjia.com"
    global max_retry
    max_retry = 5
    lists = get_s_reion(url)
    if lists is not None:
        for list in lists[17:]:
            htmls = get_url_s(url, list)
            if htmls is not None and len(htmls) != 0:
                for html in htmls:
                    page_list = Get_url_s(html)
                    for url in page_list[0:3]:
                        Get_Date(url)