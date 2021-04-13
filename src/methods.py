from hemistereo import *
import pycurl
from PIL import Image
import cv2
from io import BytesIO
import ast
import getpass
from numpy import *
import sys
import json

from src.pythonsdk.hemistereo import unpackMessageToMeta, unpackMessageToMessageMap

user = getpass.getuser()
h_sensor = 768
w_sensor = 1024
theta_d_max = 1.74532925199432953355938

field_of_view_h = 140
field_of_view_v = 140

fov_h_rad = field_of_view_h * math.pi / 180
fov_v_rad = field_of_view_v * math.pi / 180

data = []


# Function to get the name of the image from its path
def get_image_name(image_path):
    if image_path[0] == "/":
        arr = image_path.split('/')
    else:
        arr = image_path.split('\\')
    return arr[-1]


# Still need to set all camera settings.
def single_shot_save(cam_ip):
    numpy.set_printoptions(threshold=sys.maxsize)
    ctx = Context(appname="stereo", server=cam_ip, port="8888")
    ctx.setProperty("stereo_target_camera_enabled", bool(1))

    # Set Camera Model to Pinhole
    ctx.setProperty("stereo_target_camera_model", 4)
    msg = ctx.readTopic("image")

    # Unpacking distance map to numpy array
    # distance = unpackMessageToNumpy(msg1.data)
    # Reshaping the distance map to 2D
    # distance_reshaped = distance.reshape(distance.shape[0], -1)
    # 2D distance map to sparse matrix
    # distance_sparse = sparse.csr_matrix(distance_reshaped)

    np = unpackMessageToNumpy(msg.data)
    i = Image.fromarray(np)
    i.save('images/raw_image.png')

    message = ctx.readTopic("stereo_frame")
    mmap = unpackMessageToMessageMap(message)
    meta = unpackMessageToMeta(mmap["metadata"])
    print(meta)
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


def detect(model, server, cam_ip):
    # Detect Object
    ctx = single_shot_save(cam_ip)
    msg = ctx.readTopic("image")
    nump = unpackMessageToNumpy(msg.data)
    nearest_pixel = sys.maxsize
    far_pixel = 0
    depth = 0
    print('Sending image to api with specified model')
    answer = get_answer(model, server, 'images/raw_image.png')
    message = ctx.readTopic("distance")
    distance = unpackMessageToNumpy(message.data)

    # define coordinates of bounding box vertices around detected object
    if len(answer["bounding-boxes"]) > 0:
        for box in range(len(answer['bounding-boxes'])):
            object_class_name = answer['bounding-boxes'][box]['ObjectClassName']
            bounding_box = answer['bounding-boxes'][box]['coordinates']
            bottom = bounding_box['bottom']
            left = bounding_box['left']
            right = bounding_box['right']
            top = bounding_box['top']
            # Locate labeled object in the numpy array
            for i in range(left, right):
                for j in range(top, bottom):
                    if distance[j][i] < nearest_pixel and distance[j][i] != 0:
                        nearest_pixel = distance[j][i][0]
                    if distance[j][i] > far_pixel:
                        far_pixel = distance[j][i][0]
            # Draw Bounding Box
            cv2.rectangle(nump, (right, top), (left, bottom), (255, 0, 0), 2)
            img = Image.fromarray(nump, 'RGB')
            # Object's depth
            depth = (far_pixel - nearest_pixel) / 10
            print("field of view v: " + str(ctx.getProperty("stereo_matching_image_fov_v")))

            # Variable Distance Camera
            # Formulas to calculate height and width of object depending on its distance from
            # the camera, as well as on its intrinsic parameters.
            height_px = bottom - top
            height_obj = nearest_pixel / 10 * (height_px / h_sensor) * math.tan(fov_v_rad / 2) * 2

            width_px = right - left
            width_obj = nearest_pixel / 10 * (width_px / w_sensor) * math.tan(fov_h_rad / 2) * 2

            img.save('images/labeled_image.png')

        #     if "labeled_images" not in os.listdir('/home/{}/Downloads/'.format(user)):
        #         os.mkdir('/home/{}/Downloads/labeled_images'.format(user))
        # img.save(path + '{}.png'.format(datetime.datetime.now()), 'PNG')
    else:
        nearest_pixel = -1

    if nearest_pixel > 0:
        answer['bounding-boxes'][box]['dimensions'] = {"depth": depth, "width": float("{:.2f}".format(width_obj)),
                                                       "height": float("{:.2f}".format(height_obj))}
        answer['bounding-boxes'][box]['distance'] = float(nearest_pixel / 10)

    else:
        print("No objects labeled.")

    return answer


# Still needs fixing!!
# def compute_threshold(cam_ip):
#     distance, ctx = calculate_distance(model, server, cam_ip)
#     # Must do linear regression model. This formula does not always stand!!
#     textureness = 0.271 * (distance / 10) + 9.52
#     ctx.setProperty("stereo_textureness_filter_average_textureness", np.float32(textureness))
#     return textureness


# Detect and label input image
def detect_object_image(image_name, model, server):
    nearest_pixel = sys.maxsize
    far_pixel = 0

    answer = get_answer(model, server, "images/test.png")

    image = Image.open("images/test.png")
    # Convert img to numpy array
    numpy_data = asarray(image)

    loaded_distance = []

    # Retrieving data from file
    with open('data.json', 'r') as outfile:
        read_list = json.load(outfile)
        for element in read_list:
            if element['name'] == image_name:
                loaded_distance = element['distance_map']

    # This loaded distance array is a list, therefore
    # we need to convert it to a numpy array
    if len(loaded_distance) != 0:
        load_numpy_distance = numpy.array(loaded_distance)
        load_numpy_distance = load_numpy_distance.reshape(load_numpy_distance.shape[0], load_numpy_distance.shape[1], 1)
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
                    if load_numpy_distance[j][i][0] < nearest_pixel and load_numpy_distance[j][i][0] != 0:
                        nearest_pixel = load_numpy_distance[j][i][0]
                    if load_numpy_distance[j][i][0] > far_pixel:
                        far_pixel = load_numpy_distance[j][i][0]

        cv2.rectangle(numpy_data, (right, top), (left, bottom), (255, 0, 0), 2)
        img = Image.fromarray(numpy_data, 'RGB')
        # Object's depth
        depth = (far_pixel - nearest_pixel) / 10

        # Variable Distance Camera
        # Formulas to calculate height and width of object depending on its distance from
        # the camera, as well as on its intrinsic parameters.
        height_px = bottom - top
        height_obj = nearest_pixel / 10 * (height_px / h_sensor) * math.tan(fov_v_rad / 2) * 2

        width_px = right - left
        width_obj = nearest_pixel / 10 * (width_px / w_sensor) * math.tan(fov_h_rad / 2) * 2

        img.save('images/labeled_image.png')
    else:
        nearest_pixel = -1

    if nearest_pixel > 0:
        answer['bounding-boxes'][box]['dimensions'] = {"depth": depth, "width": float("{:.2f}".format(width_obj)),
                                                       "height": float("{:.2f}".format(height_obj))}
        answer['bounding-boxes'][box]['distance'] = float(nearest_pixel / 10)

    else:
        print("No objects labeled.")

    return answer
