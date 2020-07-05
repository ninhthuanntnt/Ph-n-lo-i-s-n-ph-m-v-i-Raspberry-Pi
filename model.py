
class ImageData:
    def __init__(self, id=0 , image='' , name='', path='', trainKP='', trainDesc=''):
        self.id = id
        self.image = image
        self.name = name
        self.path = path
        self.trainKP = trainKP
        self.trainDesc = trainDesc
        self.box = 0