import numpy
from abaqus import mdb
import abaqusConstants as aq 
from hAssembly import *
from hCoordinates import *
from hJob import *
from hMaterial import *
from hMesh import *
from hModel import *
from hPart import *
from hProperty import *
from hStep import *

import os

inpRoot = "E:\\inpFiles" # Location of INP files
workingDir = 'W:\\Research\\CTCSAbaqus'
os.makedirs(inpRoot)

# Create manifest
manifile = inpRoot+"/manifest.txt"
f = open(manifile, "w")
f.write('ID,Matrix,Filler,Portion,CalcPo,Radius,Number,Side,Delta,IntSize,IntCond,Nodes,Elements,DevFac,MeshSeed,dT\n')
f.close()

# Get material list
materials = getMaterialList() # Load in material Data

for key1, val in materials.iteritems():
	#Matrix levelF
	os.makedirs(inpRoot+"/"+str(key1))
	fillers = materials[key1]['fillers']
	for key2, val2 in fillers.iteritems():
		#Filler level
		os.makedirs(inpRoot+"/"+str(key1)+"/"+str(key2))
		portio1 = 'phr'
		portio2 = 'volPortion'
		if portio1 in materials[key1]['fillers'][key2].keys():
			portions = materials[key1]['fillers'][key2][portio1]
		elif portio2 in materials[key1]['fillers'][key2].keys():
			portions = materials[key1]['fillers'][key2][portio2]
		else:
			break
		for val3 in portions:
			# Portion level
			os.makedirs(inpRoot+"/"+str(key1)+"/"+str(key2)+"/"+str(val3))
			params = ["radius", "tc"]
			for val4 in params:
				# Parameter level
				os.makedirs(inpRoot+"/"+str(key1)+"/"+str(key2)+"/"+str(val3)+"/"+str(val4))
				
				if val4 == "radius":
					for i in range(2):
						# make model
						modelObject, modelName = createModel(2)
						# define materials
						side, radius, portions, dP, dM, cP, cM = defExperiment(modelObject, key1, key2)
						phr = val3 
						# get coordinates, interface Max, random interface size, etc.
						if portio1 in materials[key1]['fillers'][key2].keys():
							radius, number = invPHRAlternate3D(phr, dP, radius, dM, side)
							calcPHR = round(calculatePHR3D(number, dP, radius, dM, side))
						elif portio2 in materials[key1]['fillers'][key2].keys():
							radius, number = invVolumeAlternate3D(phr, radius, side)
							calcPHR = round(calculateVolume(number, radius, side), 3)
						
						delta = 0.15
						
						#interfaceConductivity= numpy.random.sample(1) * (cP-cM) + cM # Between cM and cP
						#interfaceConductivity = int(interfaceConductivity[0])
						interfaceConductivity = int((cP+cM)/2.0)
						# Define interface materials
						defineMaterial(modelObject, "Interface", dM, interfaceConductivity)
						intPortionLimit = getInterfacePortionLimit(side, radius, number, delta)
						interfacePortion = numpy.random.sample(1) * (intPortionLimit-0.15) + 0.15 # random 0.15 to limit inclusive
						interfacePortion = round(interfacePortion[0], 3)
						xVals, yVals, zVals = getPoints3dDeterministic(side, radius, number)

						part = createMatrix(modelObject, side, False) # Create the matrix
						edges1, vertices1, face1 = assignGeomSequence(part) # Create references to important sets in our matrix
						part2 = createSphereParticle(modelObject, radius, side) # Create Particle part
						edges2, vertices2, face2 = assignGeomSequence(part2) # Create references to important sets in particle 
						part3 = createSphereParticle(modelObject, (radius + radius*interfacePortion), side, "Interface") # Create interface part
						edges3, vertices3, face3 = assignGeomSequence(part3) # Create references to important sets in interface
						matrixSet, particleSet, interfaceSet = create3DInitialSets(part, part2, side, part3) # create sets for particle, matrix, and interface

						createSection(modelObject, part, key1, matrixSet) # Create section for matrix material
						createSection(modelObject, part2, key2, particleSet) # Create section for filler material
						createSection(modelObject, part3, "Interface", interfaceSet) # Create section for interface

						modelRootAssembly, fullMatrixPart = create3DMatrixInclusions(modelObject, part, part2, number, xVals, yVals, zVals, part3) # Create assembly and return references to assembly sets
						assemblyTop, assemblyBottom, assemblyAll = define3DAssemblySets(modelRootAssembly, side)
						temp1, temp2 = 328.15, 298.15 # Assign heat temperature to be used in experiment
						heatStep3D(modelObject, assemblyBottom, assemblyTop, temp1, temp2) # apply heat BC
						limitOutputHFL(modelObject, assemblyBottom, assemblyTop) # Limit ODB Output
						elements, nodes, df, meshSeed = makeMesh3D(modelObject, modelRootAssembly)  # Draw mesh and return number of nodes and elements
						makeElementSet(fullMatrixPart, modelRootAssembly)
						
						fileName = key1 + key2 + val4 + str(i+1)
						jobFi = createJob(modelName, fileName)
						afile = open(manifile, "a")
						afile.write(str(i+1)+","+key1+","+key2+","+str(phr)+","+str(calcPHR)+","+str(radius)+","+str(side)+","+str(delta)+","+str(interfacePortion)+","+str(interfaceConductivity)+","+str(nodes)+","+str(elements)+","+str(df)+","+str(meshSeed)+","+str(temp1-temp2)+"\n")
						afile.close()
						os.chdir(inpRoot+"/"+str(key1)+"/"+str(key2)+"/"+str(val3)+"/"+str(val4))
						generateINP(fileName)
						os.chdir(workingDir)
						del mdb.jobs[fileName]
						del mdb.models[modelName]
				elif val4 == "tc":
					# make model
					modelObject, modelName = createModel(2)

					# define materials
					side, radius, portions, dP, dM, cP, cM = defExperiment(modelObject, key1, key2)
					phr = val3 ###
					# get coordinates, interface Max, random interface size, etc.
					if portio1 in materials[key1]['fillers'][key2].keys():
						radius, number = invPHRAlternate3D(phr, dP, radius, dM, side)
						calcPHR = round(calculatePHR3D(number, dP, radius, dM, side))
					elif portio2 in materials[key1]['fillers'][key2].keys():
						radius, number = invVolumeAlternate3D(phr, radius, side)
						calcPHR = calculateVolume(number, radius, side)
					
					delta = 0.15
					intPortionLimit = getInterfacePortionLimit(side, radius, number, delta)
					interfacePortion = numpy.random.sample(1) * (intPortionLimit-0.15) + 0.15 # random 0.15 to limit inclusive
					interfacePortion = round(interfacePortion[0], 3)
					xVals, yVals, zVals = getPoints3dDeterministic(side, radius, number)

					interfaceConductivity= numpy.random.sample(1) * (cP-cM) + cM # Between cM and cP
					interfaceConductivity = int(interfaceConductivity[0])
					# Define interface materials
					defineMaterial(modelObject, "Interface", dM, interfaceConductivity)

					# Check PHR values
					

					part = createMatrix(modelObject, side, False) # Create the matrix
					edges1, vertices1, face1 = assignGeomSequence(part) # Create references to important sets in our matrix
					part2 = createSphereParticle(modelObject, radius, side) # Create Particle part
					edges2, vertices2, face2 = assignGeomSequence(part2) # Create references to important sets in particle 
					part3 = createSphereParticle(modelObject, (radius + radius*interfacePortion), side, "Interface") # Create interface part
					edges3, vertices3, face3 = assignGeomSequence(part3) # Create references to important sets in interface
					matrixSet, particleSet, interfaceSet = create3DInitialSets(part, part2, side, part3) # create sets for particle, matrix, and interface

					createSection(modelObject, part, key1, matrixSet) # Create section for matrix material
					createSection(modelObject, part2, key2, particleSet) # Create section for filler material
					createSection(modelObject, part3, "Interface", interfaceSet) # Create section for interface

					modelRootAssembly, fullMatrixPart = create3DMatrixInclusions(modelObject, part, part2, number, xVals, yVals, zVals, part3) # Create assembly and return references to assembly sets
					assemblyTop, assemblyBottom, assemblyAll = define3DAssemblySets(modelRootAssembly, side)
					temp1, temp2 = 328.15, 298.15 # Assign heat temperature to be used in experiment
					heatStep3D(modelObject, assemblyBottom, assemblyTop, temp1, temp2) # apply heat BC
					limitOutputHFL(modelObject, assemblyBottom, assemblyTop) # Limit ODB Output
					
					meshSeed = materials[matrix]['fillers'][key2]['meshSeed'] # recommended mesh
					df = materials[matrix]['fillers'][key2]['df'] # recommended deviation factor
					
					elements, nodes, df, meshSeed = makeMesh3D(modelObject, modelRootAssembly, meshSeed, df)  # Draw mesh and return number of nodes and elements
					makeElementSet(fullMatrixPart, modelRootAssembly)

					## define range for interface conductivity # Either constant or varying depending on other constants
					for i in range(2):
						interfaceConductivity= numpy.random.sample(1) * (cP-cM) + cM # Between cM and cP
						interfaceConductivity = int(interfaceConductivity[0])
						# Define interface materials
						defineMaterial(modelObject, "Interface", dM, interfaceConductivity) 
						
						fileName = key1 + key2 + val4 + str(i+1)
						jobFi = createJob(modelName, fileName)
						afile = open(manifile, "a")
						afile.write(str(i+1)+","+key1+","+key2+","+str(phr)+","+str(calcPHR)+","+str(radius)+","+str(side)+","+str(delta)+","+str(interfacePortion)+","+str(interfaceConductivity)+","+str(nodes)+","+str(elements)+","+str(df)+","+str(meshSeed)+","+str(temp1-temp2)+"\n")
						afile.close()
						os.chdir(inpRoot+"/"+str(key1)+"/"+str(key2)+"/"+str(val3)+"/"+str(val4))
						generateINP(fileName)
						os.chdir(workingDir)
						del mdb.jobs[fileName]
				
				

#odbfileName = modelName
#warningString, noElementsWarning = submitJob(modelName, odbfileName)  # Submit job and take note of any warnings
#avgHF, TC = getThermalProperties3D(radius, side, temp1, temp2, odbfileName) # Extract relevant information about thermal properties

#print(dataString(matrix, fillers[1], portions[3], radius, number, side, interfacePortion, delta, calcPHR, interfaceConductivity, seed, nodes, elements, df, meshSeed, avgHF, temp1, temp2, TC, warningString, warningPoints, noElementsWarning)) # Write the data to file
