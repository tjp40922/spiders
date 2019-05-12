#!/usr/bin/env python
# -*- coding: utf-8 -*-
#author tom
import  pymongo


class Connect_Mongo(object):
    def __init__(self):
        self.client=pymongo.MongoClient(host='127.0.0.1',port=27017)
        self.db=self.client['doukou_meishi']

    def inset_item(self,item):
        self.collection=self.db['meishi']
        self.collection.insert(item)


mongo=Connect_Mongo()
