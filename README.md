# Hemistereo NX Inference API

This is a repository for an object detection inference API using the Hemistereo NX 180 X camera.

It allows you to label an object based on the training of a model from the deeplearning06.muc:4344/ server. Also, it allows you to calculate the distance of the object from the camera, as well as its dimensions: depth, width and height.

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

```shell
sudo docker run -itd -p <docker_host_port>:1234 --restart always hemistereo_inference_api
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

##### /single_shot (POST)

Returns a picture captured by the camera. This is a raw image, hence no objects are labeled yet.

![](/docs/singleshot.gif)

##### /detect (POST)

Performs object detection and labeling on a specific object based on the trained model it is using.

It returns bounding boxes, distance and dimensions: width, depth and height.

![](/docs/detect_object.gif)

##### /detect/save_image (POST)

![](/docs/save_labeled_image.gif)
