import pymysql.cursors
import cv2
import numpy as np
import json
from model import *

class MyDatabase:
    __table_image = 'image'
    __col_id = 'id'
    __col_name = 'name'
    __col_path = 'path'
    __col_trainKP = 'trainKP'
    __col__trainDesc = 'trainDesc'

    def __init__(self):
        self.connection = DBUtils.getConnection()
        self.connection.autocommit(True)

    def open(self):
        if(not self.connection.open):
            self.connection = DBUtils.getConnection()

    def getAllData(self):
        sql = 'SELECT * FROM ' + self.__table_image
        listImageData = []
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql)

            rows = cursor.fetchall()
            for row in rows:
                imageData = ImageData()
                imageData.id = row[self.__col_id]
                imageData.name = row[self.__col_name]
                imageData.path = row[self.__col_path]
                imageData.image = cv2.imread(imageData.path, 0)
                strTrainKP = row[self.__col_trainKP]
                strTrainDesc = row[self.__col__trainDesc]
                # convert Json to list
                cvtDataKP = json.loads(strTrainKP)
                cvtDataDesc = json.loads(strTrainDesc)
                dataKP = []
                for point in cvtDataKP:
                    temp = cv2.KeyPoint(x=point[0][0], y=point[0][1], _size=point[1],
                                        _angle=point[2], _response=point[3], _octave=point[4], _class_id=point[5])
                    dataKP.append(temp)
                imageData.trainKP = dataKP
                imageData.trainDesc = np.asarray(cvtDataDesc, dtype=np.float32)
                listImageData.append(imageData)
        finally:
            print("Getted")
        return listImageData

    def getDataByNamesIn(self, names):
        sql = 'SELECT * FROM ' + self.__table_image + ' WHERE name IN(' + ','.join(names) + ')'
        print(sql)
        listImageData = []
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql)
            print(cursor.description)

            rows = cursor.fetchall()
            for row in rows:
                imageData = ImageData()
                imageData.name = row[self.__col_name]
                imageData.path = row[self.__col_path]
                imageData.image = cv2.imread(imageData.path, 0)
                strTrainKP = row[self.__col_trainKP]
                strTrainDesc = row[self.__col__trainDesc]
                # convert Json to list
                cvtDataKP = json.loads(strTrainKP)
                cvtDataDesc = json.loads(strTrainDesc)
                dataKP = []
                for point in cvtDataKP:
                    temp = cv2.KeyPoint(x=point[0][0], y=point[0][1], _size=point[1],
                                        _angle=point[2], _response=point[3], _octave=point[4], _class_id=point[5])
                    dataKP.append(temp)
                imageData.trainKP = dataKP
                imageData.trainDesc = np.asarray(cvtDataDesc, dtype=np.float32)
                listImageData.append(imageData)
        finally:
            print("Getted")
        return listImageData

    def insertData(self, imageData):
        sql = 'INSERT INTO ' + self.__table_image + ' VALUE (DEFAULT, %s, %s, %s, %s) '
        try:
            cursor = self.connection.cursor()
            name = imageData.name
            path = imageData.path
            cvtDataKP = []
            for point in imageData.trainKP:
                temp = (point.pt, point.size, point.angle,
                        point.response, point.octave, point.class_id)
                cvtDataKP.append(temp)
            strTrainKP = json.dumps(cvtDataKP)
            strTrainDesc = json.dumps(imageData.trainDesc.tolist())
            cursor.execute(sql, (name, path, strTrainKP, strTrainDesc))
            self.connection.commit()
        finally:
            print("Inserted")
    def close(self):
        if(self.connection.open):
            self.connection.close()
            
class DBUtils:
    @staticmethod
    def getConnection():
        connection = pymysql.connect(host='XXXX',
                                     port=3306,
                                     user='XXXX',
                                     password='XXXX',
                                     db='XXXX',
                                     charset='utf8',
                                     cursorclass=pymysql.cursors.DictCursor)
        return connection