import datetime
from enum import Enum

from hemistereo import *
import pycurl
from PIL import Image
import cv2
from io import BytesIO
import ast
import sys
from fastapi import FastAPI, Form, requests
from fastapi.responses import FileResponse
import os
import getpass
import uvicorn
import math
from numpy import *

# model_name = "TestCam2-Training1"
# server = "http://deeplearning06.muc:4344/"

app = FastAPI(title="Hemistereo API", description="<b>API for performing object detection using Hemistereo NX 180 X "
                                                  "camera</b></br></br>"
                                                  "<b>Contact the developer:</b></br>"
                                                  "<b>Rami Naffah: <a href='mailto:rami.naffah@lau.edu'>rami.naffah"
                                                  "@lau.edu</a></b></br> "
                                                  "<b>")
user = getpass.getuser()
ppm_w = 14.4
ppm_h = 20.75
cx = 1023 / 2
cy = 767 / 2
h_sensor = 3040
w_sensor = 4032
fc1 = 1155.309825940708606140106
theta_d_max = 1.74532925199432953355938
field_of_view_h = 180
field_of_view_v = 140

fov_h_rad = field_of_view_h * math.pi / 180
fov_v_rad = field_of_view_v * math.pi / 180


# For Equiangular
# fx = 1024 / fov_h_rad
# fy = 768 / fov_v_rad

# Intrinsic Matrix
# K = array([[fx, 0, cx],
#            [0, fy, cy],
#            [0, 0, 1]])


def single_shot(cam_ip):
    ctx = Context(appname="stereo", server=cam_ip, port="8888")
    msg = ctx.readTopic("image")
    np = unpackMessageToNumpy(msg.data)
    i = Image.fromarray(np)
    i.save('raw_image.png')
    return ctx


def get_answer(model, server):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.POST, 1)
    c.setopt(c.URL, server + "detect")
    c.setopt(c.HTTPPOST, [("model", model), ("image", (c.FORM_FILE, "images/raw_image.png"))])
    c.setopt(c.WRITEFUNCTION, buffer.write)
    c.perform()
    c.close()
    request_answer = buffer.getvalue().decode('utf-8')
    request_dict = ast.literal_eval(request_answer)
    return request_dict


def function(model, server, cam_ip):
    ctx = single_shot(cam_ip)
    msg = ctx.readTopic("image")
    np = unpackMessageToNumpy(msg.data)
    nearest_pixel = sys.maxsize
    far_pixel = 0
    width = 0
    height = 0
    depth = 0
    distance = ctx.readTopic("distance")
    print('Sending image to api with specified model')
    answer = get_answer(model, server)
    message = ctx.readTopic("distance")
    distance = unpackMessageToNumpy(message.data)

    if len(answer["bounding-boxes"]) > 0:
        for box in range(len(answer['bounding-boxes'])):
            objectClassName = answer['bounding-boxes'][box]['ObjectClassName']
            bounding_box = answer['bounding-boxes'][box]['coordinates']
            bottom = bounding_box['bottom']
            left = bounding_box['left']
            right = bounding_box['right']
            top = bounding_box['top']

            for i in range(left, right):
                for j in range(top, bottom):
                    if distance[j][i] < nearest_pixel and distance[j][i] != 0:
                        nearest_pixel = distance[j][i][0]
                    if distance[j][i] > far_pixel:
                        far_pixel = distance[j][i][0]
                        print(far_pixel)

            cv2.rectangle(np, (right, top), (left, bottom), (255, 0, 0), 2)
            img = Image.fromarray(np, 'RGB')

            depth = (far_pixel - nearest_pixel) / 10

            # Variable Distance Camera
            height_px = bottom - top
            height_obj = nearest_pixel * (height_px / h_sensor) * theta_d_max / 2

            width_px = right - left
            width_obj = nearest_pixel * (width_px / w_sensor) * fov_h_rad

            img.save('images/labeled_image.png')
            username = getpass.getuser()
        #     if "labeled_images" not in os.listdir('/home/{}/Downloads/'.format(username)):
        #         os.mkdir('/home/{}/Downloads/labeled_images'.format(username))
        # img.save('/home/{}/Downloads/labeled_images/{}.png'.format(username, datetime.datetime.now()), 'PNG')
    else:
        nearest_pixel = -1

    if nearest_pixel > 0:
        answer['bounding-boxes'][box]['dimensions'] = {"depth": depth, "width": width_obj, "height": height_obj}
        answer['bounding-boxes'][box]['distance'] = float(nearest_pixel / 10)

    else:

        print("No objects labeled.")

    return answer


@app.post("/single_shot")
def see_raw_image(cam_ip: str = Form(...)):
    single_shot(cam_ip)
    # i.save('/home/{}/Downloads/images/{}.png'.format(user, datetime.datetime.now()))
    return FileResponse('images/raw_image.png')


@app.post("/detect")
def detect_object(model: str = Form(...), server: str = Form(...), cam_ip: str = Form(...)):
    # open('raw_image.png', server).write(r.content)
    return function(model, server, cam_ip)


@app.post("/detect/save_image")
def save_labeled_image(model: str = Form(...), server: str = Form(...), cam_ip: str = Form(...)):
    answer = function(model, server, cam_ip)
    if len(answer["bounding-boxes"]) > 0:
        return FileResponse('images/labeled_image.png')


if __name__ == '__main__':
    uvicorn.run("camera_to_server:app", reload=True)
