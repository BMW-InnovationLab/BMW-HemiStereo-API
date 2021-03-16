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
from scipy import ndimage

user = getpass.getuser()
h_sensor = 768
w_sensor = 1024
theta_d_max = 1.74532925199432953355938

field_of_view_h = 140
field_of_view_v = 140

fov_h_rad = field_of_view_h * math.pi / 180
fov_v_rad = field_of_view_v * math.pi / 180


def single_shot(cam_ip):
    numpy.set_printoptions(threshold=sys.maxsize)
    ctx = Context(appname="stereo", server=cam_ip, port="8888")
    ctx.setProperty("stereo_target_camera_enabled", bool(1))
    # Set Camera Model to Pinhole
    ctx.setProperty("stereo_target_camera_model", 4)
    msg = ctx.readTopic("image")

    msg1 = ctx.readTopic("distance")
    distance = unpackMessageToNumpy(msg1.data)

    print(distance.shape)
    distance_str = ""
    for i in range(0, len(distance)):
        for j in range(0, len(distance[i])):
            distance_str += str(distance[i][j][0])

    f = open("distance.txt", "w")
    f.write(distance_str)
    f.close()

    np = unpackMessageToNumpy(msg.data)
    i = Image.fromarray(np)
    i.save('images/raw_image.png')
    # i.save(path + '{}.png'.format(datetime.datetime.now()), 'PNG')
    return ctx


def get_answer(model, server, image_path):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.POST, 1)
    c.setopt(c.URL, server + "detect")
    c.setopt(c.HTTPPOST, [("model", model), ("image", (c.FORM_FILE, image_path))])
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
    answer = get_answer(model, server, "images/raw_image.png")
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
    # Calibrate Textureness Avg. Threshold
    # threshold = compute_threshold(cam_ip, model, server)
    # print(threshold)

    # Detect Object
    ctx = single_shot(cam_ip)
    msg = ctx.readTopic("image")
    nump = unpackMessageToNumpy(msg.data)
    nearest_pixel = sys.maxsize
    far_pixel = 0
    depth = 0
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
                    if distance[j][i] > far_pixel:
                        far_pixel = distance[j][i][0]
            # Draw Bounding Box
            cv2.rectangle(nump, (right, top), (left, bottom), (255, 0, 0), 2)
            img = Image.fromarray(nump, 'RGB')

            depth = (far_pixel - nearest_pixel) / 10
            print("field of view v: " + str(ctx.getProperty("stereo_matching_image_fov_v")))

            # Variable Distance Camera
            height_px = bottom - top
            height_obj = nearest_pixel / 10 * (height_px / h_sensor) * math.tan(fov_v_rad / 2) * 2

            width_px = right - left
            width_obj = nearest_pixel / 10 * (width_px / w_sensor) * math.tan(fov_h_rad / 2) * 2

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


def compute_threshold(cam_ip):
    distance, ctx = calculate_distance(model, server, cam_ip)
    textureness = 0.271 * (distance / 10) + 9.52
    ctx.setProperty("stereo_textureness_filter_average_textureness", np.float32(textureness))
    return textureness


# Need to convert distance image into numpy array to calculate distance.
def detect_object_image(image_path, model, server):
    nearest_pixel = sys.maxsize
    far_pixel = 0

    answer = get_answer(model, server, image_path)

    with open('distance.txt', 'r+') as file:
        distance = file.read().rstrip()
    distance_array = numpy.array(list(distance), dtype=numpy.uint16)
    distance_array = numpy.reshape(distance_array, (800, 1024, 1))

    if len(answer["bounding-boxes"]) > 0:
        for box in range(len(answer['bounding-boxes'])):
            object_class_name = answer['bounding-boxes'][box]['ObjectClassName']
            bounding_box = answer['bounding-boxes'][box]['coordinates']
            bottom = bounding_box['bottom']
            left = bounding_box['left']
            right = bounding_box['right']
            top = bounding_box['top']
    #
            for i in range(left, right):
                for j in range(top, bottom):
                    if distance_array[j][i][0] < nearest_pixel and distance_array[j][i][0] != 0:
                        nearest_pixel = distance_array[j][i][0]
                    if distance_array[j][i][0] > far_pixel:
                        far_pixel = distance_array[j][i][0]
        cv2.rectangle(numpy_data, (right, top), (left, bottom), (255, 0, 0), 2)
    #     img = Image.fromarray(numpy_data, 'RGB')
    #
    #     depth = (far_pixel - nearest_pixel) / 10
    #
    #     # Variable Distance Camera
    #     height_px = bottom - top
    #     height_obj = nearest_pixel / 10 * (height_px / h_sensor) * math.tan(fov_v_rad / 2) * 2
    #
    #     width_px = right - left
    #     width_obj = nearest_pixel / 10 * (width_px / w_sensor) * math.tan(fov_h_rad / 2) * 2
    #
    #     img.save('images/labeled_image.png')
    # else:
    #     nearest_pixel = -1
    #
    # if nearest_pixel > 0:
    #     answer['bounding-boxes'][box]['dimensions'] = {"depth": depth, "width": float("{:.2f}".format(width_obj)),
    #                                                    "height": float("{:.2f}".format(height_obj))}
    #     answer['bounding-boxes'][box]['distance'] = float(nearest_pixel / 10)
    #
    # else:
    #     print("No objects labeled.")
    #
    # return answer
