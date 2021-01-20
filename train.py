{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "metadata": {},
   "outputs": [],
   "source": [
    "\"\"\"爬取指定起始地点中途全部换乘的12306的火车票信息\"\"\"\n",
    "from selenium.webdriver.common.keys import Keys\n",
    "from selenium import webdriver\n",
    "import json, base64\n",
    "import requests,os\n",
    "from bs4 import BeautifulSoup\n",
    "import pickle\n",
    "import urllib\n",
    "import datetime\n",
    "import pandas as pd\n",
    "import time"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# 获取地址的英文简称"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "metadata": {},
   "outputs": [],
   "source": [
    "if not os.path.exists(os.path.join(os.getcwd(),'station.pkl')):\n",
    "    # 点击输入地址框\n",
    "    browser.find_elements_by_id('fromStationText')[0].click()\n",
    "    name_dict = {}\n",
    "    name_list = []\n",
    "    # 显示六列首字母对应的地址，其中第一列是热门站点，无“下一页”选项，因此从第二列开始遍历\n",
    "    index_list = ['17','21','21','24','21']  #每一列中的“下一页”的css属性有不同的部分\n",
    "    # 遍历首字母列\n",
    "    for name_j in range(1,len(browser.find_elements_by_xpath(\"//ul[@id='abc']//li\"))):\n",
    "        browser.find_elements_by_xpath(\"//ul[@id='abc']//li\")[name_j].click() # 点击首字母列\n",
    "        next_i = 1 #\"下一页\"的索引\n",
    "        while True:\n",
    "            if browser.find_elements_by_id('ul_list'+str(name_j+1)):\n",
    "                #获取当前页的html代码\n",
    "                result = browser.find_elements_by_id('ul_list'+str(name_j+1))[0].get_attribute('innerHTML')\n",
    "                soup = BeautifulSoup(result,'lxml')\n",
    "                result_list = soup.find_all('li',class_=\"ac_even openLi\")  # 每个li都是一个地名以及相应的英文简写  \n",
    "                name_list.extend(result_list)\n",
    "            #点击“下一页”\n",
    "            if browser.find_elements_by_css_selector('[onclick=\"$.stationFor12306.pageDesigh('+index_list[name_j-1]+','+str(next_i)+','+str(name_j+1)+')\"]'):\n",
    "                browser.find_elements_by_css_selector('[onclick=\"$.stationFor12306.pageDesigh('+index_list[name_j-1]+','+str(next_i)+','+str(name_j+1)+')\"]')[0].click()\n",
    "                next_i = next_i + 1 \n",
    "            else:\n",
    "                break    \n",
    "    #从li中取出地名以及英文名            \n",
    "    for i in name_list:\n",
    "        if i.get('data'):\n",
    "            name_dict[i.text] = i.get('data')                \n",
    "   #存入pickle中         \n",
    "    with open(os.path.join(os.getcwd(),'station.pkl'),'wb') as f:\n",
    "        pickle.dump(name_dict,f)            \n",
    "else:\n",
    "    with open('station.pkl','rb') as f:\n",
    "        name_dict = pickle.load(f)   \n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### 获取第一层车票"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "metadata": {},
   "outputs": [],
   "source": [
    "#反转地址\n",
    "name_dict_converse = dict(zip(name_dict.values(), name_dict.keys()))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 17,
   "metadata": {},
   "outputs": [],
   "source": [
    "def query_ticket(fromStation,toStation,date):\n",
    "    #https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=2020-12-18\\\n",
    "    #&leftTicketDTO.from_station=BJP&leftTicketDTO.to_station=TJP&purpose_codes=ADULT\n",
    "    url = \"https://kyfw.12306.cn/otn/leftTicket/queryT?leftTicketDTO.train_date={date}&leftTicketDTO.from_station={fromStation}&leftTicketDTO.to_station={toStation}&purpose_codes=ADULT\".format(fromStation=name_dict[fromStation],\n",
    "                                                                                            toStation=name_dict[toStation],\n",
    "                                                                                            date=date)\n",
    "    return url"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 18,
   "metadata": {},
   "outputs": [],
   "source": [
    "fromStation = '深圳'\n",
    "toStation = '南宁'\n",
    "date = '2021-02-09'\n",
    "# time_limit = ['08:00','10:00']  #发车时间限制\n",
    "time_limit = None\n",
    "origin_url = query_ticket(fromStation,toStation,date)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### 获取cookie"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 27,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "{'domain': '.12306.cn', 'expiry': 1924905600, 'httpOnly': False, 'name': 'RAIL_DEVICEID', 'path': '/', 'secure': False, 'value': 'a31Ui0PjWBTI2OZ40dFibouGoZCk81rkF16OVLyq9zB6EU4lMaJZrAjj1GJiXSTe_WmqByi9miypxhIyxeKl_eJfYunLV4lx4WhJffqgnkGJeTAeZDPoogWqTTprDjXVwLoerO8vfmouTH3QyJHPVfuxHOh59Vli'}\n",
      "{'domain': 'kyfw.12306.cn', 'httpOnly': False, 'name': 'route', 'path': '/', 'secure': False, 'value': '6f50b51faa11b987e576cdb301e545c4'}\n",
      "{'domain': '.12306.cn', 'expiry': 1696769273, 'httpOnly': False, 'name': 'RAIL_EXPIRATION', 'path': '/', 'secure': False, 'value': '1610696495434'}\n",
      "{'domain': 'kyfw.12306.cn', 'httpOnly': False, 'name': 'BIGipServerotn', 'path': '/', 'secure': False, 'value': '4023845130.64545.0000'}\n",
      "{'domain': 'kyfw.12306.cn', 'httpOnly': False, 'name': 'JSESSIONID', 'path': '/otn', 'secure': False, 'value': '7E60B546470C1E3857824518E5192DC2'}\n",
      "{'domain': 'kyfw.12306.cn', 'expiry': 1925729272, 'httpOnly': False, 'name': '_uab_collina', 'path': '/otn/leftTicket', 'secure': False, 'value': '161036927276478306787637'}\n"
     ]
    }
   ],
   "source": [
    "#无头浏览器\n",
    "options = webdriver.ChromeOptions()\n",
    "# options.add_argument(\"--headless\")\n",
    "# options.add_argument(\"--disable-gpu\")\n",
    "browser = webdriver.Chrome(options=options)\n",
    "browser.get('https://kyfw.12306.cn/otn/leftTicket/init')\n",
    "time.sleep(2)\n",
    "req = requests.Session()\n",
    "cookies = browser.get_cookies()\n",
    "for cookie in cookies:\n",
    "        print(cookie)\n",
    "        req.cookies.set(cookie['name'],cookie['value'])  "
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 31,
   "metadata": {},
   "outputs": [],
   "source": [
    "browser.close()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 22,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "['BIGipServerotn',\n",
       " 'JSESSIONID',\n",
       " 'RAIL_DEVICEID',\n",
       " 'RAIL_EXPIRATION',\n",
       " '_uab_collina',\n",
       " 'route']"
      ]
     },
     "execution_count": 22,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# req.cookies.keys()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### 处理中间站"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 35,
   "metadata": {},
   "outputs": [],
   "source": [
    "def mid_station_check():\n",
    "    try:\n",
    "        global tostation_list\n",
    "        global train_no_list\n",
    "        tostation_list_uni = list(set(tostation_list))\n",
    "        train_no_list_uni = list(set(train_no_list))\n",
    "        #中间站名\n",
    "        global url_midstation_list\n",
    "        midstation_list = []\n",
    "        for url in url_midstation_list:\n",
    "            for i in req.get(url).json().get('data',{}).get('data',[None]):\n",
    "                if i.get('isEnabled') == True:  #只用出发站之后的中间站\n",
    "                    midstation_list.append(i.get('station_name'))  \n",
    "        midstation_list = list(set(midstation_list))\n",
    "        if fromStation in midstation_list:\n",
    "            midstation_list.remove(fromStation)  #删除出发站\n",
    "\n",
    "        #车票基本信息\n",
    "        mid_train_no_all_list = []\n",
    "        mid_train_no_list = []\n",
    "        mid_fromstation_list = []\n",
    "        mid_tostation_list = []\n",
    "        mid_starttime_list = []\n",
    "        mid_endtime_list = []\n",
    "        mid_duringtime_list = []\n",
    "        mid_super_soft_sleeper_count = []\n",
    "        mid_soft_sleeper_count = []\n",
    "        mid_soft_seat_count = []\n",
    "        mid_no_seat_count = []\n",
    "        mid_hard_sleeper_count = []\n",
    "        mid_hard_seat_count = []\n",
    "        mid_second_seat_count = []\n",
    "        mid_first_seat_count = []\n",
    "        mid_business_seat_count = []\n",
    "        mid_high_speed_sleeper_count = []   \n",
    "\n",
    "        #遍历中间站\n",
    "        global date\n",
    "        for midstn in midstation_list[:]:\n",
    "            url = query_ticket(fromStation,midstn,date)\n",
    "            #遍历每一趟车\n",
    "        #     print(url)\n",
    "            result = req.get(url).json()\n",
    "\n",
    "            time.sleep(1)\n",
    "            for i in result['data']['result']:\n",
    "                data = i.split('|')\n",
    "                train_no_all = data[2] #完整车号\n",
    "                train_no = data[3] #车号\n",
    "                startstation = data[4]    #始发站\n",
    "                endstation = data[5]    #终点站\n",
    "                fromstation = data[6]    #起点\n",
    "                tostation = data[7]    #终点\n",
    "                starttime = data[8]  #出发时间\n",
    "                endtime = data[9]  #到达时间\n",
    "                duringtime = data[10]  #历时\n",
    "                isbuyable = data[11]  #能否预定   \n",
    "                date = data[13][:4]+'-'+data[13][4:6]+'-'+data[13][6:]  #日期 \n",
    "\n",
    "                if isbuyable == 'Y' and (train_no in train_no_list_uni) and (name_dict_converse[tostation] not in tostation_list_uni):\n",
    "                    #去重\n",
    "                    if (train_no,name_dict_converse[fromstation],name_dict_converse[tostation]) in list(zip(mid_train_no_list,mid_fromstation_list,mid_tostation_list)):\n",
    "                        continue\n",
    "                    mid_train_no_all_list.append(train_no_all)\n",
    "                    mid_train_no_list.append(train_no)\n",
    "                    mid_fromstation_list.append(name_dict_converse[fromstation])\n",
    "                    mid_tostation_list.append(name_dict_converse[tostation])\n",
    "                    mid_starttime_list.append(starttime)\n",
    "                    mid_endtime_list.append(endtime)\n",
    "                    mid_duringtime_list.append(duringtime)\n",
    "\n",
    "                    mid_super_soft_sleeper_count.append(data[21] if data[21].isdigit() or data[21] == '有' else None)\n",
    "                    mid_soft_sleeper_count.append(data[23] if data[23].isdigit() or data[23] == '有' else None)\n",
    "                    mid_soft_seat_count.append(data[24] if data[24].isdigit() or data[24] == '有' else None)\n",
    "                    mid_no_seat_count.append(data[26] if data[26].isdigit() or data[26] == '有' else None)\n",
    "                    mid_hard_sleeper_count.append(data[28] if data[28].isdigit() or data[28] == '有' else None)\n",
    "                    mid_hard_seat_count.append(data[29] if data[29].isdigit() or data[29] == '有' else None)\n",
    "                    mid_second_seat_count.append(data[30] if data[30].isdigit() or data[30] == '有' else None)\n",
    "                    mid_first_seat_count.append(data[31] if data[31].isdigit() or data[31] == '有' else None)\n",
    "                    mid_business_seat_count.append(data[32] if data[32].isdigit() or data[32] == '有' else None)\n",
    "                    mid_high_speed_sleeper_count.append(data[33] if data[33].isdigit() or data[33] == '有' else None)        \n",
    "    except Exception as e:\n",
    "        print(e)\n",
    "        print('查询速度过快')\n",
    "    finally:    \n",
    "        #生成df\n",
    "        result_df_mid = pd.DataFrame([mid_train_no_all_list,mid_train_no_list,\n",
    "                      mid_fromstation_list,mid_tostation_list,mid_starttime_list,\n",
    "                      mid_endtime_list,mid_duringtime_list,\n",
    "                     mid_super_soft_sleeper_count,mid_soft_sleeper_count,mid_soft_seat_count,mid_no_seat_count,\n",
    "                     mid_hard_sleeper_count,mid_hard_seat_count,mid_second_seat_count,mid_first_seat_count,\n",
    "                      mid_business_seat_count,mid_high_speed_sleeper_count],\n",
    "                     index=['车号','车次','出发','到达','出发时间','到达时间',\n",
    "                           '时长','高级软卧','软卧','软座','无座','硬卧','硬座','二等','一等','商务','动卧']).T  \n",
    "        if not result_df_mid.empty:\n",
    "            result_df_mid = result_df_mid.sort_values('出发时间').reset_index(drop = True)\n",
    "            if time_limit:\n",
    "                result_df_mid = result_df_mid[(result_df_mid['出发时间']>=time_limit[0])&(result_df_mid['出发时间']<=time_limit[1])]\n",
    "            #删除全空列\n",
    "            for col in result_df_mid.columns:\n",
    "                if result_df_mid[col].count() == 0:\n",
    "                    result_df_mid.drop(labels=col, axis=1, inplace=True)\n",
    "            #置换空值       \n",
    "            result_df_mid = result_df_mid.where(pd.notnull(result_df_mid),'')        \n",
    "            display(result_df_mid)  \n",
    "            result_df_mid.to_csv('mid.csv')\n",
    "            return result_df_mid\n",
    "        else:\n",
    "            print('中间站结果为空')\n",
    "            return None"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### check!"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 36,
   "metadata": {
    "scrolled": true
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "中间站结果为空\n"
     ]
    }
   ],
   "source": [
    "# def time_judge(time,flag=0):\n",
    "#     if flag:  #test\n",
    "#         return True\n",
    "#     if time >= time_limit[0] and time <= time_limit[1]:\n",
    "#         return True\n",
    "#     else:\n",
    "#         return False\n",
    "try:\n",
    "    train_no_all_list = []\n",
    "    train_no_list = []\n",
    "    fromstation_list = []\n",
    "    tostation_list = []\n",
    "    starttime_list = []\n",
    "    endtime_list = []\n",
    "    duringtime_list = []\n",
    "    super_soft_sleeper_count = []\n",
    "    soft_sleeper_count = []\n",
    "    soft_seat_count = []\n",
    "    no_seat_count = []\n",
    "    hard_sleeper_count = []\n",
    "    hard_seat_count = []\n",
    "    second_seat_count = []\n",
    "    first_seat_count = []\n",
    "    business_seat_count = []\n",
    "    high_speed_sleeper_count = []\n",
    "\n",
    "    #中间站链接\n",
    "    url_midstation_list = []\n",
    "\n",
    "    #遍历每一趟车\n",
    "    result = req.get(origin_url).json()\n",
    "    \n",
    "    for i in result['data']['result']:\n",
    "        data = i.split('|')\n",
    "        train_no_all = data[2] #完整车号\n",
    "        train_no = data[3] #车号\n",
    "        startstation = data[4]    #始发站\n",
    "        endstation = data[5]    #终点站\n",
    "        fromstation = data[6]    #起点\n",
    "        tostation = data[7]    #终点\n",
    "        starttime = data[8]  #出发时间\n",
    "        endtime = data[9]  #到达时间\n",
    "        duringtime = data[10]  #历时\n",
    "        isbuyable = data[11]  #能否预定   \n",
    "        date = data[13][:4]+'-'+data[13][4:6]+'-'+data[13][6:]  #日期 \n",
    "    #     ticket_dict = {    \n",
    "    #         '高级软卧' : data[21] if data[21].isdigit() or data[21] == '有' else None,  #高级软卧\n",
    "    #         '软卧' : data[23] if data[23].isdigit() or data[23] == '有' else None,  #软卧\n",
    "    #         '软座' : data[24] if data[24].isdigit() or data[24] == '有' else None,  #软座\n",
    "    #         '无座' : data[26] if data[26].isdigit() or data[26] == '有' else None,  #无座\n",
    "    #         '硬卧' : data[28] if data[28].isdigit() or data[28] == '有' else None ,  #硬卧   \n",
    "    #         '硬座' : data[29] if data[29].isdigit() or data[29] == '有' else None ,  #硬座\n",
    "    #         '二等' : data[30] if data[30].isdigit() or data[30] == '有' else None , #二等座\n",
    "    #         '一等' : data[31] if data[31].isdigit() or data[31] == '有' else None,  #一等座\n",
    "    #         '商务' : data[32] if data[32].isdigit() or data[32] == '有' else None,  #商务特等座\n",
    "    #         '动卧' : data[33] if data[33].isdigit() or data[33] == '有' else None,  #动卧 \n",
    "    #     }   \n",
    "        #若可购买\n",
    "        # flag为0是测试模式\n",
    "    #     if isbuyable == 'Y' and time_judge(starttime,flag=1):\n",
    "    #         print(train_no_all,train_no.ljust(6,' '),\n",
    "    #               name_dict_converse[fromstation]+'-->'+name_dict_converse[tostation],\n",
    "    #               starttime.ljust(5,' ')+'-->'+endtime,'('+duringtime+')',end='\\t',sep='\\t')\n",
    "    #         for v in ticket_dict.values():\n",
    "    #             if v:\n",
    "    #                 print(v,end='\\t')\n",
    "    #         print()\n",
    "    #         url_part = 'https://kyfw.12306.cn/otn/czxx/queryByTrainNo?train_no={train_no_all}&from_station_telecode={fromstation}&to_station_telecode={tostation}&depart_date={date}'.format(train_no_all=train_no_all,\n",
    "    # fromstation=fromstation,tostation=tostation,date=date\n",
    "\n",
    "    # )\n",
    "    #         print(req.get(url_part).json())\n",
    "        if isbuyable == 'Y':\n",
    "            train_no_all_list.append(train_no_all)\n",
    "            train_no_list.append(train_no)\n",
    "            fromstation_list.append(name_dict_converse[fromstation])\n",
    "            tostation_list.append(name_dict_converse[tostation])\n",
    "            starttime_list.append(starttime)\n",
    "            endtime_list.append(endtime)\n",
    "            duringtime_list.append(duringtime)\n",
    "\n",
    "            super_soft_sleeper_count.append(data[21] if data[21].isdigit() or data[21] == '有' else None)\n",
    "            soft_sleeper_count.append(data[23] if data[23].isdigit() or data[23] == '有' else None)\n",
    "            soft_seat_count.append(data[24] if data[24].isdigit() or data[24] == '有' else None)\n",
    "            no_seat_count.append(data[26] if data[26].isdigit() or data[26] == '有' else None)\n",
    "            hard_sleeper_count.append(data[28] if data[28].isdigit() or data[28] == '有' else None)\n",
    "            hard_seat_count.append(data[29] if data[29].isdigit() or data[29] == '有' else None)\n",
    "            second_seat_count.append(data[30] if data[30].isdigit() or data[30] == '有' else None)\n",
    "            first_seat_count.append(data[31] if data[31].isdigit() or data[31] == '有' else None)\n",
    "            business_seat_count.append(data[32] if data[32].isdigit() or data[32] == '有' else None)\n",
    "            high_speed_sleeper_count.append(data[33] if data[33].isdigit() or data[33] == '有' else None)        \n",
    "\n",
    "        url_part = 'https://kyfw.12306.cn/otn/czxx/queryByTrainNo?train_no={train_no_all}&from_station_telecode={fromstation}&to_station_telecode={tostation}&depart_date={date}'.format(train_no_all=train_no_all,\n",
    "fromstation=fromstation,tostation=tostation,date=date)\n",
    "        url_midstation_list.append(url_part)\n",
    "\n",
    "\n",
    "except Exception as e:\n",
    "    print(e)\n",
    "    print('查询速度过快')\n",
    "finally:\n",
    "    \n",
    "    #生成df\n",
    "    result_df = pd.DataFrame([train_no_all_list,train_no_list,\n",
    "                  fromstation_list,tostation_list,starttime_list,\n",
    "                  endtime_list,duringtime_list,\n",
    "                 super_soft_sleeper_count,soft_sleeper_count,soft_seat_count,no_seat_count,\n",
    "                 hard_sleeper_count,hard_seat_count,second_seat_count,first_seat_count,\n",
    "                  business_seat_count,high_speed_sleeper_count],\n",
    "                 index=['车号','车次','出发','到达','出发时间','到达时间',\n",
    "                       '时长','高级软卧','软卧','软座','无座','硬卧','硬座','二等','一等','商务','动卧']).T      \n",
    "    if not result_df.empty:\n",
    "        #删除全空列\n",
    "        for col in result_df.columns:\n",
    "            if result_df[col].count() == 0:\n",
    "                result_df.drop(labels=col, axis=1, inplace=True)\n",
    "        if len(result_df.columns) >7:\n",
    "            #置换空值       \n",
    "            result_df = result_df.where(pd.notnull(result_df),'')\n",
    "            result_df = result_df.sort_values('出发时间')\n",
    "            if time_limit:\n",
    "                result_df = result_df[(result_df['出发时间']>=time_limit[0])&(result_df['出发时间']<=time_limit[1])]\n",
    "            display(result_df)\n",
    "            result_df.to_csv('main.csv')\n",
    "        else:\n",
    "            mid_station_check()\n",
    "    else:\n",
    "        mid_station_check()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### 第一层"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# result_df"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#### 第二层（中间站先上车后补票）"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 32,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "[]\n",
      "list.remove(x): x not in list\n",
      "查询速度过快\n"
     ]
    },
    {
     "ename": "UnboundLocalError",
     "evalue": "local variable 'mid_train_no_all_list' referenced before assignment",
     "output_type": "error",
     "traceback": [
      "\u001b[1;31m---------------------------------------------------------------------------\u001b[0m",
      "\u001b[1;31mUnboundLocalError\u001b[0m                         Traceback (most recent call last)",
      "\u001b[1;32m<ipython-input-32-bcce24af2c96>\u001b[0m in \u001b[0;36m<module>\u001b[1;34m\u001b[0m\n\u001b[1;32m----> 1\u001b[1;33m \u001b[0mmid_result\u001b[0m \u001b[1;33m=\u001b[0m \u001b[0mmid_station_check\u001b[0m\u001b[1;33m(\u001b[0m\u001b[1;33m)\u001b[0m\u001b[1;33m\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0m",
      "\u001b[1;32m<ipython-input-30-f1a804f0ccba>\u001b[0m in \u001b[0;36mmid_station_check\u001b[1;34m()\u001b[0m\n\u001b[0;32m     86\u001b[0m     \u001b[1;32mfinally\u001b[0m\u001b[1;33m:\u001b[0m\u001b[1;33m\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0;32m     87\u001b[0m         \u001b[1;31m#生成df\u001b[0m\u001b[1;33m\u001b[0m\u001b[1;33m\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[1;32m---> 88\u001b[1;33m         result_df_mid = pd.DataFrame([mid_train_no_all_list,mid_train_no_list,\n\u001b[0m\u001b[0;32m     89\u001b[0m                       \u001b[0mmid_fromstation_list\u001b[0m\u001b[1;33m,\u001b[0m\u001b[0mmid_tostation_list\u001b[0m\u001b[1;33m,\u001b[0m\u001b[0mmid_starttime_list\u001b[0m\u001b[1;33m,\u001b[0m\u001b[1;33m\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n\u001b[0;32m     90\u001b[0m                       \u001b[0mmid_endtime_list\u001b[0m\u001b[1;33m,\u001b[0m\u001b[0mmid_duringtime_list\u001b[0m\u001b[1;33m,\u001b[0m\u001b[1;33m\u001b[0m\u001b[1;33m\u001b[0m\u001b[0m\n",
      "\u001b[1;31mUnboundLocalError\u001b[0m: local variable 'mid_train_no_all_list' referenced before assignment"
     ]
    }
   ],
   "source": [
    "# mid_result = mid_station_check()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# super_soft_sleeper_count = data[21]  #高级软卧\n",
    "# soft_sleeper_count = data[23]  #软卧一等座\n",
    "# soft_seat_count = data[24]  #软座\n",
    "# no_seat_count = data[26]  #无座\n",
    "# hard_sleeper_count = data[28]  #硬卧   \n",
    "# hard_seat_count = data[29]  #硬座\n",
    "# second_seat_count = data[30]  #二等座\n",
    "# first_seat_count = data[31]  #一等座\n",
    "# business_seat_count = data[32]  #商务特等座\n",
    "# high_speed_sleeper_count = data[33]  #动卧"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.7.4"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
