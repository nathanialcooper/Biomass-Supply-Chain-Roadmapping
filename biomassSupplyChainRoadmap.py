# Biomass Supply Chain Roadmap
# Author name: Nathanial Cooper
# Author email: nathanial.cooper AT imperial.ac.uk (preferred), nattiecooper AT gmail.com (alternate)
# Date: 24 July 2018
# Version: 1.0
#-------------------------------------------DESCRIPTION-----------------------------------------------------------
# This program pulls refinery locations out of GAMS .lst files and adds a point layer to that location. It
# also tracks the pathways that user indicated materials take in the optimisation.
# This script requires: 
# 1) the lst from GAMS with refinery locations listed
# 2) vector grid which corresponds to the locations used in the GAMS analysis
# 3) which field of the vector grid corresponds to the ID number
# 4) name of the variable for presence of refinery
# 5) name of the variable for flow rate of material
# 6) cell ID for demand centers 
# 7) names of products, separated by commas
# 8) names of transportaion methods, separated by commas
# This script outputs:
# 1) a separate point layer for each refinery type with locations
# 2) a separate line layer with arrows directing the flow of indicated materials for each material
#----------------------------------------------------------------------------------------------------------------------

# Inputs
##RENESENG Biomass Supply Chain Roadmap=name
##GAMS_lst_output=file
##Reference_Grid=vector polygon
##ID_Field=field Reference_Grid
##Name_of_Refinery_Presence_Variable_in_locations_file=string X
##Name_of_Flow_Rate_Variable_in_locations_file=string Q
##Locations_of_Demand_Centers_separate_values_by_commas=string 69,89
##Types_of_Materials_separate_values_by_commas=string winter_wheat_straw,winter_barley_straw,corn_stover,ethanol,power,xylitol,PU,PF_resin
##Types_of_Transportation_Methods_separate_values_by_commas=string truck

# Relevant package importation
from qgis.core import *
from PyQt4.QtCore import *
import colorsys

# Used as a key for sorting the cells in order of ID number
def getID(f):
    return f[ID_Field]

# Parse various inputs for use
countryGrid = processing.getObject(Reference_Grid)
demCenters = [int(s) for s in Locations_of_Demand_Centers_separate_values_by_commas.split(',')]
prods = Types_of_Materials_separate_values_by_commas.split(',')
transMeth = Types_of_Transportation_Methods_separate_values_by_commas.split(',')

# Prepare the GAMS file and determine the starting sequences
fxdWidth = 12
locationFile = open(GAMS_lst_output)
startLineASCII = "VARIABLE %s.L" % Name_of_Refinery_Presence_Variable_in_locations_file
startLine = startLineASCII.encode("utf8")
startLineFlowASCII = "VARIABLE %s.L" % Name_of_Flow_Rate_Variable_in_locations_file
startLineFlow = startLineFlowASCII.encode("utf8")

# initialize the empty matrices for later use
allLocs = []
refineries = []
sourceCells = []
for i in prods:
    sourceCells.append(str(i))
    sourceCells.append([])
count = 0
readFlag = 0
startLoc = 0
currProd = []

# Arrow Scaling values
arrowMax = 3
arrowMin = 0.5

# process the .lst file: (1) add refinery locations to list and (2) add flow between cells to list
for line in locationFile:
    if (readFlag and ("----" in line)): # stop reading when get to next variable
        print "End before line: %s" % line
        readFlag = 0
        
    elif (readFlag == 1): # for reading refinery locations
        numSlices = len(line)/fxdWidth
        splitLine = []
        for i in range(0,numSlices): # construct a list of all refinery types and locations
            oneSlice = line[(fxdWidth*i):(fxdWidth*(i+1))]
            splitLine.append(oneSlice.strip())
    
        if not splitLine: # if the line was empty, do nothing
            count = count + 1
        elif ((not splitLine[0]) or (splitLine[0] == '+')): # these are the lines that list the refinery cell numbers
            allLocs = splitLine
        else: # looks at one refinery type
            if (splitLine[0] in refineries): # if that refinery is already listed, get the position in the list
                locsPos = refineries.index(splitLine[0]) + 1
            else: # otherwise append it to the end
                refineries.append(splitLine[0])
                refineries.append([])
                locsPos = -1
        
            enumList = [i for i,x in enumerate(splitLine) if x == '1.000']
            refineries[locsPos] = refineries[locsPos] + [int(allLocs[i]) for i in enumList]
    
    elif (readFlag == 2): # for reading transport to demand centers
        splitLine = line.split()
        if not splitLine: # if the line was empty, do nothing
            count = count + 1
        elif ('INDEX' in splitLine):
            startLoc = 0
            if [i for i in prods if i in splitLine]:
                startLoc = int(splitLine[-1])
                currProd = [i for i in prods if i in splitLine]
        elif (startLoc and [i for i in transMeth if i in splitLine[0]]):
            endLoc = splitLine[0].split('.')
            transAmts = [float(i) for i in splitLine[1:]]
            avgVal = sum(transAmts)/12.0
            sourcePos = sourceCells.index(str(currProd[0]))+1
            sourceCells[sourcePos].append([startLoc, int(endLoc[-1]), avgVal])
    
    elif (startLine in line): # start paying attention when we get to the start of the refinery locations
        print "Start after line: %s" % line
        readFlag = 1
    elif ((startLineFlow in line) and ("----" in line)): # start paying attention when we get to the product flows
        print "Start flow after line: %s" % line
        readFlag = 2

# generate colors for even distribution
numColors = 1 + len(refineries)/2
HSV_vals = [(i*1.0/numColors, 1, 1) for i in range(numColors)]
RGB_vals_frac = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_vals)

# create centroid layer
tmpCentroidLayer = processing.runalg('qgis:polygoncentroids',countryGrid,None)
centroidLayer = QgsVectorLayer(tmpCentroidLayer['OUTPUT_LAYER'],"Centroids","ogr")

# create the defining information for the point and line layers
fieldNum = centroidLayer.fieldNameIndex(ID_Field)
defPtInfo = "Point?crs=%s" % centroidLayer.crs().authid()
defLnInfo = "LineString?crs=%s" % centroidLayer.crs().authid()
listPointLayers = []
listLineLayers = []

# add all centroids to the list in order for ease of calling
centroidsInOrder = sorted(centroidLayer.getFeatures(),key = getID)

# Make point Layer for Demand Centers, add the demand centers as features, set the color
tmpLayer = QgsVectorLayer(defPtInfo,'Demand Centers',"memory")
dataProv = tmpLayer.dataProvider()
dataProv.addAttributes(centroidLayer.dataProvider().fields())
tmpLayer.updateFields()

for i in demCenters:
    outElem = QgsFeature()
    outElem.setGeometry(centroidsInOrder[int(i)-1].geometry())
    outElem.setAttributes(centroidsInOrder[int(i)-1].attributes())
    dataProv.addFeatures([outElem])
tmpLayer.updateExtents()

pointColor = '%d, %d, %d, 255' % (int(255*RGB_vals_frac[0][0]), int(255*RGB_vals_frac[0][1]), int(255*RGB_vals_frac[0][2]))
symbol = QgsMarkerSymbolV2.createSimple({'name':'square','size':'3','color':pointColor})
tmpLayer.rendererV2().setSymbol(symbol)
QgsMapLayerRegistry.instance().addMapLayer(tmpLayer)
listPointLayers.append(tmpLayer)

# Make Point Layers for each refinery type
for i in range(0,len(refineries)/2):
    tmpLayer = QgsVectorLayer(defPtInfo,refineries[2*i],"memory")
    dataProv = tmpLayer.dataProvider()
    dataProv.addAttributes(centroidLayer.dataProvider().fields())
    tmpLayer.updateFields()
    
    # add the refinery locations as features to the point layers
    for j in refineries[2*i+1]:
        outElem = QgsFeature()
        outElem.setGeometry(centroidsInOrder[int(j)-1].geometry())
        outElem.setAttributes(centroidsInOrder[int(j)-1].attributes())
        dataProv.addFeatures([outElem])
    
    # set the color of each point layer
    tmpLayer.updateExtents()
    pointColor = '%d, %d, %d, 255' % (int(255*RGB_vals_frac[i+1][0]), int(255*RGB_vals_frac[i+1][1]), int(255*RGB_vals_frac[i+1][2]))
    symbol = QgsMarkerSymbolV2.createSimple({'name':'circle','size':'3','color':pointColor})
    tmpLayer.rendererV2().setSymbol(symbol)
    QgsMapLayerRegistry.instance().addMapLayer(tmpLayer)
    listPointLayers.append(tmpLayer)

# generate colors for even distribution
numColors = len(sourceCells)/2
HSV_vals = [(i*1.0/numColors, 1, 1) for i in range(numColors)]
RGB_vals_frac = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_vals)

# create line layer for each material
for i in range(len(sourceCells)/2):
    tmpLayer = QgsVectorLayer(defLnInfo,sourceCells[2*i],"memory")
    dataProv = tmpLayer.dataProvider()
    dataProv.addAttributes([QgsField('AvgTrnsAmt', QVariant.Double),QgsField('ArrowScale',QVariant.Double)]) 
    tmpLayer.updateFields()
    
    # create the start and end points of the line, then create the line
    for j in sourceCells[2*i+1]:
        strtPt = QgsFeature()
        strtPt.setGeometry(centroidsInOrder[j[0]-1].geometry())
        strtPt.setAttributes(centroidsInOrder[j[0]-1].attributes())
        
        endPt = QgsFeature()
        endPt.setGeometry(centroidsInOrder[j[1]-1].geometry())
        endPt.setAttributes(centroidsInOrder[j[1]-1].attributes())
        
        tmpLine = QgsFeature()
        tmpLine.setGeometry(QgsGeometry.fromPolyline([strtPt.geometry().asPoint(),endPt.geometry().asPoint()]))
        tmpLine.setAttributes([j[2],0])
        dataProv.addFeatures([tmpLine])
        tmpLayer.updateExtents()
    
    # calculate the relative arrow size for all arrows in a layer
    iter = tmpLayer.getFeatures()
    tmpLayer.startEditing()
    dataMax = tmpLayer.maximumValue(0)
    dataMin = tmpLayer.minimumValue(0)
    m = (arrowMin-arrowMax)/(dataMin-dataMax)
    b = (arrowMax*dataMin-arrowMin*dataMax)/(dataMin-dataMax)
    for feat in iter:
        feat[1] = m*feat[0]+b
        tmpLayer.updateFeature(feat)
    tmpLayer.commitChanges()
    
    # Set the arrow color and arrow size, for all arrows
    pointColor = '%d, %d, %d, 255' % (int(255*RGB_vals_frac[i][0]), int(255*RGB_vals_frac[i][1]), int(255*RGB_vals_frac[i][2]))
    metaL = QgsSymbolLayerV2Registry.instance().symbolLayerMetadata("ArrowLine").createSymbolLayer({'color':pointColor})
    metaL.setDataDefinedProperty('arrow_start_width','"ArrowScale"*1.0')
    metaL.setDataDefinedProperty('arrow_width','"ArrowScale"*1.0')
    metaL.setDataDefinedProperty('head_length','"ArrowScale"*1.6')
    metaL.setDataDefinedProperty('head_thickness','"ArrowScale"*1.6')
    symLayL = QgsSymbolV2.defaultSymbol(tmpLayer.geometryType())
    symLayL.deleteSymbolLayer(0)
    symLayL.appendSymbolLayer(metaL)
    symRendL = QgsSingleSymbolRendererV2(symLayL)
    tmpLayer.setRendererV2(symRendL)
    QgsMapLayerRegistry.instance().addMapLayer(tmpLayer)
