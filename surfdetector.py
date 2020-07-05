import cv2
import numpy as np

class SURFDetector:
    __FLANN_INDEX_KDITREE = 0
    __MIN_MATCH_COUNT = 100
    __detector = cv2.xfeatures2d.SURF_create()
    __flannParam = dict(algorithm=__FLANN_INDEX_KDITREE, tree=5)
    __flann = cv2.FlannBasedMatcher(__flannParam, {})
    def __init__(self):
        self.listImageData = []

    def detectObject(self, frame):
        QueryImg = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        coordinates = []
        detectedName = ''
        indexBox = 1
        for i in range(0, len(self.listImageData)):
            queryKP, queryDesc = self.__detector.detectAndCompute(QueryImg, None)
            matches = self.__flann.knnMatch(
                queryDesc, self.listImageData[i].trainDesc, k=2)

            goodMatch = []
            for m, n in matches:
                if(m.distance < 0.8*n.distance):
                    goodMatch.append(m)

            if(len(goodMatch) > self.__MIN_MATCH_COUNT):
                tp = []
                qp = []
                for m in goodMatch:
                    tp.append(self.listImageData[i].trainKP[m.trainIdx].pt)
                    qp.append(queryKP[m.queryIdx].pt)
                tp, qp = np.float32((tp, qp))
                H, status = cv2.findHomography(tp, qp, cv2.RANSAC, 3.0)
                h, w = self.listImageData[i].image.shape
                trainBorder = np.float32(
                    [[[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]])
                try:
                    queryBorder = cv2.perspectiveTransform(trainBorder, H)
                except:
                    break
                
                coordinates = np.int32(queryBorder)
                detectedName = self.listImageData[i].name
                indexBox = self.listImageData[i].box
                break
            else:
                print("Not Enough match found- %d/%d" %
                      (len(goodMatch), self.__MIN_MATCH_COUNT))
        return [indexBox, detectedName, coordinates]

    def detectAndCompute(self, image, mask):
        return self.__detector.detectAndCompute(image, mask)
    
    def setData(self, listImageData):
        for imageData in listImageData:
            print('Loaded' + imageData.name)
        self.listImageData = listImageData