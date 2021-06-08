# Hemistereo NX Inference API

This is a repository for an object detection inference API using the Hemistereo NX 180 X camera.

It allows you to label an object based on the training of a model from a server. Also, it allows you to calculate the distance of the object from the camera, as well as its dimensions: depth, width and height.

## Prerequisites

- Ubuntu 18.04
- Docker CE
- Hemistereo Viewer Software

### Check for prerequisites

To check if you have docker-ce installed:

```shell
docker --version
```

### Install prerequisites

Use the following command to install docker on Ubuntu:

```sh
chmod +x install_prerequisites.sh && source install_prerequisites.sh
```

Install the Hemistereo Viewer Software following the [official docs](https://3dvisionlabs.com/downloads/)

## Build The Docker Image

In order to build the project run the following command from the project's root directory:

```shell
sudo docker build -t hemistereo_inference_api -f docker/Dockerfile .
```

### Behind a proxy

```shell
sudo docker build --build-arg http_proxy='' --build-arg https_proxy='' -t hemistereo_inference_api -f ./docker/Dockerfile .
```

## Run The Docker Container

If you wish to deploy this API using **docker**, go to the API's directory and issue the following command:

### On Ubuntu:

```shell
sudo docker run -itdv $(pwd)/src/raw_images:/app/raw_images -v $(pwd)/src/labeled_images:/app/labeled_images -p <docker_host_port>:1234 --restart always hemistereo_inference_api
```

### On Windows:

```bash
docker run -itdv %cd%\src\raw_images:\app\raw_images -v %cd%\src\labeled_images:\app\labeled_images -p <docker_host_port>:1234 --restart always hemistereo_inference_api
```

*Note that <docker_host_port> can be any unique port of your choice.*

*Also note that the --restart always tag will always re-run the container each time the device reboots.*

To check if the container is running, run the following command:

```shell
sudo docker ps
```

 Now that the container is running correctly, the service will listen to the http requests on the chosen port.

## API Endpoints

To see all available endpoints, open your favorite browser and navigate to:

```http
http://<hemistereo_camera_IP>:<docker_host_port>/docs
```

#### Endpoints Summary

##### /set_camera_settings

Allows the user to set the vertical and horizontal field of view of the camera.

![](/docs/set_camera_settings.gif)

##### /single_shot (POST)

Returns a picture captured by the camera. This is a raw image, hence no objects are labeled yet. Moreover, this endpoint saves the name (which is a datetime stamp) and the distance map of the image in a data.json file for later use.

*Note that there is a watcher.py file that listens to the directory in which the images are being saved. It detects any change made in the directory: so if an image is deleted, its information will be automatically removed from the data.json file.*

![](/docs/singleshot.gif)

##### /single_shot/distance_map (POST)

This endpoint returns and saves the raw image with its distance map.

![](/docs/singleshot_distance.png)

##### /set_threshold (POST)

Allows the user to manually calibrate the camera in terms of textureness threshold.

![](/docs/set_threshold.gif)

##### /detect (POST)

Performs object detection and labeling on a specific object based on the trained model it is using.

It returns bounding boxes, distance and dimensions: width, depth and height.

![](/docs/detect.png)

##### /detect_input (POST)

Allows the user to attach a previously saved raw image (not labeled) in order to detect it, label it and measure it. This endpoint uses the information previously saved in the data.json file while saving the image.

![](/docs/detect_input_image.gif)

##### /detect/save_image (POST)

This endpoint allows the user to detect and save the labeled image.

![](/docs/save_labeled_image.gif)

## Hemistereo Viewer Software Tutorial

In this part, we will explain how to use the Hemistereo Viewer Software in order to calibrate the camera if needed. Although there are methods and endpoints implemented to do that, the change of environment can affect those calibrations and you might want to do that manually.

### Maximum Disparities

The camera does not give accurate values when an object is really close to it. In this case, you can increase the maximum disparities to 256 to solve this issue. But keep in mind that the frame rate will drop. So do not change the value of the latter variable if you need to stream.

![](/docs/max_disp.gif)

### Field of View

In case you want to change the field of view of the camera, you can do that by using the slide bar as shown in the gif.

Note that it is advised to give the matching resolution field of view the same values as in the target camera settings.

![](/docs/field_of_view.gif)

### Textureness Filter Settings

If you are using a smooth surface, on which the light can affect the distance map of your camera, you will need to modify the parameters in the Textureness Settings, which are also modified using a sliding bar.

The threshold value is often changed to filter out any junk values in your distance map which are caused by light reflection or other factors.

Usually, the more the object is far from the camera, the more you increase the threshold value, and vice versa.

![](/docs/textureness_threshold.gif)

There are much more parameters you can change and play around with, but these are the most used ones for camera calibration.

# References

https://rami-naffah.medium.com/how-to-use-a-stereo-camera-for-object-detection-and-measurement-bmw-no-code-ai-4e4319952a3


