# Biomass-Supply-Chain-Roadmapping

This work is covered by a GNU GPL v3.0, as provided in this repository (titled 'LICENSE').

This work was produced as a part of the Renewable Systems Engineering (RENESENG) grant, as funded by the Research Executive Agency of the Seventh Framework Programme of the European Union, as a Marie Curie Initial Training Network (FP7-PEOPLE-2013-ITN), with grant number 607415.

This project is for use with QGIS, written and tested using version 2.18.7 (I have not tested other versions, but hopefully will in the future). The work is written for python 2.7 (I have not tested it for compatibility with python 3, but again, hopefully will in the future).

This code is meant to assist in visualising the results of a Biomass Supply Chain Optimisation.

To use, either 1) save the code file and select the "Add script from file" tool in the Processing Toolbox, or 2) create a new blank script, copy-paste the code in, and save the script. To run the script select the "Run Algorithm" option on the script editor screen (looks like interlaced gears) and provide the required information.

This program pulls refinery locations out of GAMS .lst files and adds a point layer to that location. It also tracks the pathways that user indicated materials take in the optimisation.

This script requires:

(1) the .lst from GAMS with refinery locations listed
(2) vector grid which corresponds to the locations used in the GAMS analysis
(3) which field of the vector grid corresponds to the ID number
(4) name of the variable for presence of refinery
(5) name of the variable for flow rate of material
(6) cell ID for demand centers
(7) names of products, separated by commas
(8) names of transportaion methods, separated by commas

This script outputs:

(1) a separate point layer for each refinery type with locations
(2) a separate line layer with arrows directing the flow of indicated materials for each material
