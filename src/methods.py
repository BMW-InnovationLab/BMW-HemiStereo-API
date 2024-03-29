import pickle
from hemistereo import *
import pycurl
from PIL import Image
import cv2
from io import BytesIO
import ast
import getpass
from numpy import *
import sys
from linear_regression_model import *

user = getpass.getuser()
h_sensor = 800
w_sensor = 1024

numpy.set_printoptions(threshold=sys.maxsize)


# Function to get the name of the image from its path
def get_image_name(image_path):
    arr = image_path.split('/')
    image_name = arr[-1]
    return image_name


# Take a picture
def single_shot_save(cam_ip):
    # while True:
    ctx = Context(appname="stereo", server=cam_ip, port="8888")
    # Save Image
    msg = ctx.readTopic("image")
    np = unpackMessageToNumpy(msg.data)
    i = Image.fromarray(np)
    i.save('images/raw_image.png')
    return ctx


# Function used to communicate with a server
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


# This function calculates the distance between the camera and the labeled object
def calculate_distance(model, server, cam_ip):
    ctx = single_shot_save(cam_ip)
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


# Detect and label image
def detect(model, server, cam_ip, vertical_fov, horizontal_fov):
    # Detect Object
    ctx = single_shot_save(cam_ip)
    msg = ctx.readTopic("image")
    nump = unpackMessageToNumpy(msg.data)
    nearest_pixel = sys.maxsize
    far_pixel = 0
    depth = 0
    print('Sending image to api with specified model')
    answer = get_answer(model, server, 'images/raw_image.png')
    # define coordinates of bounding box vertices around detected object
    point_cloud = unpackMessageToNumpy(ctx.readTopic("pointcloud").data)

    if len(answer["bounding-boxes"]) > 0:
        for box in range(len(answer['bounding-boxes'])):
            object_class_name = answer['bounding-boxes'][box]['ObjectClassName']
            bounding_box = answer['bounding-boxes'][box]['coordinates']
            bottom = bounding_box['bottom']
            left = bounding_box['left']
            right = bounding_box['right']
            top = bounding_box['top']
            # Locate labeled object in the numpy array
            point_cloud_copy = point_cloud[top:bottom, left:right, 2]
            for i in range(right - left):
                for j in range(bottom - top):
                    if point_cloud_copy[j][i] < nearest_pixel and point_cloud_copy[j][i] != 0:
                        nearest_pixel = point_cloud_copy[j][i]
                    if point_cloud_copy[j][i] > far_pixel:
                        far_pixel = point_cloud_copy[j][i]

            # Draw Bounding Box
            cv2.rectangle(nump, (right, top), (left, bottom), (255, 0, 0), 2)
            img = Image.fromarray(nump, 'RGB')

            # Object's depth
            depth = (far_pixel - nearest_pixel) / 10

            # Variable Distance Camera
            # Formulas to calculate height and width of object depending on its distance from
            # the camera, as well as on its intrinsic parameters.
            height_px = bottom - top
            height_obj = nearest_pixel / 10 * (height_px / h_sensor) * math.tan((vertical_fov * math.pi / 180) / 2) * 2

            width_px = right - left
            width_obj = nearest_pixel / 10 * (width_px / w_sensor) * math.tan((horizontal_fov * math.pi / 180) / 2) * 2

            img.save('images/labeled_image.png')

    else:
        nearest_pixel = -1

    if nearest_pixel > 0:
        answer['bounding-boxes'][box]['dimensions'] = {"depth": float("{:.2f}".format(depth)),
                                                       "width": float("{:.2f}".format(width_obj)),
                                                       "height": float("{:.2f}".format(height_obj))}
        answer['bounding-boxes'][box]['distance'] = float("{:.2f}".format(nearest_pixel / 10))

    else:
        print("No objects labeled.")

    return answer


# Calibrates the camera based on light intensity and distance to the object detected
def calibrate(cam_ip, model, server):
    distance, ctx = calculate_distance(model, server, cam_ip)
    message = ctx.readTopic("stereo_frame")
    mmap = unpackMessageToMessageMap(message)
    meta = unpackMessageToMeta(mmap["metadata"])
    thresh_pred = linear_regression([[distance, meta.sceneLux]])
    ctx.setProperty("stereo_textureness_filter_average_textureness", np.float32(thresh_pred[0]))
    return thresh_pred[0]


# Detect and label input image
# Needs fixing. Should let the user specify the fov or save it for later use.
def detect_object_image(image_name, model, server, vertical_fov, horizontal_fov):
    nearest_pixel = sys.maxsize
    far_pixel = 0

    answer = get_answer(model, server, "raw_images/" + image_name)

    image = Image.open("raw_images/" + image_name)
    # Convert img to numpy array
    numpy_data = asarray(image)

    # Unpickle pickle file
    infile = open('pickle_files/' + image_name[0:image_name.index('.p')], 'rb')
    distance = pickle.load(infile)
    infile.close()

    # Locates object with bounding boxes.
    if len(answer["bounding-boxes"]) > 0:
        for box in range(len(answer['bounding-boxes'])):
            object_class_name = answer['bounding-boxes'][box]['ObjectClassName']
            bounding_box = answer['bounding-boxes'][box]['coordinates']
            bottom = bounding_box['bottom']
            left = bounding_box['left']
            right = bounding_box['right']
            top = bounding_box['top']
            # Locates the object in the numpy array.
            for i in range(left, right):
                for j in range(top, bottom):
                    if distance[j][i][0] < nearest_pixel and distance[j][i][0] != 0:
                        nearest_pixel = distance[j][i][0]
                    if distance[j][i][0] > far_pixel:
                        far_pixel = distance[j][i][0]

        cv2.rectangle(numpy_data, (right, top), (left, bottom), (255, 0, 0), 2)
        img = Image.fromarray(numpy_data, 'RGB')

        print(far_pixel)
        print(nearest_pixel)

        # Object's depth
        depth = (far_pixel - nearest_pixel) / 10

        # Variable Distance Camera
        # Formulas to calculate height and width of object depending on its distance from
        # the camera, as well as on its intrinsic parameters.
        height_px = bottom - top
        height_obj = nearest_pixel / 10 * (height_px / h_sensor) * math.tan((vertical_fov * math.pi / 180) / 2) * 2

        width_px = right - left
        width_obj = nearest_pixel / 10 * (width_px / w_sensor) * math.tan((horizontal_fov * math.pi / 180) / 2) * 2
        img.save('images/labeled_image.png')
    else:
        nearest_pixel = -1

    if nearest_pixel > 0:
        answer['bounding-boxes'][box]['dimensions'] = {"depth": float("{:.2f}".format(depth)),
                                                       "width": float("{:.2f}".format(width_obj)),
                                                       "height": float("{:.2f}".format(height_obj))}
        answer['bounding-boxes'][box]['distance'] = float("{:.2f}".format(nearest_pixel / 10))

    else:
        print("No objects labeled.")

    return answer
