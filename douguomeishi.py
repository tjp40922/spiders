#!/usr/bin/env python
# -*- coding: utf-8 -*-
#author tom
import requests
from multiprocessing import Queue
from handle_pymongo import mongo
from concurrent.futures import ThreadPoolExecutor

class Douguo():
    def __init__(self):
        self.queue_list=Queue()

    #因为所有的请求的请求头都一样，所以放在这边处理，其实请求头也可以放在__init__
    def handle_request(self,url,data):
        headers={
            "client":"4",
            "version":"6920.4",
            "device":"SM-G9350",
            "sdk":"22,5.1.1",
            "imei":"861373280750547",
            "channel":"qqkp",
            # "mac":"2c:c3:82:e2:0b:03",
            "resolution":"1024*576",
            "dpi":"1.19375",
            # "android-id":"4014041355524873",
            # "pseudo-id":"28075263",
            "brand"	:"samsung",
            "scale"	:"1.19375",
            "timezone":"28800",
            "language":"zh",
            "cns":"3",
            # "imsi":"460005263415341",
            "user-agent":"Mozilla/5.0 (Linux; Android 5.1.1; SM-G9350 Build/LMY48Z) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/39.0.0.0 Mobile Safari/537.36",
            "reach"	:"1",
            "newbie":"1",
            "Content-Type":"application/x-www-form-urlencoded; charset=utf-8",
            "Accept-Encoding":"gzip, deflate",
            # "Cookie":"duid=59758072", #能不带最好不带
            "Host":"api.douguo.net",
            # "Content":"-Length	68",
            "Connection":"keep-alive"
            }
        response = requests.post(url=url, headers=headers,data=data)
        return response

    #请求食谱首页
    def handle_index(self):
        url='http://api.douguo.net/recipe/flatcatalogs'
        data={
            "client":"4",
            # "_session":"1557318413116861373280750547",
            # "v":"1503650468",
            "_vs": "2305"
        }
        response_index=self.handle_request(url,data)
        indext_response_dict=response_index.json()
        #遍历这个三级分类
        for index_item in indext_response_dict['result']['cs']:
            for items in index_item['cs']:
                for item in items['cs']:
                    #每一个小分类
                    data2={
                        "client": "4",
                        # "_session": "1557318413116861373280750547",
                        "keyword":item['name'],
                        "order": "3",
                        "_vs": "400"
                    }
                    self.queue_list.put(data2)

    #请求具体食材的做法
    def handle_caipu_list(self,data):
        print("当前处理的食材是:",data['keyword'])
        #翻页
        for i in range(1,11):
            caipu_list_url='http://api.douguo.net/recipe/v2/search/{0}/20'.format(str(i*20))
            caipu_list_response=self.handle_request(url=caipu_list_url,data=data)
            caipu_list_dict=caipu_list_response.json()
            #判断是否有数据
            if caipu_list_dict['result']['end']==1:
                break
            for item in caipu_list_dict['result']['list']:
                caipu_info={}
                caipu_info['shicai'] = data['keyword']
                if item['type']==13:
                    caipu_info['user_name']=item['r']['an']
                    caipu_info['shicai_id']=item['r']['id']
                    caipu_info['describe']=item['r']['cookstory'].replace('/n','').replace(' ','')
                    caipu_info['caipu_name']=item['r']['n']
                    caipu_info['zuoliao_list']=item['r']['major']
                    # print(caipu_info)
                    #获取详情页的内容
                    detail_url='http://api.douguo.net/recipe/detail/'+str(caipu_info['shicai_id'])
                    detail_data={
                        "client": "4",
                        # "_session": "1557318413116861373280750547",
                        "author_id": "0",
                        "_vs": "2803",
                        "_ext":'{"query": {"kw": '+caipu_info['shicai']+', "src": "2803", "idx": "1", "type": "13", "id": '+str(caipu_info['shicai_id'])+'}}'
                    }
                    detail_response=self.handle_request(url=detail_url,data=detail_data)
                    detail_response_dict=detail_response.json()
                    caipu_info['tips']=detail_response_dict['result']['recipe']['tips']
                    caipu_info['cook_step']=detail_response_dict['result']['recipe']['cookstep']
                    print('当前入库的是：',caipu_info['caipu_name'])
                    mongo.inset_item(caipu_info)
                #g过滤掉广告
                else:
                    continue



if __name__ == '__main__':
    d=Douguo()
    d.handle_index()
    pool=ThreadPoolExecutor(max_workers=20)
    while d.queue_list.qsize()>0:
        pool.submit(d.handle_caipu_list,d.queue_list.get())

