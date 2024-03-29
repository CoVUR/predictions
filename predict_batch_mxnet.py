# USAGE
# python predict_batch.py --input logos/images --output output

# import the necessary packages
import numpy as np
import mxnet as mx
from mxnet import autograd, gluon
import gluoncv as gcv
import xml.etree.ElementTree as ET
from xml.dom import minidom
from imutils import paths
import numpy as np
import argparse
import cv2
import os

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
#Sobra
ap.add_argument("-m", "--model", required=True,
	help="path to pre-trained model")
ap.add_argument("-i", "--input", required=True,
	help="path to directory containing input images")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
	help="minimum probability to filter weak detections")
args = vars(ap.parse_args())

# TODO:
# Allow option for --input to be a .txt file OR a directory. Check if
# file, and if so, presume keras-retinanet set of images + labels

##### J. Esto hay que cambiarlo dependiendo de cada problema
classes = ['tinamou',
'red_fox',
'wood_mouse',
'spiny_rat',
'agouti',
'red_brocket_deer',
'bird_spec',
'red_deer',
'european_hare',
'ocelot',
'white_nosed_coati',
'paca',
'collared_peccary',
'red_squirrel',
'common_opossum',
'coiban_agouti',
'wild_boar',
'white_tailed_deer',
'mouflon',
'roe_deer']

net = gcv.model_zoo.get_model('ssd_512_resnet50_v1_custom', classes=classes, pretrained_base=False)
net.load_parameters(args["model"])

imagePaths = list(paths.list_images(args["input"]))


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def generateXML(filename,outputPath,w,h,d,boxes):
    top = ET.Element('annotation')
    childFolder = ET.SubElement(top, 'folder')
    childFolder.text = 'images'
    childFilename = ET.SubElement(top, 'filename')
    childFilename.text = filename[0:filename.rfind(".")]
    childPath = ET.SubElement(top, 'path')
    childPath.text = outputPath + "/" + filename
    childSource = ET.SubElement(top, 'source')
    childDatabase = ET.SubElement(childSource, 'database')
    childDatabase.text = 'Unknown'
    childSize = ET.SubElement(top, 'size')
    childWidth = ET.SubElement(childSize, 'width')
    childWidth.text = str(w)
    childHeight = ET.SubElement(childSize, 'height')
    childHeight.text = str(h)
    childDepth = ET.SubElement(childSize, 'depth')
    childDepth.text = str(d)
    childSegmented = ET.SubElement(top, 'segmented')
    childSegmented.text = str(0)
    #boxes tiene que contener labels
    for (box,score) in boxes:
        # Cambiar categoria por label
        category = box[0]
	# Jonathan - Cambio
        box = box[1]
        (x,y,xmax,ymax) = box
        childObject = ET.SubElement(top, 'object')
        childName = ET.SubElement(childObject, 'name')
        childName.text = category
        childScore = ET.SubElement(childObject, 'confidence')
        childScore.text = str(score.asscalar())
        childPose = ET.SubElement(childObject, 'pose')
        childPose.text = 'Unspecified'
        childTruncated = ET.SubElement(childObject, 'truncated')
        childTruncated.text = '0'
        childDifficult = ET.SubElement(childObject, 'difficult')
        childDifficult.text = '0'
        childBndBox = ET.SubElement(childObject, 'bndbox')
        childXmin = ET.SubElement(childBndBox, 'xmin')
        childXmin.text = str(int(x))
        childYmin = ET.SubElement(childBndBox, 'ymin')
        childYmin.text = str(int(y))
        childXmax = ET.SubElement(childBndBox, 'xmax')
        childXmax.text = str(int(xmax))
        childYmax = ET.SubElement(childBndBox, 'ymax')
        childYmax.text = str(int(ymax))
    return prettify(top)

# loop over the input image paths
for (i, imagePath) in enumerate(imagePaths):
	# load the input image (in BGR order), clone it, and preprocess it
	#print("[INFO] predicting on image {} of {}".format(i + 1,
	#	len(imagePaths)))

	# load the input image (in BGR order), clone it, and preprocess it
	image = cv2.imread(imagePath)
	(hI, wI, d) = image.shape
	

	# detect objects in the input image and correct for the image scale
        # Poner short=512
	# Jonathan - Cambio
	x, image = gcv.data.transforms.presets.ssd.load_test(imagePath,512)
	cid, score, bbox = net(x)
	# Jonathan - Cambio
	(HI, WI, d) = image.shape
	boxes1 = []
        #Añadir cid[0]
	for (cid,box, score) in zip(cid[0],bbox[0], score[0]):
		if score < args["confidence"]:
			continue
                # Añadir label que sera con net.classes[cid]
		# Jonathan - Cambio
		(x,y,xmax,ymax) = box.asnumpy()
		# Jonathan - Cambio
		box = (x*wI/WI,y*hI/HI,xmax*wI/WI,ymax*hI/HI)
		boxes1.append(([net.classes[cid[0].asnumpy()[0].astype('int')],box],score))

	# parse the filename from the input image path, construct the
	# path to the output image, and write the image to disk
	filename = imagePath.split(os.path.sep)[-1]
	#outputPath = os.path.sep.join([args["output"], filename])
	file = open(imagePath[0:imagePath.rfind(".")]+".xml", "w")
	file.write(generateXML(imagePath[0:imagePath.rfind(".")],imagePath,wI, hI, d, boxes1))
	file.close()

	
	#cv2.imwrite(outputPath, output)
