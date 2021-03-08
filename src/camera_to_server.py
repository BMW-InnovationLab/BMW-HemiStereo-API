from fastapi import FastAPI, Form
from fastapi.responses import FileResponse
from starlette.responses import StreamingResponse
import uvicorn
from methods import *
import io

# model_name = "TestCam2-Training1"
# server = "http://deeplearning06.muc:4344/"

app = FastAPI(title="Hemistereo API", description="<b>API for performing object detection using Hemistereo NX 180 X "
                                                  "camera</b></br></br>"
                                                  "<b>Contact the developer:</b></br>"
                                                  "<b>Rami Naffah: <a href='mailto:rami.naffah@lau.edu'>rami.naffah"
                                                  "@lau.edu</a></b></br> "
                                                  "<b>")


@app.post("/single_shot")
def see_raw_image(cam_ip: str = Form(...)):
    ctx = single_shot(cam_ip)
    # i.save('/home/{}/Downloads/images/{}.png'.format(user, datetime.datetime.now()))
    return FileResponse('images/raw_image.png')


@app.post("/single_shot/distance_map")
def see_raw_image(model: str = Form(...), server: str = Form(...), cam_ip: str = Form(...)):
    ctx = single_shot(cam_ip)
    msg = ctx.readTopic("distance")
    rgb = unpackMessageToNumpy(msg.data)
    rgb = formatNumpyToRGB(rgb)
    i = Image.fromarray(rgb)
    i.save('images/distance_map.png')
    # with open("images/raw_image.png", "rb") as im1:
    #     b1 = bytearray(im1.read())
    # with open("images/distance_map.png", "rb") as im2:
    #     b2 = bytearray(im2.read())
    im1 = cv2.imread('images/raw_image.png')
    im2 = cv2.imread('images/distance_map.png')
    im_h = cv2.hconcat([im1, im2])
    cv2.imwrite('images/raw+dist.png', im_h)
    # i.save('/home/{}/Downloads/images/{}.png'.format(user, datetime.datetime.now()))
    # return StreamingResponse(io.BytesIO(im_h.tobytes()), media_type="image/png")
    return FileResponse('images/raw+dist.png')
    # , detect(model, server, cam_ip)


@app.post("/set_threshold")
def set_threshold(cam_ip=Form(...), model=Form(...), server=Form(...)):
    return compute_threshold(cam_ip, model, server)


@app.post("/detect")
def detect_object(model: str = Form(...), server: str = Form(...), cam_ip: str = Form(...)):
    # open('raw_image.png', server).write(r.content)
    return detect(model, server, cam_ip)


@app.post("/detect/save_image")
def save_labeled_image(model: str = Form(...), server: str = Form(...), cam_ip: str = Form(...)):
    answer = detect(model, server, cam_ip)
    if len(answer["bounding-boxes"]) > 0:
        with open("images/labeled_image.png", "rb") as f:
            b = bytearray(f.read())
        return StreamingResponse(io.BytesIO(b), media_type="image/png")


if __name__ == '__main__':
    uvicorn.run("camera_to_server:app", reload=True)
