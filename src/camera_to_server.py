from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import FileResponse
from starlette.responses import StreamingResponse
import uvicorn
from methods import *
import io
import shutil
import getpass
from watcher import *
import threading
import time

# model_name = "TestCam2-Training1"
# server = "http://deeplearning06.muc:4344/"

app = FastAPI(title="Hemistereo API", description="<b>API for performing object detection using Hemistereo NX 180 X "
                                                  "camera</b></br></br>"
                                                  "<b>Contact the developer:</b></br>"
                                                  "<b>Rami Naffah: <a href='mailto:rami.naffah@lau.edu'>rami.naffah"
                                                  "@lau.edu</a></b></br> "
                                                  "<b>")


def watch():
    w = Watcher()
    time.sleep(2)
    # w.run("/home/maria/Downloads/images")
    w.run("raw_images")


@app.post("/single_shot")
def see_raw_image(cam_ip: str = Form(...)):
    ctx = single_shot_save(cam_ip)
    im = ctx.readTopic("image")
    np = unpackMessageToNumpy(im.data)
    msg = ctx.readTopic("distance")
    # 3D distance map to list
    distance = unpackMessageToNumpy(msg.data).tolist()

    image_path = "raw_images/{}.png".format(datetime.datetime.now())
    i = Image.fromarray(np)
    i.save(image_path, 'PNG')
    data.append({'name': get_image_name(image_path), 'distance_map': distance})
    with open('data.json', 'w') as outfile:
        json.dump(data, outfile)
    # i.save('/home/{}/Downloads/images/{}.png'.format(user, datetime.datetime.now()))
    return FileResponse(image_path)


@app.post("/single_shot/distance_map")
def see_raw_image(model: str = Form(...), server: str = Form(...), cam_ip: str = Form(...), path: str = Form(...)):
    ctx = single_shot(cam_ip, path)
    msg = ctx.readTopic("distance")
    rgb = unpackMessageToNumpy(msg.data)
    rgb = formatNumpyToRGB(rgb)
    i = Image.fromarray(rgb)
    i.save('images/distance_map.png')
    im1 = cv2.imread('images/raw_image.png')
    im2 = cv2.imread('images/distance_map.png')
    im_h = cv2.hconcat([im1, im2])
    cv2.imwrite('images/raw+dist.png', im_h)
    # return StreamingResponse(io.BytesIO(im_h.tobytes()), media_type="image/png")
    return FileResponse('images/raw+dist.png')


@app.post("/set_threshold")
def set_threshold(cam_ip=Form(...), model=Form(...), server=Form(...)):
    return compute_threshold(cam_ip, model, server)


@app.post("/detect")
def detect_object(model: str = Form(...), server: str = Form(...), cam_ip: str = Form(...)):
    # open('raw_image.png', server).write(r.content)
    return detect(model, server, cam_ip)


@app.post("/detect_input")
def detect_object_from_input_image(image: UploadFile = File(...), model=Form(...), server=Form(...)):
    with open("images/test.png", "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    return detect_object_image(image.filename, model, server)


@app.post("/detect/save_image")
def save_labeled_image(model: str = Form(...), server: str = Form(...), cam_ip: str = Form(...)):
    answer = detect(model, server, cam_ip)
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
