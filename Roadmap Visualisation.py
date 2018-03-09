# Roadmap Visaulisation
# Author name: Nathanial Cooper
# Author email: nathanial.cooper AT imperial.ac.uk (preferred), nattiecooper AT gmail.com (alternate)
# Date: 6 July 2017
# Version: 0.4
#-------------------------------------------DESCRIPTION-----------------------------------------------------------
# This program creates a roadmap visualisation of a supply chain network or other similar network
# This script requires: 
# (1) a txt (or csv?) of order number, coordinates and CRS
# This script outputs:
# (1) a layer of all coordinates in the same CRS in order
# (2) a layer of all lines connecting the coordinates
#----------------------------------------------------------------------------------------------------------------------

##Roadmap Visualization=name
##Coordinate_Data_textfile=file
##Map_Save_Folder=folder
##Map_Save_Name=string roadmap

from qgis.core import *
from qgis.utils import *
from qgis.gui import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os.path

locations = open(Coordinate_Data_textfile)
currLine = locations.readline()
pointID,pointX,pointY,originCRS = currLine.split()
mapName = "%s.png" %Map_Save_Name
outfile = os.path.join(Map_Save_Folder,mapName)
pdfName = "%s.pdf" %Map_Save_Name
outPDF = os.path.join(Map_Save_Folder,pdfName)

URIstrP = "Point?crs=EPSG:%s" %originCRS
layerP = QgsVectorLayer(URIstrP,"pointsPath","memory")
oCRS = layerP.crs()
provP = layerP.dataProvider()
provP.addAttributes([QgsField("ID", QVariant.Int), QgsField("Name",QVariant.String)])
layerP.updateFields()
URIstrL = "LineString?crs=EPSG:%s" %originCRS
layerL = QgsVectorLayer(URIstrL,"linePath","memory")
provL = layerL.dataProvider()
pCRS = layerP.crs()

while currLine != "":
    pointID,pointX,pointY,pointCRS = currLine.split()
    pCRS.createFromId(int(pointCRS))
    if pCRS == oCRS:
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPoint(QgsPoint(float(pointX),float(pointY))))
        feat.setAttributes([int(pointID),"a"])
        provP.addFeatures([feat])
    else:
        tform = QgsCoordinateTransform(pCRS,oCRS)
        tmpPoint = tform.transform(QgsPoint(float(pointX),float(pointY)))
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPoint(tmpPoint))
        feat.setAttributes([int(pointID),"a"])
        provP.addFeatures([feat])
    currLine = locations.readline()

layerP.updateExtents()

iter = layerP.getFeatures()
firstPass = True
for feature in iter:
    if firstPass:
        startPoint = feature.geometry().asPoint()
        firstPass = False
    else:
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPolyline([startPoint,feature.geometry().asPoint()]))
        provL.addFeatures([feat])
        startPoint = feature.geometry().asPoint()

symReg = QgsSymbolLayerV2Registry.instance()
metaRegL = symReg.symbolLayerMetadata("SimpleLine")
symLayL = QgsSymbolV2.defaultSymbol(layerL.geometryType())
metaL = metaRegL.createSymbolLayer({'width':'1','color':'0,0,0'})
symLayL.deleteSymbolLayer(0)
symLayL.appendSymbolLayer(metaL)
symRendL = QgsSingleSymbolRendererV2(symLayL)
layerL.setRendererV2(symRendL)

metaRegP = symReg.symbolLayerMetadata("SimpleMarker")
symLayP = QgsSymbolV2.defaultSymbol(layerP.geometryType())
metaP = metaRegP.createSymbolLayer({'size':'3','color':'0,0,0'})
symLayP.deleteSymbolLayer(0)
symLayP.appendSymbolLayer(metaP)
symRendP = QgsSingleSymbolRendererV2(symLayP)
layerP.setRendererV2(symRendP)

QgsMapLayerRegistry.instance().addMapLayer(layerP)
QgsMapLayerRegistry.instance().addMapLayer(layerL)
#iface.mapCanvas().refresh()

# -------------- Simplest --------------------
#canvas = iface.mapCanvas()
#extent = layerP.extent()
#canvas.setExtent(extent)
#canvas.saveAsImage(outfile,None,"TIF")

#-------------- Using QImage -------------------
#visImg = QImage(QSize(1600,1200),QImage.Format_ARGB32_Premultiplied)

# Background color
#visColor = QColor(255,255,255)
#visImg.fill(visColor.rgb())

# Create Painter
#visPainter = QPainter()
#visPainter.begin(visImg)
#visPainter.setRenderHint(QPainter.Antialiasing)
#visRender = QgsMapRenderer()

# set rendering window
#layerList = []
#for layer in QgsMapLayerRegistry.instance().mapLayers().values():
#    layerList.append(layer.id())

#figure out color thickness and transparency for these
#print layerList
#layerList.reverse()
#print layerList
#visRender.setLayerSet(layerList)

# set viewing window
#visExtent = QgsRectangle(visRender.fullExtent())
#visExtent = QgsRectangle(layerP.extent())
#visExtent.scale(1.25)
#visRender.setExtent(visExtent)
#visRender.setOutputSize(visImg.size(),visImg.logicalDpiX())
#visRender.render(visPainter)
#visPainter.end()
#visImg.save(outfile,"png")

def render_image():
    size=QSize(1920,1080)
    #size = iface.mapCanvas().size()
    image = QImage(size, QImage.Format_ARGB32_Premultiplied)

    painter = QPainter(image)
    settings = iface.mapCanvas().mapSettings()

    # You can fine tune the settings here for different
    # dpi, extent, antialiasing...
    # Just make sure the size of the target image matches
    painter.setRenderHint(QPainter.Antialiasing)
    bound = layerP.extent()
    bound.scale(1.25)
    settings.setExtent(bound)
    settings.setOutputSize(image.size())
    dpm = 300/0.0254
    image.setDotsPerMeterX(dpm)
    image.setDotsPerMeterY(dpm)
    
    # You can also add additional layers. In the case here,
    # this helps to add layers that haven't been added to the
    # canvas yet
    
    layers = settings.layers()
    #settings.setLayers([layerP.id(), layerL.id()] + layers)
    settings.setLayers(layers)

    job = QgsMapRendererCustomPainterJob(settings, painter)
    job.renderSynchronously()
    painter.end()
    image.save(outfile,"PNG")

# If you don't want to add additional layers manually to the
# mapSettings() you can also do this:
# Give QGIS give a tiny bit of time to bring the layers from 
# the registry to the canvas (the 10 ms do not matter, the important
# part is that it's posted to the event loop)

QTimer.singleShot(10, render_image)
#render_image()
