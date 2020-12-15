"""爬取指定起始地点中途全部换乘的12306的火车票信息"""
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
import json, base64
import requests,os
from bs4 import BeautifulSoup
import pickle
import urllib