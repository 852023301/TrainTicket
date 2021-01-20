#!/usr/bin/env python
# coding: utf-8

# In[1]:


"""爬取指定起始地点中途全部换乘的12306的火车票信息"""
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
import json, base64
import requests,os
from bs4 import BeautifulSoup
import pickle
import urllib
import datetime
import pandas as pd
import time


# # 获取地址的英文简称

# In[2]:


if not os.path.exists(os.path.join(os.getcwd(),'station.pkl')):
    # 点击输入地址框
    browser.find_elements_by_id('fromStationText')[0].click()
    name_dict = {}
    name_list = []
    # 显示六列首字母对应的地址，其中第一列是热门站点，无“下一页”选项，因此从第二列开始遍历
    index_list = ['17','21','21','24','21']  #每一列中的“下一页”的css属性有不同的部分
    # 遍历首字母列
    for name_j in range(1,len(browser.find_elements_by_xpath("//ul[@id='abc']//li"))):
        browser.find_elements_by_xpath("//ul[@id='abc']//li")[name_j].click() # 点击首字母列
        next_i = 1 #"下一页"的索引
        while True:
            if browser.find_elements_by_id('ul_list'+str(name_j+1)):
                #获取当前页的html代码
                result = browser.find_elements_by_id('ul_list'+str(name_j+1))[0].get_attribute('innerHTML')
                soup = BeautifulSoup(result,'lxml')
                result_list = soup.find_all('li',class_="ac_even openLi")  # 每个li都是一个地名以及相应的英文简写  
                name_list.extend(result_list)
            #点击“下一页”
            if browser.find_elements_by_css_selector('[onclick="$.stationFor12306.pageDesigh('+index_list[name_j-1]+','+str(next_i)+','+str(name_j+1)+')"]'):
                browser.find_elements_by_css_selector('[onclick="$.stationFor12306.pageDesigh('+index_list[name_j-1]+','+str(next_i)+','+str(name_j+1)+')"]')[0].click()
                next_i = next_i + 1 
            else:
                break    
    #从li中取出地名以及英文名            
    for i in name_list:
        if i.get('data'):
            name_dict[i.text] = i.get('data')                
   #存入pickle中         
    with open(os.path.join(os.getcwd(),'station.pkl'),'wb') as f:
        pickle.dump(name_dict,f)            
else:
    with open('station.pkl','rb') as f:
        name_dict = pickle.load(f)   


# In[3]:


#反转地址
name_dict_converse = dict(zip(name_dict.values(), name_dict.keys()))


# #### 获取第一层车票

# In[17]:


def query_ticket(fromStation,toStation,date):
    #https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=2020-12-18\
    #&leftTicketDTO.from_station=BJP&leftTicketDTO.to_station=TJP&purpose_codes=ADULT
    url = "https://kyfw.12306.cn/otn/leftTicket/queryT?leftTicketDTO.train_date={date}&leftTicketDTO.from_station={fromStation}&leftTicketDTO.to_station={toStation}&purpose_codes=ADULT".format(fromStation=name_dict[fromStation],
                                                                                            toStation=name_dict[toStation],
                                                                                            date=date)
    return url


# In[18]:


fromStation = '深圳'
toStation = '南宁'
date = '2021-02-09'
# time_limit = ['08:00','10:00']  #发车时间限制
time_limit = None
origin_url = query_ticket(fromStation,toStation,date)


# In[19]:


origin_url


# #### 获取cookie

# In[27]:


#无头浏览器
options = webdriver.ChromeOptions()
# options.add_argument("--headless")
# options.add_argument("--disable-gpu")
browser = webdriver.Chrome(options=options)
browser.get('https://kyfw.12306.cn/otn/leftTicket/init')
time.sleep(2)
req = requests.Session()
cookies = browser.get_cookies()
for cookie in cookies:
        print(cookie)
        req.cookies.set(cookie['name'],cookie['value'])  


# In[31]:


browser.close()


# In[22]:


req.cookies.keys()


# #### 处理中间站

# In[35]:


def mid_station_check():
    try:
        global tostation_list
        global train_no_list
        tostation_list_uni = list(set(tostation_list))
        train_no_list_uni = list(set(train_no_list))
        #中间站名
        global url_midstation_list
        midstation_list = []
        for url in url_midstation_list:
            for i in req.get(url).json().get('data',{}).get('data',[None]):
                if i.get('isEnabled') == True:  #只用出发站之后的中间站
                    midstation_list.append(i.get('station_name'))  
        midstation_list = list(set(midstation_list))
        if fromStation in midstation_list:
            midstation_list.remove(fromStation)  #删除出发站

        #车票基本信息
        mid_train_no_all_list = []
        mid_train_no_list = []
        mid_fromstation_list = []
        mid_tostation_list = []
        mid_starttime_list = []
        mid_endtime_list = []
        mid_duringtime_list = []
        mid_super_soft_sleeper_count = []
        mid_soft_sleeper_count = []
        mid_soft_seat_count = []
        mid_no_seat_count = []
        mid_hard_sleeper_count = []
        mid_hard_seat_count = []
        mid_second_seat_count = []
        mid_first_seat_count = []
        mid_business_seat_count = []
        mid_high_speed_sleeper_count = []   

        #遍历中间站
        global date
        for midstn in midstation_list[:]:
            url = query_ticket(fromStation,midstn,date)
            #遍历每一趟车
        #     print(url)
            result = req.get(url).json()

            time.sleep(1)
            for i in result['data']['result']:
                data = i.split('|')
                train_no_all = data[2] #完整车号
                train_no = data[3] #车号
                startstation = data[4]    #始发站
                endstation = data[5]    #终点站
                fromstation = data[6]    #起点
                tostation = data[7]    #终点
                starttime = data[8]  #出发时间
                endtime = data[9]  #到达时间
                duringtime = data[10]  #历时
                isbuyable = data[11]  #能否预定   
                date = data[13][:4]+'-'+data[13][4:6]+'-'+data[13][6:]  #日期 

                if isbuyable == 'Y' and (train_no in train_no_list_uni) and (name_dict_converse[tostation] not in tostation_list_uni):
                    #去重
                    if (train_no,name_dict_converse[fromstation],name_dict_converse[tostation]) in list(zip(mid_train_no_list,mid_fromstation_list,mid_tostation_list)):
                        continue
                    mid_train_no_all_list.append(train_no_all)
                    mid_train_no_list.append(train_no)
                    mid_fromstation_list.append(name_dict_converse[fromstation])
                    mid_tostation_list.append(name_dict_converse[tostation])
                    mid_starttime_list.append(starttime)
                    mid_endtime_list.append(endtime)
                    mid_duringtime_list.append(duringtime)

                    mid_super_soft_sleeper_count.append(data[21] if data[21].isdigit() or data[21] == '有' else None)
                    mid_soft_sleeper_count.append(data[23] if data[23].isdigit() or data[23] == '有' else None)
                    mid_soft_seat_count.append(data[24] if data[24].isdigit() or data[24] == '有' else None)
                    mid_no_seat_count.append(data[26] if data[26].isdigit() or data[26] == '有' else None)
                    mid_hard_sleeper_count.append(data[28] if data[28].isdigit() or data[28] == '有' else None)
                    mid_hard_seat_count.append(data[29] if data[29].isdigit() or data[29] == '有' else None)
                    mid_second_seat_count.append(data[30] if data[30].isdigit() or data[30] == '有' else None)
                    mid_first_seat_count.append(data[31] if data[31].isdigit() or data[31] == '有' else None)
                    mid_business_seat_count.append(data[32] if data[32].isdigit() or data[32] == '有' else None)
                    mid_high_speed_sleeper_count.append(data[33] if data[33].isdigit() or data[33] == '有' else None)        
    except Exception as e:
        print(e)
        print('查询速度过快')
    finally:    
        #生成df
        result_df_mid = pd.DataFrame([mid_train_no_all_list,mid_train_no_list,
                      mid_fromstation_list,mid_tostation_list,mid_starttime_list,
                      mid_endtime_list,mid_duringtime_list,
                     mid_super_soft_sleeper_count,mid_soft_sleeper_count,mid_soft_seat_count,mid_no_seat_count,
                     mid_hard_sleeper_count,mid_hard_seat_count,mid_second_seat_count,mid_first_seat_count,
                      mid_business_seat_count,mid_high_speed_sleeper_count],
                     index=['车号','车次','出发','到达','出发时间','到达时间',
                           '时长','高级软卧','软卧','软座','无座','硬卧','硬座','二等','一等','商务','动卧']).T  
        if not result_df_mid.empty:
            result_df_mid = result_df_mid.sort_values('出发时间').reset_index(drop = True)
            if time_limit:
                result_df_mid = result_df_mid[(result_df_mid['出发时间']>=time_limit[0])&(result_df_mid['出发时间']<=time_limit[1])]
            #删除全空列
            for col in result_df_mid.columns:
                if result_df_mid[col].count() == 0:
                    result_df_mid.drop(labels=col, axis=1, inplace=True)
            #置换空值       
            result_df_mid = result_df_mid.where(pd.notnull(result_df_mid),'')        
            display(result_df_mid)  
            return result_df_mid
        else:
            print('中间站结果为空')
            return None


# #### check!

# In[36]:


# def time_judge(time,flag=0):
#     if flag:  #test
#         return True
#     if time >= time_limit[0] and time <= time_limit[1]:
#         return True
#     else:
#         return False
try:
    train_no_all_list = []
    train_no_list = []
    fromstation_list = []
    tostation_list = []
    starttime_list = []
    endtime_list = []
    duringtime_list = []
    super_soft_sleeper_count = []
    soft_sleeper_count = []
    soft_seat_count = []
    no_seat_count = []
    hard_sleeper_count = []
    hard_seat_count = []
    second_seat_count = []
    first_seat_count = []
    business_seat_count = []
    high_speed_sleeper_count = []

    #中间站链接
    url_midstation_list = []

    #遍历每一趟车
    result = req.get(origin_url).json()
    
    for i in result['data']['result']:
        data = i.split('|')
        train_no_all = data[2] #完整车号
        train_no = data[3] #车号
        startstation = data[4]    #始发站
        endstation = data[5]    #终点站
        fromstation = data[6]    #起点
        tostation = data[7]    #终点
        starttime = data[8]  #出发时间
        endtime = data[9]  #到达时间
        duringtime = data[10]  #历时
        isbuyable = data[11]  #能否预定   
        date = data[13][:4]+'-'+data[13][4:6]+'-'+data[13][6:]  #日期 
    #     ticket_dict = {    
    #         '高级软卧' : data[21] if data[21].isdigit() or data[21] == '有' else None,  #高级软卧
    #         '软卧' : data[23] if data[23].isdigit() or data[23] == '有' else None,  #软卧
    #         '软座' : data[24] if data[24].isdigit() or data[24] == '有' else None,  #软座
    #         '无座' : data[26] if data[26].isdigit() or data[26] == '有' else None,  #无座
    #         '硬卧' : data[28] if data[28].isdigit() or data[28] == '有' else None ,  #硬卧   
    #         '硬座' : data[29] if data[29].isdigit() or data[29] == '有' else None ,  #硬座
    #         '二等' : data[30] if data[30].isdigit() or data[30] == '有' else None , #二等座
    #         '一等' : data[31] if data[31].isdigit() or data[31] == '有' else None,  #一等座
    #         '商务' : data[32] if data[32].isdigit() or data[32] == '有' else None,  #商务特等座
    #         '动卧' : data[33] if data[33].isdigit() or data[33] == '有' else None,  #动卧 
    #     }   
        #若可购买
        # flag为0是测试模式
    #     if isbuyable == 'Y' and time_judge(starttime,flag=1):
    #         print(train_no_all,train_no.ljust(6,' '),
    #               name_dict_converse[fromstation]+'-->'+name_dict_converse[tostation],
    #               starttime.ljust(5,' ')+'-->'+endtime,'('+duringtime+')',end='\t',sep='\t')
    #         for v in ticket_dict.values():
    #             if v:
    #                 print(v,end='\t')
    #         print()
    #         url_part = 'https://kyfw.12306.cn/otn/czxx/queryByTrainNo?train_no={train_no_all}&from_station_telecode={fromstation}&to_station_telecode={tostation}&depart_date={date}'.format(train_no_all=train_no_all,
    # fromstation=fromstation,tostation=tostation,date=date

    # )
    #         print(req.get(url_part).json())
        if isbuyable == 'Y':
            train_no_all_list.append(train_no_all)
            train_no_list.append(train_no)
            fromstation_list.append(name_dict_converse[fromstation])
            tostation_list.append(name_dict_converse[tostation])
            starttime_list.append(starttime)
            endtime_list.append(endtime)
            duringtime_list.append(duringtime)

            super_soft_sleeper_count.append(data[21] if data[21].isdigit() or data[21] == '有' else None)
            soft_sleeper_count.append(data[23] if data[23].isdigit() or data[23] == '有' else None)
            soft_seat_count.append(data[24] if data[24].isdigit() or data[24] == '有' else None)
            no_seat_count.append(data[26] if data[26].isdigit() or data[26] == '有' else None)
            hard_sleeper_count.append(data[28] if data[28].isdigit() or data[28] == '有' else None)
            hard_seat_count.append(data[29] if data[29].isdigit() or data[29] == '有' else None)
            second_seat_count.append(data[30] if data[30].isdigit() or data[30] == '有' else None)
            first_seat_count.append(data[31] if data[31].isdigit() or data[31] == '有' else None)
            business_seat_count.append(data[32] if data[32].isdigit() or data[32] == '有' else None)
            high_speed_sleeper_count.append(data[33] if data[33].isdigit() or data[33] == '有' else None)        

        url_part = 'https://kyfw.12306.cn/otn/czxx/queryByTrainNo?train_no={train_no_all}&from_station_telecode={fromstation}&to_station_telecode={tostation}&depart_date={date}'.format(train_no_all=train_no_all,
fromstation=fromstation,tostation=tostation,date=date)
        url_midstation_list.append(url_part)


except Exception as e:
    print(e)
    print('查询速度过快')
finally:
    
    #生成df
    result_df = pd.DataFrame([train_no_all_list,train_no_list,
                  fromstation_list,tostation_list,starttime_list,
                  endtime_list,duringtime_list,
                 super_soft_sleeper_count,soft_sleeper_count,soft_seat_count,no_seat_count,
                 hard_sleeper_count,hard_seat_count,second_seat_count,first_seat_count,
                  business_seat_count,high_speed_sleeper_count],
                 index=['车号','车次','出发','到达','出发时间','到达时间',
                       '时长','高级软卧','软卧','软座','无座','硬卧','硬座','二等','一等','商务','动卧']).T      
    if not result_df.empty:
        #删除全空列
        for col in result_df.columns:
            if result_df[col].count() == 0:
                result_df.drop(labels=col, axis=1, inplace=True)
        if len(result_df.columns) >7:
            #置换空值       
            result_df = result_df.where(pd.notnull(result_df),'')
            result_df = result_df.sort_values('出发时间')
            if time_limit:
                result_df = result_df[(result_df['出发时间']>=time_limit[0])&(result_df['出发时间']<=time_limit[1])]
            display(result_df)
        else:
            mid_station_check()
    else:
        mid_station_check()


# #### 第一层

# In[ ]:


result_df


# #### 第二层（中间站先上车后补票）

# In[32]:


mid_result = mid_station_check()


# In[ ]:


# super_soft_sleeper_count = data[21]  #高级软卧
# soft_sleeper_count = data[23]  #软卧一等座
# soft_seat_count = data[24]  #软座
# no_seat_count = data[26]  #无座
# hard_sleeper_count = data[28]  #硬卧   
# hard_seat_count = data[29]  #硬座
# second_seat_count = data[30]  #二等座
# first_seat_count = data[31]  #一等座
# business_seat_count = data[32]  #商务特等座
# high_speed_sleeper_count = data[33]  #动卧


# In[ ]:




