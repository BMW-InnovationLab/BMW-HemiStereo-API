import cv2
import numpy
import ipycanvas
import pyntcloud
import pandas

def formatNumpyToRGB( np, equalize_histogram=True, color_map="jet" ):
    if np.shape[-1] == 1:
        np = np.astype(numpy.float16)
        np[np == numpy.inf] = 0
        np = np * 256 / np.max()
        np = np.astype(numpy.uint8)
        if equalize_histogram:
            np = cv2.equalizeHist(np)
        if color_map == "jet":
            np = cv2.applyColorMap(np, cv2.COLORMAP_JET)
        elif color_map == "winter":
            np = cv2.applyColorMap(np, cv2.COLORMAP_WINTER)
        elif color_map == "bone":
            np = cv2.applyColorMap(np, cv2.COLORMAP_BONE)
        elif color_map == "ocean":
            np = cv2.applyColorMap(np, cv2.COLORMAP_OCEAN)
        elif color_map == "cool":
            np = cv2.applyColorMap(np, cv2.COLORMAP_COOL)
        elif color_map == "hot":
            np = cv2.applyColorMap(np, cv2.COLORMAP_HOT)
        elif color_map == "rainbow":
            np = cv2.applyColorMap(np, cv2.COLORMAP_RAINBOW)
        else:
            print( "color_map '{}' not supported, falling back to jet".format( color_map ))
            np = cv2.applyColorMap(np, cv2.COLORMAP_JET)
    return np

def formatNumpyToPointCloud( pyc, image = None, filter_nan=True, max_dist=None, scale=0.01, every=10 ):
    length = pyc.shape[0] * pyc.shape[1]
    pyc = pyc.reshape( length, 3 )
    if isinstance( image, numpy.ndarray ):
        if len(image.shape) <= 2 or image.shape[2] == 1:
            raise Exception( "only rgb images may be used for coloization of pcl's!" )
        if image.size != pyc.size:
            raise Exception( "image for colorization and pointcloud must be of same size!" )
        imageMod = image.reshape(image.shape[0]*image.shape[1],3)
        pyc = numpy.column_stack((pyc, imageMod))
    if filter_nan:
        pyc = pyc[~numpy.isnan(pyc).any(axis=1)]
    if max_dist:
        pyc = pyc[((pyc[:,0]**2+pyc[:,1]**2+pyc[:,2]**2<10000**2))]
    if every:
        pyc = pyc[::every]
    if scale and isinstance( image, numpy.ndarray ):
        pyc = pyc * (scale,scale,scale,1,1,1)
    elif scale:
        pyc = pyc * scale
    return pyc

def rotateCounterClockWise( image ):
    return cv2.rotate( image, cv2.ROTATE_90_COUNTERCLOCKWISE )

def rotateClockWise( image ):
    return cv2.rotate( image, cv2.ROTATE_90_CLOCKWISE )

def plotRGB( image, canvas=None ):
    image = image.squeeze()
    height, width= image.shape[:2]
    if not canvas:
        canvas = ipycanvas.Canvas(width=width,height=height)
        display( canvas )
    with ipycanvas.hold_canvas( canvas ):
        canvas.put_image_data(image)
    return canvas

def plotPCL( pyc ):
    if pyc.shape[1] == 3:
        points = pandas.DataFrame( pyc, columns=["x", "y", "z"] )
        pcl = pyntcloud.PyntCloud(points)
        return pcl.plot( mesh=True, backend="threejs"  )
    else:
        points = pandas.DataFrame( pyc, columns=["x", "y", "z", "red", "green", "blue"] )
        pcl = pyntcloud.PyntCloud(points)
        return pcl.plot( mesh=True, backend="threejs" )
