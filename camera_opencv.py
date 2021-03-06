import cv2
from base_camera import BaseCamera
import facerecognition
import Queue
import numpy as np
import time,os

def rotate(image, angle, center=None, scale=1.0):
    (h, w) = image.shape[:2]

    if center is None:
        center = (w / 2, h / 2)

    M = cv2.getRotationMatrix2D(center, angle, scale)
    rotated = cv2.warpAffine(image, M, (w, h))

    return rotated

def draw_name(image, rect, name):
    # cv2.rectangle(images[i],(rect[0],rect[1]),(rect[0] + rect[2],rect[1]+rect[3]),(0,0,255),2)
    # cv2.putText(images[i], ret['name'],(rect[0],rect[1]),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)
    cv2.rectangle(image,(rect[0],rect[1]),(rect[0] + rect[2],rect[1]+rect[3]),(127,255,0),1)
			
    # draw thicking corners
    int_x=rect[2]/5
    int_y=rect[3]/5
    cv2.line(image,(rect[0],rect[1]),(rect[0] + int_x,rect[1]),(127,255,0),3)
    cv2.line(image,(rect[0],rect[1]),(rect[0],rect[1]+int_y),(127,255,0),3)
    cv2.line(image,(rect[0],rect[1]+int_y*4),(rect[0],rect[1]+rect[3]),(127,255,0),3)
    cv2.line(image,(rect[0],rect[1]+rect[3]),(rect[0] + int_x,rect[1]+rect[3]),(127,255,0),3)
    cv2.line(image,(rect[0]+ int_x*4,rect[1]+rect[3]),(rect[0] + rect[2],rect[1]+rect[3]),(127,255,0),3)
    cv2.line(image,(rect[0] + rect[2],rect[1]+rect[3]),(rect[0] + rect[2],rect[1]+int_y*4),(127,255,0),3)
    cv2.line(image,(rect[0] + rect[2],rect[1]+int_y),(rect[0] + rect[2],rect[1]),(127,255,0),3)
    cv2.line(image,(rect[0] + int_x*4,rect[1]),(rect[0] + rect[2],rect[1]),(127,255,0),3)
    #draw middle line
    line_x=rect[2]/8
    cv2.line(image,(rect[0]-line_x,rect[1]+rect[3]/2),(rect[0] + line_x,rect[1]+rect[3]/2),(127,255,0),1)
    cv2.line(image,(rect[0]+rect[2]/2,rect[1]+rect[3]-line_x),(rect[0]+rect[2]/2,rect[1]+rect[3]+line_x),(127,255,0),1)
    cv2.line(image,(rect[0]+line_x*7,rect[1]+rect[3]/2),(rect[0]+line_x*9,rect[1]+rect[3]/2),(127,255,0),1)
    cv2.line(image,(rect[0]+rect[2]/2,rect[1]-line_x),(rect[0]+rect[2]/2,rect[1]+line_x),(127,255,0),1)
    #write name text
    cv2.putText(image, name,(rect[0]+rect[2],rect[1]),cv2.FONT_HERSHEY_COMPLEX,int_y*1.0/40,(242,243,231),2)


facerecg = facerecognition.FaceRecognition("./models", 0.63)

class Camera(BaseCamera):
    video_source = []
    camera_number = 0
    reg_ret = []
    new_name = None

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source
        Camera.camera_number = len(source)
        if Camera.camera_number > 2:
            Camera.camera_number = 2

    @staticmethod
    def del_person(name):
        facerecg.del_person(name)

    @staticmethod
    def add_person(name):
        Camera.new_name = name

    @staticmethod
    def get_names():
        return facerecg.get_names()

    @staticmethod
    def frames():
        framequeue = []
        cameras = []
        for i in range(Camera.camera_number):
            cameras.append(cv2.VideoCapture(Camera.video_source[i]))
            if not cameras[i].isOpened():
                raise RuntimeError('Could not start camera. Index:' , i)

        while True:
            images = []

            for i in range(Camera.camera_number):
                _, img = cameras[i].read()
                #after = rotate(img, -90)
                #images.append(after)
                images.append(img)

            #framequeue.put(images)
            #images = framequeue.get()
            image_char = images[0].astype(np.uint8).tostring()

            if Camera.new_name != None:
                rets = facerecg.add_person(Camera.new_name,images[0].shape[0], images[0].shape[1], image_char)
                if rets == 0:
                    Camera.new_name = None
                rets = []
            else:
                rets = facerecg.recognize(images[0].shape[0], images[0].shape[1], image_char)
            #for (i, each) in  enumerate(rets):
            for ret  in  rets:
                #for ret in each:
                #draw bounding box for the face
                rect = ret['rect']
                draw_name(images[0], rect, ret['name'])

            if (len(images) == 1):
                final1 = images[0]
                final = cv2.copyMakeBorder(final1,0,0,192,192, cv2.BORDER_CONSTANT,value=[255,255,255])
            elif (len(images) == 2):
                final1 = np.concatenate((images[0], images[1]), axis=1)
                final = cv2.copyMakeBorder(final1,48,48,0,0, cv2.BORDER_CONSTANT,value=[255,255,255])
            elif (len(images) == 3):
                final1 = np.concatenate((images[0], images[1]), axis=1)
                final2 = np.concatenate((images[2], images[2]), axis=1)
                final = np.concatenate((final1, final2), axis=0)
            elif (len(images) == 4):
                final1 = np.concatenate((images[0], images[1]), axis=1)
                final2 = np.concatenate((images[2], images[3]), axis=1)
                final = np.concatenate((final1, final2), axis=0)
            yield cv2.imencode('.png', final)[1].tobytes()
