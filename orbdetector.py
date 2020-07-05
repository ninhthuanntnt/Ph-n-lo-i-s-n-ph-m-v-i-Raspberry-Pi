import cv2
import numpy as np
import time
import sys
PY3 = sys.version_info[0] == 3
if PY3:
    xrange = range
from collections import namedtuple
PlanarTarget = namedtuple('PlaneTarget', 'id,name,box,image,keypoints,descrs')
TrackedTarget = namedtuple('TrackedTarget', 'target, quad')
MIN_MATCH_COUNT=12
class ORBDetector:
    __FLANN_INDEX_LSH=6
    __flannParam=dict(algorithm = __FLANN_INDEX_LSH,
                   table_number = 6, # 12
                   key_size = 12,     # 20
                   multi_probe_level = 1) #2
    def __init__(self):
        #self.listImageData=[]
        self.detector=cv2.ORB_create(nfeatures=1500)
        self.targets = []
        
        self.__flann=cv2.FlannBasedMatcher(self.__flannParam,{})
    def detectObject(self,frame):
#         init param
        box = 1
        name =''
        coordinates = []
        frame_points, frame_descrs = self.detectAndCompute(frame, None)
        # frame_descrs = np.float32(frame_descrs)
        if len(frame_points) < MIN_MATCH_COUNT:
            return [box, name, coordinates]
        t=time.time()
        matches = self.__flann.knnMatch(frame_descrs, k = 2)
        
        matches = [m[0] for m in matches if len(m) == 2 and m[0].distance < m[1].distance * 0.75]
        
        matches_by_id = [[] for _ in xrange(len(self.targets))]
        
        
        for m in matches:
            matches_by_id[m.imgIdx].append(m)
        tracked = []
        for imgIdx, matches in enumerate(matches_by_id):
            if len(matches) < MIN_MATCH_COUNT:
                continue
            target = self.targets[imgIdx]
            p0 = [target.keypoints[m.trainIdx].pt for m in matches]
            p1 = [frame_points[m.queryIdx].pt for m in matches]
            p0, p1 = np.float32((p0, p1))
            H, status = cv2.findHomography(p0, p1, cv2.RANSAC, 3.0)
            status = status.ravel() != 0
            if status.sum() < MIN_MATCH_COUNT:
                continue
            # p0, p1 = p0[status], p1[status]
            w,h=target.image.shape
            quad = np.float32([[0, 0], [0, w],[h,w],[h,0]])
            quad = cv2.perspectiveTransform(quad.reshape(1, -1, 2), H).reshape(-1, 2)
            
            track = TrackedTarget(target=target,quad=quad)
            tracked.append(track)
        # tracked.sort(key = lambda t: len(t.p0), reverse=True)
        # print(time.time()-t)
        if len(tracked) > 0:
            box = tracked[0].target.box
            name = tracked[0].target.name
            coordinates = np.int32(tracked[0].quad)
        return [box, name, coordinates]
       
    def detectAndCompute(self, frame, mask):
        keypoints, descrs = self.detector.detectAndCompute(frame, mask)
        if descrs is None:  # detectAndCompute returns descs=None if not keypoints found
            descrs = []
        return keypoints, descrs
        
    def addData(self, imageData):
        self.listImageData.append(imageData)

    def setData(self, listImageData):
        #for imageData in listImageData:
        #    print('Loaded' + imageData.name)
        #self.listImageData = listImageData 
        for imageData in listImageData:
        #    print(np.unit8(imageData.trainKP))
           print('Loaded' + imageData.name)
           points= imageData.trainKP  
           descs = np.uint8(imageData.trainDesc)
           self.__flann.add([descs])
           target = PlanarTarget(id=imageData.id,name=imageData.name,box=imageData.box,image = cv2.imread(imageData.path,0),keypoints = points,descrs=descs)
           self.targets.append(target)
           
           print(len(self.targets))
            
                       