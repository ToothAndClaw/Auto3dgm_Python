#INPUT
#path to meshes
#PLEASE ADD SLASHES AS APPROPRIATE FOR OS
meshDir = '/INPUT/MESH/DIRECTORY/HERE/'
#path to cleaned meshes
outputDir = '/OUTPUT/MESH/DIRECTORY/HERE/'


import numpy as np
import pymeshlab as pml
import os


notSimplyConnectedDir = outputDir+'/NotSimplyConnected/'
discDir = outputDir + 'DiscTopology/'
sphereDir = outputDir + 'SphereTopology/'
#path to bad meshes
badDir = outputDir + 'BadMeshes/'
#number of smoothing iterations
numSmooth = 2



def touch(newDir):
    if not os.path.isdir(newDir):
        os.mkdir(newDir)
        
meshList = os.listdir(meshDir)
touch(outputDir)
touch(notSimplyConnectedDir)
touch(discDir)
touch(sphereDir)
touch(badDir)

for i in range(len(meshList)):
    print(meshList[i],flush=True)
    ms=pml.MeshSet()
    try:
        ms.load_new_mesh(meshDir+meshList[i])
    except:
        continue
    ms.set_current_mesh(0)
    ms.meshing_remove_connected_component_by_diameter(mincomponentdiag=pml.Percentage(20))
    out_dict = ms.get_topological_measures()

    cnt = 0
    while not out_dict['is_mesh_two_manifold']:
        ms.meshing_repair_non_manifold_edges(method=0)
        ms.meshing_repair_non_manifold_vertices(vertdispratio=0)
        ms.meshing_remove_unreferenced_vertices()
        ms.meshing_remove_duplicate_faces()
        ms.meshing_remove_duplicate_vertices()
        try:
            ms.meshing_close_holes(maxholesize=50,newfaceselected=True,selfintersection=True)
        except:
            continue

        out_dict = ms.get_topological_measures()
        cnt = cnt + 1
        if cnt == 30:
            print('Unable to clean without deleting some connected components, attempting...')
            break
    if out_dict['connected_components_number'] > 1:
        ms.generate_splitting_by_connected_components()
        bestVol = 0
        bestInd = 0
        for j in range(out_dict['connected_components_number']):
            k = j+1
            curVol = ms.mesh(k).bounding_box().dim_x()*ms.mesh(k).bounding_box().dim_y()*ms.mesh(k).bounding_box().dim_z()
            if curVol > bestVol:
                bestInd = j+1
                bestVol = curVol
        ms.set_current_mesh(bestInd)
    msTemp = pml.MeshSet()
    msTemp.add_mesh(ms.current_mesh())
    ms=msTemp
    
    cnt = 20
    while ms.current_mesh().face_number() < 10000:
        ms.meshing_surface_subdivision_loop(loopweight=1,iterations=1,threshold=pml.Percentage(0))
        cnt = cnt-1
        if cnt == 0:
            break
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum=10000,autoclean=True)
    
    for j in range(numSmooth):
        ms.apply_coord_hc_laplacian_smoothing()
    
    cnt = 0
    out_dict = ms.get_topological_measures()
    if out_dict['connected_components_number'] > 1:
        ms.generate_splitting_by_connected_components()
        bestVol = 0
        bestInd = 0
        for j in range(out_dict['connected_components_number']):
            k = j+1
            curVol = ms.mesh(k).bounding_box().dim_x()*ms.mesh(k).bounding_box().dim_y()*ms.mesh(k).bounding_box().dim_z()
            if curVol > bestVol:
                bestInd = j+1
                bestVol = curVol
        ms.set_current_mesh(bestInd)
    msTemp = pml.MeshSet()
    msTemp.add_mesh(ms.current_mesh())
    ms=msTemp
    out_dict = ms.get_topological_measures()
    while not out_dict['is_mesh_two_manifold']:
        ms.meshing_repair_non_manifold_edges(method=0)
        ms.meshing_repair_non_manifold_vertices(vertdispratio=0)
        ms.meshing_remove_unreferenced_vertices()
        ms.meshing_remove_duplicate_faces()
        ms.meshing_remove_duplicate_vertices()
        if out_dict['connected_components_number'] > 1:
            ms.generate_splitting_by_connected_components()
            bestVol = 0
            bestInd = 0
            for j in range(out_dict['connected_components_number']):
                k = j+1
                curVol = ms.mesh(k).bounding_box().dim_x()*ms.mesh(k).bounding_box().dim_y()*ms.mesh(k).bounding_box().dim_z()
                if curVol > bestVol:
                    bestInd = j+1
                    bestVol = curVol
            ms.set_current_mesh(bestInd)
        msTemp = pml.MeshSet()
        msTemp.add_mesh(ms.current_mesh())
        ms=msTemp
        out_dict = ms.get_topological_measures()
        
        cnt = cnt + 1
        if cnt == 10:
            out_dict
            break
    for prefix in [badDir,notSimplyConnectedDir,discDir,sphereDir]:
        if os.path.isfile(prefix+meshList[i]):
            os.remove(prefix+meshList[i])
    
    ms.meshing_close_holes(maxholesize=30,newfaceselected=True,selfintersection=True)
    ms.meshing_surface_subdivision_loop(loopweight=1,iterations=2,selected=True)
    ms.meshing_remove_unreferenced_vertices()
    ms.meshing_remove_connected_component_by_diameter(mincomponentdiag=pml.Percentage(20))
    ms.meshing_close_holes(maxholesize=30,newfaceselected=True,selfintersection=True)
    out_dict = ms.get_topological_measures()
    if out_dict['connected_components_number'] > 1:
        ms.generate_splitting_by_connected_components()
        bestVol = 0
        bestInd = 0
        for j in range(out_dict['connected_components_number']):
            k = j+1
            curVol = ms.mesh(k).bounding_box().dim_x()*ms.mesh(k).bounding_box().dim_y()*ms.mesh(k).bounding_box().dim_z()
            if curVol > bestVol:
                bestInd = j+1
                bestVol = curVol
        ms.set_current_mesh(bestInd)
    try:
        msTemp = pml.MeshSet()
        msTemp.add_mesh(ms.current_mesh())
        ms=msTemp
        ms.meshing_re_orient_faces_coherentely()
        out_dict = ms.get_topological_measures()

        if out_dict['connected_components_number'] > 1:
            ms.save_current_mesh(badDir+meshList[i])
            print(meshList[i]+':ConnectedComponentIssue',flush=True)
        elif out_dict['genus'] > 0:
            ms.save_current_mesh(notSimplyConnectedDir+meshList[i])
            print(meshList[i]+':NotSimplyConnected',flush=True)
        elif out_dict['boundary_edges'] > 0:
            ms.save_current_mesh(discDir+meshList[i])
            print(meshList[i]+':Disc',flush=True)
        else:
            ms.save_current_mesh(sphereDir+meshList[i])
            print(meshList[i]+':Sphere',flush=True)
    except:
        ms.save_current_mesh(badDir+meshList[i])
        print(meshList[i]+':BadMesh',flush=True)
