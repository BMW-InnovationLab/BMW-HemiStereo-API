from hemistereo import *
import pycurl
from PIL import Image
import cv2
from io import BytesIO
import ast
import getpass
from numpy import *
import sys
import datetime

user = getpass.getuser()
h_sensor = 800
w_sensor = 1024
aspect_ratio = w_sensor / h_sensor
fc1 = 1155.309825940708606140106
theta_d_max = 1.74532925199432953355938

afov_h = 180 * math.pi / 180
afov_v = 140 * math.pi / 180

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
    ctx.setProperty("stereo_target_camera_enabled", bool(1))
    ctx.setProperty("stereo_target_camera_model", 5)
    msg = ctx.readTopic("image")
    np = unpackMessageToNumpy(msg.data)
    i = Image.fromarray(np)
    i.save('images/raw_image.png')
    # i.save('/home/{}/Downloads/images/{}.png'.format(user, datetime.datetime.now()), 'PNG')
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


def calculate_distance(model, server, cam_ip):
    ctx = single_shot(cam_ip)
    nearest_pixel = sys.maxsize
    print('Sending image to api with specified model')
    answer = get_answer(model, server)
    message = ctx.readTopic("distance")
    distance = unpackMessageToNumpy(message.data)

    if len(answer["bounding-boxes"]) > 0:
        for box in range(len(answer['bounding-boxes'])):
            object_class_name = answer['bounding-boxes'][box]['ObjectClassName']
            bounding_box = answer['bounding-boxes'][box]['coordinates']
            bottom = bounding_box['bottom']
            left = bounding_box['left']
            right = bounding_box['right']
            top = bounding_box['top']

            for i in range(left, right):
                for j in range(top, bottom):
                    if distance[j][i] < nearest_pixel and distance[j][i] != 0:
                        nearest_pixel = distance[j][i][0]
    else:
        nearest_pixel = -1
    return nearest_pixel, ctx


def detect(model, server, cam_ip):
    ctx = single_shot(cam_ip)
    msg = ctx.readTopic("image")
    nump = unpackMessageToNumpy(msg.data)
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
            object_class_name = answer['bounding-boxes'][box]['ObjectClassName']
            bounding_box = answer['bounding-boxes'][box]['coordinates']
            bottom = bounding_box['bottom']
            left = bounding_box['left']
            right = bounding_box['right']
            top = bounding_box['top']

            for i in range(left, right):
                for j in range(top, bottom):
                    if distance[j][i] < nearest_pixel and distance[j][i] != 0:
                        nearest_pixel = distance[j][i][0]
                        # textureness = 0.271 * (nearest_pixel / 10) + 9.52
                        # ctx.setProperty("stereo_textureness_filter_average_textureness", np.float32(textureness))
                    if distance[j][i] > far_pixel:
                        far_pixel = distance[j][i][0]

            cv2.rectangle(nump, (right, top), (left, bottom), (255, 0, 0), 2)
            img = Image.fromarray(nump, 'RGB')

            depth = (far_pixel - nearest_pixel) / 10
            print("field of view v: " + str(ctx.getProperty("stereo_matching_image_fov_v")))

            # Variable Distance Camera
            # fov_v = 2 * (nearest_pixel / 10) * math.tan(afov_v/2)

            height_px = bottom - top
            height_obj = nearest_pixel / 10 * (height_px / h_sensor) * fov_v_rad
            # height_obj = nearest_pixel / 10 * (height_px / h_sensor) * fov_v

            # fov_h = 2 * (nearest_pixel / 10) * math.tan(afov_h/2)
            width_px = right - left
            # width_obj = nearest_pixel / 10 * (width_px / w_sensor) * fov_h
            width_obj = nearest_pixel / 10 * (width_px / w_sensor) * fov_h_rad * 1.75

            img.save('images/labeled_image.png')

        #     if "labeled_images" not in os.listdir('/home/{}/Downloads/'.format(user)):
        #         os.mkdir('/home/{}/Downloads/labeled_images'.format(user))
        # img.save('/home/{}/Downloads/labeled_images/{}.png'.format(user, datetime.datetime.now()), 'PNG')
    else:
        nearest_pixel = -1

    if nearest_pixel > 0:
        answer['bounding-boxes'][box]['dimensions'] = {"depth": depth, "width": float("{:.2f}".format(width_obj)),
                                                       "height": float("{:.2f}".format(height_obj))}
        answer['bounding-boxes'][box]['distance'] = float(nearest_pixel / 10)

    else:
        print("No objects labeled.")

    return answer


def compute_threshold(cam_ip, model, server):
    distance, ctx = calculate_distance(model, server, cam_ip)
    textureness = 0.271 * (distance / 10) + 9.52
    ctx.setProperty("stereo_textureness_filter_average_textureness", np.float32(textureness))
    return textureness
