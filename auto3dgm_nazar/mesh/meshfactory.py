from os.path import isfile, splitext
from auto3dgm_nazar.mesh.mesh import Mesh
from numpy import array, ndarray, concatenate, empty, full
#from vtk import vtkPLYReader,vtkOBJReader,vtkSTLReader,vtkPolyData, vtkPoints, vtkCellArray
#from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk, numpy_to_vtkIdTypeArray
from tvtk.api import tvtk
from warnings import warn
import numpy as np


class MeshFactory(object):
    """Stub of Mesh Factory class.
    Longer class information...
    Attributes:
        attr1: Information.
        attr2: Information.

    MeshFactory (Class with Static Methods)
        createFromFile: receives a string file location, creates a VTK mesh object, returns Mesh object
        createFromData: receives vertex and/or face arrays, creates a VTK mesh object, returns Mesh object
        Rationale: Using a factory decouples mesh creation logic from VTK,
        enabling possibly complex loading behavior and even using non-VTK Mesh classes in the future
        Notes: Should be capable of creating meshes from files with formats .ply, .obj, .stl, and .off
    """

    @staticmethod
    def mesh_from_file(file_path, center_scale=False):
        """Returns a VTK PolyData object from a mesh.
        TODO ing file types: off. (The PyMesh Package might help.)"""
        allowed_filetypes = ['.ply', '.obj','.stl','.off']

        if isfile(file_path) and splitext(file_path)[1] in allowed_filetypes:
            if splitext(file_path)[1] == '.ply':
                reader = tvtk.PLYReader()

            elif splitext(file_path)[1] == '.obj':
                reader = tvtk.OBJReader()

            elif splitext(file_path)[1] == '.stl':
                reader = tvtk.STLReader()
            elif splitext(file_path)[1] == '.off':
                (vertices, faces)=MeshFactory.off_parser(file_path)
                namelist=file_path.split('/')
                name=namelist[len(namelist)-1].split('.')[0]
                return MeshFactory.mesh_from_data(vertices, faces, name=name, center_scale=center_scale)
            namelist=file_path.split('/')
            name=namelist[len(namelist)-1].split('.')[0]
            reader.file_name=file_path
            #reader.SetFileName(file_path)
            reader.update()
            
            polydata = reader.get_output()
            if isinstance(polydata, tvtk.PolyData):
                #polydata=tvtk.to_tvtk(polydata)
                return Mesh(polydata, center_scale, name)
            else:
                msg = 'VTK reader output type expected {}, but got {}'.format(
                    'vtkCommonDataModelPython.vtkPolyData', type(polydata))
                raise TypeError(msg)
        else:
            msg = 'File {} not present or not allowed filetype: {}'.format(
                file_path, ', '.join(allowed_filetypes))
            raise OSError(msg)

    @staticmethod
    def mesh_from_data(vertices, faces=empty([0,0]), name=None, center_scale=False, deep=True):
        """Returns a VTK PolyData object from vertex and face ndarrays"""
        vertices = np.array(vertices)
        numV = np.shape(vertices)[0]
        if center_scale:
            #print(vertices[0,:])
            #print(np.mean(vertices,axis=0))
            vertices = vertices-np.matlib.repmat(np.mean(vertices,axis=0),numV,1)
            #print(vertices[0,:])
            #print(np.mean(vertices,axis=0))
            vertices = vertices/np.linalg.norm(vertices,'fro')
        faces = array(faces, dtype=int)
        vertices = array(vertices,dtype=float)

        polydata = tvtk.PolyData()

        # vertices
        points = tvtk.Points()
        points.from_array(vertices)
        polydata.points=points
        #points.SetData(numpy_to_vtk(vertices, deep=deep))
        #polydata.SetPoints(points)

        # faces
        #if isinstance(faces, ndarray) and faces.ndim == 2 and faces.shape[1] == 3:
            #faces = concatenate((full([faces.shape[0], 1], 3), faces), axis=1)
            #polydata.polys=faces
            #cells = tvtk.CellArray()
            #nf = faces.shape[0]
            #vtk_id_array = numpy_to_vtkIdTypeArray(faces.ravel(), deep=deep)
            #cells.SetCells(nf, vtk_id_array)
            #polydata.SetPolys(cells)
        #polydata=tvtk.to_tvtk(polydata)
        return Mesh(vtk_mesh=polydata, center_scale=False, name=name)

    @staticmethod
    def off_parser(file_path):
        file=open(file_path,"r")
        # Checking we have valid headers
        A=file.readline().split()
        if A[0] != 'OFF':
            msg = 'The input file does not seem to be valid off file, first line should read "OFF".'
            raise TypeError(msg)
        #Reading in the number of vertices, faces and edges, and pre-formatting their arrays
        (V,F,E)=map(int,file.readline().strip().split(' '))
        vertices=empty([V,3], dtype=np.float32)
        faces=empty([F,3])
        # Read in the vertices
        for i in range(0,V):
            vertices[i]=list(map(float,file.readline().strip().split(' ')))
        #Read in the faces
        for i in range(0,F):
            line=list(map(int,file.readline().strip().split(' ')))
        # Notify the user that there are non-triangular faces.
        # Non-triangular faces wouldn't be supported by the vtk setup that we have anyway.
        # Better way would be to triangulate the polygons, that can be added if deemed useful
        # Also, we could use warnings
            if len(line)!=4:
                print("Warning: The .off contains non-triangular faces, holes might have been created.")
            if (line[0]!=3 and len(line)==4):
                print("Warning: The .off file contains a face that is defined to be non-triangular. It is a valid triangle, reading it as a triangle.")
            faces[i]=line[1:4]
        #TODO Once the correct format for mesh_from_data face array is clarified, decide if faces should be transposed or not
        vertices.astype(np.float32)
        return(vertices, faces.T)
