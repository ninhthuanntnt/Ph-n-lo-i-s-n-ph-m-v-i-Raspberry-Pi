from firebase import firebase
from datetime import datetime
import time

class FirebaseService:
    __url = 'https://ntnt-1999.firebaseio.com/'
    
    def __init__(self):
        self.app = firebase.FirebaseApplication('https://ntnt-1999.firebaseio.com/', authentication=None)
        
        now = datetime.now()
        self.year = now.year
        self.month = now.month
        self.day = now.day
        self.link = '{0}/{1}/{2}'.format(self.year, self.month, self.day)
        self.linkToProducts = self.link + '/products'
        self.startTime = now.strftime('%H:%M:%S')
        if self.app.get('/{0}'.format(self.year),'') == None:
            self.app.put('/',str(year),{
                str(month) : {
                    str(day):{
                        'history':{
                            self.startTime : ''
                            },
                        'status' : True
                    }
                }
            })
            
        elif self.app.get('/{0}/{1}'.format(self.year, self.month),'') == None:
            self.app.put('/{0}'.format(self.year),str(self.month),{
                str(self.day) : {
                    'history':{
                            self.startTime : ''
                            },
                    'status' : True
                }
            })
            
        elif self.app.get('/{0}/{1}/{2}'.format(self.year, self.month, self.day),'') == None:
            self.app.put('/{0}/{1}'.format(self.year,self.month),str(self.day),{
                'history':{
                            self.startTime : ''
                            },
                'status' : True
            })
        else:
            self.app.put(self.link, 'status', True)
            self.app.put(self.link + '/history', self.startTime, '')
            
        self.dataProducts = self.app.get(self.linkToProducts,'')
    
    def updateProducts(self, productsForDetecting):
        self.dataProducts = self.app.get(self.link,'products')
        if self.dataProducts == None:
            dictProduct = {}
            for product in productsForDetecting:
                dictProduct[product] = 0
                self.app.put(self.link, 'products', dictProduct)
        else:
            print('testinggggg')
            for product in productsForDetecting:
                if(product not in self.dataProducts):
                    self.app.put(self.linkToProducts, product, 0)
        
        self.dataProducts = self.app.get(self.linkToProducts,'')
    
    def addOneProduct(self, productName):
        self.dataProducts[productName] += 1
    
    def setStatusToFalse(self):
        self.app.put(self.link,'status', False)
        
        now = datetime.now()
        endTime = now.strftime('%H:%M:%S')
        self.app.put(self.link + '/history', self.startTime, endTime)
    
    def updateProductQuantityThread(self):
        while(1):
            self.app.put(self.link,'products',self.dataProducts)
            print(self.dataProducts)
            time.sleep(10)
        
        
                    
        
        
        