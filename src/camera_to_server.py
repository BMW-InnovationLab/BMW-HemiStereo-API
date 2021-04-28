import os

from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.responses import StreamingResponse
import uvicorn
import io
import shutil
import datetime
from watcher import *
import threading
import time
import pickle

app = FastAPI(title="Hemistereo API", description="<b>API for performing object detection using Hemistereo NX 180 X "
                                                  "camera</b></br></br>"
                                                  "<b>Contact the developer:</b></br>"
                                                  "<b>Rami Naffah: <a href='mailto:rami.naffah@lau.edu'>rami.naffah"
                                                  "@lau.edu</a></b></br> "
                                                  "<b>")


class CameraParameters(BaseModel):
    cam_ip: str
    model: str
    server: str
    vertical_fov: float
    horizontal_fov: float


class Calibration(BaseModel):
    cam_ip: str
    model: str
    server: str


class ShotParameters(BaseModel):
    cam_ip: str
    vertical_fov: float
    horizontal_fov: float


def watch():
    w = Watcher()
    time.sleep(2)
    w.run("raw_images")


@app.post("/set_camera_settings")
def set_camera_settings(item: ShotParameters):
    ctx = Context(appname="stereo", server=item.cam_ip, port="8888")
    ctx.setProperty("stereo_target_camera_enabled", bool(1))

    # Set Camera Model to Pinhole
    ctx.setProperty("stereo_target_camera_model", 4)

    # Set Camera Field of View
    ctx.setProperty("stereo_target_image_fov_h", numpy.single(item.horizontal_fov))
    ctx.setProperty("stereo_target_image_fov_v", numpy.single(item.vertical_fov))
    ctx.setProperty("stereo_matching_image_fov_v", numpy.single(item.vertical_fov))
    ctx.setProperty("stereo_matching_image_fov_h", numpy.single(item.horizontal_fov))


@app.post("/single_shot")
def see_raw_image(cam_ip: str = Form(...)):
    ctx = single_shot_save(cam_ip)
    im = ctx.readTopic("image")
    np = unpackMessageToNumpy(im.data)
    msg = ctx.readTopic("distance")

    # 3D distance map to list
    # distance = unpackMessageToNumpy(msg.data).tolist()
    distance = unpackMessageToNumpy(msg.data)
    # point_cloud = unpackMessageToNumpy(ctx.readTopic("pointcloud").data).tolist()

    image_path = "raw_images/{}.png".format(datetime.datetime.now())
    i = Image.fromarray(np)
    i.save(image_path, 'PNG')

    # Serialize Distance Map into pickle file
    image_name = get_image_name(image_path)
    image_name = image_name[0:image_name.index('.p')]
    filename = 'pickle_files/' + image_name
    outfile = open(filename, 'wb')
    pickle.dump(distance, outfile)
    outfile.close()
    return FileResponse(image_path)


@app.post("/single_shot/distance_map")
def see_image_with_distance_map(cam_ip: str = Form(...)):
    ctx = single_shot_save(cam_ip)
    msg = ctx.readTopic("distance")
    rgb = unpackMessageToNumpy(msg.data)
    rgb = formatNumpyToRGB(rgb)
    i = Image.fromarray(rgb)
    i.save('images/distance_map.png')
    im1 = cv2.imread('images/raw_image.png')
    im2 = cv2.imread('images/distance_map.png')
    im_h = cv2.hconcat([im1, im2])
    cv2.imwrite('images/raw+dist.png', im_h)
    return FileResponse('images/raw+dist.png')


@app.post("/set_threshold")
def set_threshold(item: Calibration):
    return calibrate(item.cam_ip, item.model, item.server)


@app.post("/detect")
def detect_object(item: CameraParameters):
    # open('raw_image.png', server).write(r.content)
    return detect(item.model, item.server, item.cam_ip, item.vertical_fov,
                  item.horizontal_fov)


@app.post("/detect_input")
def detect_object_from_input_image(image: UploadFile = File(...), model=Form(...), server=Form(...)):
    with open("images/test.png", "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    return detect_object_image(image.filename, model, server)


@app.post("/detect/save_image")
def save_labeled_image(item: CameraParameters):
    answer = detect(item.model, item.server, item.cam_ip, item.vertical_fov,
                    item.horizontal_fov)
    if len(answer["bounding-boxes"]) > 0:
        with open("images/labeled_image.png", "rb") as f:
            b = bytearray(f.read())
            img = Image.open("images/labeled_image.png")
            img.save('labeled_images/{}.png'.format(datetime.datetime.now()), 'PNG')
        return StreamingResponse(io.BytesIO(b), media_type="image/png")


if __name__ == '__main__':
    t1 = threading.Thread(target=watch)
    t1.start()
    uvicorn.run("camera_to_server:app", reload=True)
