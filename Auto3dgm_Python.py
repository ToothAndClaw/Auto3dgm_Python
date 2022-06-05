import tkinter.filedialog
import tkinter as tk
import os
import multiprocessing
import psutil
import threading
import json
import time
import webbrowser
import auto3dgm_nazar
import numpy as np
import pandas as pd
import trimesh
import numpy.matlib
from datetime import datetime
from tkinter import messagebox
from tkinter import ttk
from http.server import HTTPServer, CGIHTTPRequestHandler
from auto3dgm_nazar.mesh.meshexport import MeshExport
from auto3dgm_nazar.mesh.meshfactory import MeshFactory
from http.server import HTTPServer, CGIHTTPRequestHandler


# Set up GUI
SPAN_WIDTH = 3
ENTRY_WIDTH = 23
FILE_WIDTH = 63
PADX = 10
PADY = (0, 10)


# Opens file browser
class interface:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Auto3dgm_Python")
        self.alignData = None
        self.sampledMeshes = None
        self.originalMeshes = None



    # Clears tkinter 
    def clear(self):
        lst = self.root.grid_slaves()
        for l in lst:
            l.destroy()
        
        lst = self.root.pack_slaves()
        for l in lst:
            l.destroy()

        for widget in self.root.winfo_children():
            widget.destroy()



    # Browse for file
    def browseFile(self, entry):

        filename = tk.filedialog.askdirectory()
        if(len(filename) != 0):
            entry.delete(0,"end")
            entry.insert(0, filename)
    

    
    # Toggle function for reflection
    # Done in this way to avoid global variable
    def switchRefl(self):    
        # Determine if switch is on or off
        if self.reflection_btn["text"] == "Reflection": 
            self.reflection_btn["text"] = "No Reflection"
        else:
            self.reflection_btn["text"] = "Reflection"

    

    # Save settings
    def saveSettings(self, num_subsample_e1, num_subsample_e2, 
                    seed_e, num_cores_var, num_cores_e, sample_method_var,
                    reflection_btn, mesh_dir_entry, output_dir_entry):

        # Get inputs
        num_subsample = (int(num_subsample_e1.get()), int(num_subsample_e2.get()))
        seed = seed_e.get()
        if seed == "":
            seed = None
        else:
            seed = int(seed)
        num_cores = num_cores_var.get()
        if num_cores == 0:
            num_cores = int(num_cores_e.get())
        sample_method = sample_method_var.get()

        if reflection_btn["text"] == "Reflection": 
            reflection = True
        else:
            reflection = False

        mesh_dir = mesh_dir_entry.get()
        output_dir = output_dir_entry.get()
        
        # Validate inputs
        if(len(mesh_dir) == 0):
            tk.messagebox.showerror("Error", "You need to select your mesh directory!", icon="error")
            return
        if(len(output_dir) == 0):
            tk.messagebox.showerror("Error", "You need to select your output directory!", icon="error")
            return
        
        # Add on ending / if needed
        if mesh_dir[-1] != "/" or mesh_dir[-1] != "\\":
            mesh_dir += "/"
        if output_dir[-1] != "/" or output_dir[-1] != "\\":
            output_dir += "/"
        
        # Not the prettiest way, but it was the easiest to type it out
        settings = {"num_subsample": num_subsample, "seed": seed, "num_cores": num_cores, 
        "sample_method": sample_method, "reflection": reflection, "mesh_dir": mesh_dir, 
        "output_dir": output_dir}

        with open('settings.json', 'w+') as f:
            json.dump(settings, f)

        self.clear()
        self.alignMeshController()



    # Set the settings for alignment
    def setSettings(self):
        self.running = True
        self.root.geometry('400x485')

        # Labels for input boxes
        tk.Label(self.root, text="Number of Subsampled Points").grid(row=0, columnspan = SPAN_WIDTH, sticky="W")
        tk.Label(self.root, text="Low Resolution").grid(row=1, column=0, sticky="W")
        tk.Label(self.root, text="High Resolution").grid(row=1, column=1, sticky="W")
        tk.Label(self.root, text="FPV Seed (Optional)").grid(row=3, sticky="W")
        tk.Label(self.root, text="Single Core").grid(row=5, column=0, sticky="W")
        tk.Label(self.root, text="Multiple Cores").grid(row=5, column=1, sticky="W")
        tk.Label(self.root, text="Number of Cores").grid(row=5, column=2, sticky="W")
        tk.Label(self.root, text="Sampling Method").grid(row=7, sticky="W")
        tk.Label(self.root, text="Mesh Directory").grid(row=10, sticky="W")
        tk.Label(self.root, text="Output Directory").grid(row=13, sticky="W")


        # Input Variables
        sample_method_var = tk.StringVar()
        num_cores_var = tk.IntVar()


        # Entries
        num_subsample_e1 = tk.Entry(self.root, width=ENTRY_WIDTH)
        num_subsample_e2 = tk.Entry(self.root, width=ENTRY_WIDTH)

        seed_e = tk.Entry(self.root, width=ENTRY_WIDTH)

        num_cores_e = tk.Entry(self.root, width=ENTRY_WIDTH)

        mesh_dir_entry, output_dir_entry = tk.Entry(self.root, width=FILE_WIDTH), tk.Entry(self.root, width=FILE_WIDTH)

        

        # Toggle Button 
        # Weird work around for scope
        reflection_btn = tk.Button(self.root, text="Reflection", width=20,
                                    command = lambda: self.switchRefl())

        self.reflection_btn = reflection_btn
                             
        

        # Radio Buttons
        num_cores_r1 = tk.Radiobutton(self.root, text="Single Core", value=1, var=num_cores_var)
        num_cores_r2 = tk.Radiobutton(self.root, text="Multiple Cores", value=0, var=num_cores_var)

        sample_method_r1 = tk.Radiobutton(self.root, text="FPS", value="FPS", var=sample_method_var)
        sample_method_r2 = tk.Radiobutton(self.root, text="GPL", value="GPL", var=sample_method_var)
        sample_method_r3 = tk.Radiobutton(self.root, text="Hybrid", value="Hybrid", var=sample_method_var)
        sample_method_r2["state"] = "disabled"
        sample_method_r3["state"] = "disabled"


        # Set up the browse and save buttons
        btn_bws_mesh = tk.Button(self.root, height=1, width=10, text="Browse", 
                            command=lambda:self.browseFile(mesh_dir_entry))
        btn_bws_save = tk.Button(self.root, height=1, width=10, text="Browse", 
                            command=lambda:self.browseFile(output_dir_entry))
        btn_save = tk.Button(self.root, height=2, width=20, text="Save Settings", 
                            command=lambda:self.saveSettings(num_subsample_e1, num_subsample_e2, 
                                                            seed_e, num_cores_var, num_cores_e, sample_method_var,
                                                            reflection_btn, mesh_dir_entry, output_dir_entry))


        # Set default values
        cwd = os.getcwd()
        num_subsample_e1.insert(0, 100)
        num_subsample_e2.insert(0, 200)
        output_dir_entry.insert(0, cwd)
        num_cores_e.insert(0, psutil.cpu_count(logical=False))
        sample_method_var.set("FPS")


        # Set positioning
        num_subsample_e1.grid(row=2, column=0, sticky="W", pady=PADY)
        num_subsample_e2.grid(row=2, column=1, sticky="W", pady=PADY)

        seed_e.grid(row=4, sticky="W", pady=PADY)

        num_cores_r1.grid(row=6, column=0, sticky="W", pady=PADY)
        num_cores_r2.grid(row=6, column=1, sticky="W", pady=PADY)
        num_cores_e.grid(row=6, column=2, sticky="W", pady=PADY)

        sample_method_r1.grid(row=8, column=0, sticky="W", pady=PADY)
        sample_method_r2.grid(row=8, column=1, sticky="W", pady=PADY)
        sample_method_r3.grid(row=8, column=2, sticky="W", pady=PADY)

        reflection_btn.grid(row=9)

        mesh_dir_entry.grid(row=11, columnspan = SPAN_WIDTH, sticky="W", pady = (0, 5))
        btn_bws_mesh.grid(row=12, sticky="W", pady=(0,10))

        output_dir_entry.grid(row=14, columnspan = SPAN_WIDTH, sticky="W", pady=(0,5))
        btn_bws_save.grid(row=15, sticky="W", pady=(0,10))

        btn_save.grid(row=16, sticky="W", pady=10)


        # Allows for span across multiple columns
        for i in range(SPAN_WIDTH):
            self.root.grid_columnconfigure(i, weight=1, uniform="foo")


        # Put Padding around all elements
        for child in self.root.winfo_children():
            child.grid_configure(padx=10)

        

    # Start loading bar
    def startLoading(self, text):
        ft = ttk.Frame()
        ft.pack(expand=True, fill=tk.BOTH, side=tk.TOP)
        pb_hD = ttk.Progressbar(ft, orient='horizontal', mode='indeterminate')
        tk.Label(ft, text=text).pack(side=tk.TOP, pady = 10, padx = 50)
        pb_hD.pack(expand=True, fill=tk.BOTH, pady = (8, 15), padx = 50)
        pb_hD.start(20)
        self.root.title("Auto3dgm_Python")
        self.root.mainloop()



    # Centers and gives unit surface area
    def Centralize(self, mesh, scale=None):
        Center = np.mean(mesh.vertices, 0).reshape(1,3)
        foo = np.matlib.repmat(Center, len(mesh.vertices), 1)
        mesh.vertices -= foo

        if scale != None:
            mesh.vertices = mesh.vertices * np.sqrt(1 / mesh.area)

        return mesh, Center


    def convert(self):
        mesh_dir = self.settings["mesh_dir"]

        # Make output directory if it doesn't exist
        output_dir = self.settings["output_dir"] + "originalMeshes/"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for file in os.listdir(mesh_dir):
            if file.endswith(".off") or file.endswith(".obj") or file.endswith(".ply"):
                filename = os.path.splitext(file)[0]
                mesh = trimesh.load(mesh_dir + file)
                mesh.export(output_dir + filename + '.ply')

        self.settings["mesh_dir"] = output_dir





    # Samples and aligns meshes
    def alignMesh(self):
        # Open settings file saved made by gui
        with open("settings.json") as json_file: 
            self.settings = json.load(json_file)

        # Convert files to .ply, .off files won't work
        self.convert()

        mesh_dir = self.settings["mesh_dir"]
        num_subsample = self.settings["num_subsample"]
        seed = self.settings["seed"]


        dataset_coll = auto3dgm_nazar.dataset.datasetfactory.DatasetFactory.ds_from_dir(mesh_dir)
        self.originalMeshes = dataset_coll.datasets[0]
        
        print("Subsampling meshes",flush=True)
        sample_time = time.time()
        if seed:
            ss = auto3dgm_nazar.mesh.subsample.Subsample(pointNumber=num_subsample, meshes=self.originalMeshes, seed=seed,center_scale=False)
        else:
            ss = auto3dgm_nazar.mesh.subsample.Subsample(pointNumber=num_subsample, meshes=self.originalMeshes, center_scale=False)
        self.subsample = ss
        
        ss_res = ss.ret

        low_res_meshes = []
        numFail=0
        for name, mesh in ss_res[num_subsample[0]]['output'].items():
            mesh.name = name
            newMesh = MeshFactory.mesh_from_data(mesh.koodinimi, center_scale=True, name=mesh.name)
            low_res_meshes.append(newMesh)  
            

        self.sampledMeshes = []
        for name, mesh in ss_res[num_subsample[1]]['output'].items():
            mesh.name = name
            newMesh = MeshFactory.mesh_from_data(mesh.koodinimi, center_scale=True, name=mesh.name)
            self.sampledMeshes.append(newMesh)  

        sample_time = time.time() - sample_time
        print("--- %s seconds for sampling meshes ---" % (sample_time),flush=True)
        print("Finished sampling",flush=True)
        

        # Align low resolution meshes
        print("Aligning low resolution meshes")
        low_res_time = time.time()
        mirror = self.settings["reflection"]
        corr = auto3dgm_nazar.analysis.correspondence.Correspondence(meshes=low_res_meshes, mirror=mirror)
        low_res_time = time.time() - low_res_time
        print("--- %s seconds for low resolution meshes ---" % (low_res_time))       
        

        # Align high resolution meshes
        print("Aligning high resolution meshes",flush=True)
        high_res_time = time.time()
        ga = corr.globalized_alignment
        self.alignData = auto3dgm_nazar.analysis.correspondence.Correspondence(meshes=self.sampledMeshes, mirror=mirror, initial_alignment=ga)
        high_res_time = time.time() - high_res_time
        print("--- %s seconds for sampling meshes ---" % (sample_time),flush=True)
        print("--- %s seconds for low resolution meshes ---" % (low_res_time),flush=True)   
        print("--- %s seconds for high resolution meshes ---" % (high_res_time),flush=True)
        print("Saving aligned meshes")

        # Make output directory if it doesn't exist
        output_dir = self.settings["output_dir"] + "alignedMeshes/"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)


        viewer_dir = os.getcwd() + "/viewer/aligned_meshes/"
        # Clear any previous meshes in the viewer folder
        for f in os.listdir(viewer_dir):
            os.remove(os.path.join(viewer_dir, f))


        # normalize and export meshes
        time_save = time.time()
        for t in range(len(self.originalMeshes)):
            R = self.alignData.globalized_alignment['r'][t]

            verts=self.originalMeshes[t].vertices
            faces=self.originalMeshes[t].faces
            name=self.originalMeshes[t].name


            vertices=np.transpose(np.matmul(R,np.transpose(verts)))
            faces=faces.astype('int64')

            # aligned_mesh=auto3dgm_nazar.mesh.meshfactory.MeshFactory.mesh_from_data(vertices, faces=faces, name=name, center_scale=True, deep=True)
            # MeshExport.writeToFile(output_dir, aligned_mesh, format='ply')
            # aligned_mesh.name = aligned_mesh.name.replace("_", "-")
            # MeshExport.writeToFile(viewer_dir, aligned_mesh, format='obj')

            # mesh_from_data doesn't create faces, so I used this workaround
            aligned_mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
            aligned_mesh, _ = self.Centralize(aligned_mesh, scale=None)
            aligned_mesh.export(output_dir + name + '.ply')
            name = name.replace("_", "-")
            aligned_mesh.export(viewer_dir + name + '.obj')


        print("Total time to save", time.time() - time_save)
        print("Aligned meshes saved \n" )
        self.root.quit()



    # Controller to run loading bar and alignment concurrently
    def alignMeshController(self):
        self.root.destroy()
        self.root = tk.Tk()
        total_time = time.time()
        #self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        t1=threading.Thread(target=self.alignMesh, args=())
        t1.start()
        self.startLoading("Aligning Meshes")  # This will block while the mainloop runs
        t1.join()

        output = self.settings["output_dir"]
        output_landmarks = output + "landmarks/"
        output_rotations = output + "rotations/"
        if not os.path.exists(output_landmarks):
            os.makedirs(output_landmarks)
        if not os.path.exists(output_rotations):
            os.makedirs(output_rotations)
        
        self.exportAlignedLandmarksNew(output)
        #self.exportRotationsScale(output)
        #self.exportScaleInfo(output)
        #self.exportRotations(output_rotations)
        total_time = time.time() - total_time
        print("--- %s seconds total run time ---" % (total_time),flush=True)
        
        self.complete()


    # Taken from auto3dgm slicer code
    def landmarksFromPseudoLandmarks(self, subsampledMeshes, permutations, rotations):
        meshes = []
        for i in range(len(subsampledMeshes)):
            mesh = self.sampledMeshes[i]
            perm = permutations[i]
            rot = rotations[i]
            V = mesh.vertices
            # scaledV = self.originalMeshes[i].vertices
            lmtranspose = V.T @ perm
            #landmarks = scaledV
            landmarks = np.transpose(np.matmul(rot,lmtranspose))
            mesh = auto3dgm_nazar.mesh.meshfactory.MeshFactory.mesh_from_data(vertices=landmarks,name=mesh.name, center_scale=False, deep=True)
            meshes.append(mesh)

        return(meshes)



    def exportAlignedLandmarksNew(self, output):
        exportFolder = output + "landmarks/"
        self.touch(exportFolder)
        m = self.sampledMeshes
        r = self.alignData.globalized_alignment['r']
        p = self.alignData.globalized_alignment['p']
        landmarks = self.landmarksFromPseudoLandmarks(m, p, r)

        # Create Pandas Dataframe
        colNames = ["Name"]
        for i in range(1, len(landmarks[0].vertices) + 1):
            idx = str(i)
            vals = ["X" + idx, "Y" + idx, "Z" + idx]
            colNames.extend(vals)

        dfLandmarks = pd.DataFrame(columns=colNames)

        for l in landmarks:
            self.saveNumpyArrayToFcsv(l.vertices, os.path.join(exportFolder, l.name))
            # self.saveNumpyArrayToCsv(l.vertices, os.path.join(exportFolder, l.name))
            data = [l.name]
            verts = np.array(l.vertices)
            data.extend(verts.flatten())
            dfLandmarks.loc[len(dfLandmarks)] = data

        # Save landmarks
        dfLandmarks.to_csv(os.path.join(output, "landmarks.csv"), index=False)
        #Write morphologika
        fid = open(os.path.join(output, "morphologika.txt"),"w")
        
        fid.write("[Individuals]\n")
        fid.write(str(dfLandmarks.shape[0]) + "\n")
        fid.write("[Landmarks]\n")
        fid.write(str(self.settings["num_subsample"][1])+"\n")
        fid.write("[dimensions]\n")
        fid.write("3\n")
        fid.write("[names]\n")
        for l in landmarks:
            fid.write(l.name+"\n")
        fid.write("\n")
        fid.write("[rawpoints]\n")
        
        for l in landmarks:
            fid.write("\n")
            fid.write("\'"+l.name+"\n")
            fid.write("\n")
            for i in range(l.vertices.shape[0]):
                fid.write("{:.7e}".format(l.vertices[i,0])+ " " + "{:.7e}".format(l.vertices[i,1]) + " " + "{:.7e}".format(l.vertices[i,2],7) + "\n")
        fid.close()
    # Exports landmarks
    def exportAlignedLandmarks(self, exportFolder):
        m = self.sampledMeshes
        r = self.alignData.globalized_alignment['r']
        p = self.alignData.globalized_alignment['p']
        landmarks = self.landmarksFromPseudoLandmarks(m, p, r)

        for l in landmarks:
            self.saveNumpyArrayToFcsv(l.vertices, os.path.join(exportFolder, l.name))
            # Auto3dgmLogic.saveLandmarks(l.vertices, os.path.join(exportFolder, l.name))


    def touch(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
    def saveNumpyArrayToCsv(self, array, filename):
        np.savetxt(filename+".csv",array,delimiter = ",",fmt = "%s")
  
    def saveNumpyArrayToFcsv(self, array, filename):
        l = np.shape(array)[0]
        fname2 = filename + ".fcsv"
        file = open(fname2,"w")
        file.write("# Markups fiducial file version = 4.4 \n")
        file.write("# columns = id,x,y,z,vis,sel \n")
        for i in range(l):
            file.write("p" + str(i) + ",")
            file.write(str(array[i,0]) + "," + str(array[i,1]) + "," + str(array[i,2]) + ",1,1 \n")
        file.close()


    def exportRotations(self, exportFolder):
        m = self.sampledMeshes
        r = self.alignData.globalized_alignment['r']

        for idx in range(len(m)):
            mesh = m[idx]
            rot = r[idx]
            # rot = np.linalg.inv(rot)
            # pad rot into 4 x 4 transform matrix in slicer
            rot[2][0] = -1 * rot[2][0]
            rot[2][1] = -1 * rot[2][1]
            rot[0][2] = -1 * rot[0][2]
            rot[1][2] = -1 * rot[1][2]
            rot = np.vstack((rot.T, [0, 0, 0]))  # add a 4-th column for center info
            rot = np.vstack((rot.T, [0, 0, 0, 1])) # add a 4-row
            self.saveNumpyArrayToCsv(rot, os.path.join(exportFolder, mesh.name))


    def exportRotationsScale(self, output):
        rotations = dict()
        scale_mat = dict()
        exportFolder = output + "rotations/"
        self.touch(exportFolder)
        m = self.sampledMeshes
        r = self.alignData.globalized_alignment['r']


        for idx in range(len(m)):
            mesh = m[idx]
            rot = r[idx]
            rotations[mesh.name] = rot
            self.saveNumpyArrayToCsv(rot, os.path.join(exportFolder, mesh.name))

        exportFolder = output + "scale/"
        self.touch(exportFolder)

        meshes = self.scale
        for idx, name in enumerate(meshes.keys()):
            filename = os.path.join(exportFolder, name)
            m = (1/meshes[name]) * np.diag([1, 1, 1])
            scale_mat[name] = m
            self.saveNumpyArrayToCsv(m, filename)

        # Create scale outputs
        fields = ["Name", "Rotations", "", "", "", "Scale"]
        filename = os.path.join(output, 'rotation_scale.csv')
        
        with open(filename, 'w+', newline='') as f:
            write = csv.writer(f)
            write.writerow(fields)

            for mesh in rotations.keys():
                row = [mesh]
                row.extend(rotations[mesh][0])
                row.append("")
                row.extend(scale_mat[mesh][0])
                write.writerow(row)

                for i in range(1, len(rotations[mesh])):
                    row = [""]
                    row.extend(rotations[mesh][i])
                    row.append("")
                    row.extend(scale_mat[mesh][i])
                    write.writerow(row)                


    def exportScaleInfo(self, output):
        exportFolder = output + "scale/"
        self.touch(exportFolder)
        meshes = self.scale
        for idx, name in enumerate(meshes.keys()):
            filename = os.path.join(exportFolder, name)
            m = (1/meshes[name]) * np.diag([1, 1, 1])
            self.saveNumpyArrayToCsv(m, filename)

    # Starts the viewer server
    def start_server(self, path, port=8000):
        '''Start a simple webserver serving path on port'''
        os.chdir(path)
        httpd = HTTPServer(('', port), CGIHTTPRequestHandler)
        httpd.serve_forever()
    


    # Visualize the meshes in browser
    def visualize(self):
        # Start the server in a new thread
        PORT = 8000
        os.chdir("./viewer/")

        daemon = threading.Thread(name='daemon_server',
                                target=self.start_server,
                                args=('.', PORT))
        daemon.setDaemon(True) # Set as a daemon so it will be killed once the main thread is dead.
        daemon.start()

        # Open the web browser 
        webbrowser.open('http://localhost:{}/auto3dgm.html'.format(PORT))

        



    # Opens dialog for viewing mesh or exiting
    def complete(self):
        self.clear()
        self.root.geometry('225x85')

        # Labels for input boxes
        tk.Label(self.root, text="Alignment completed.\nDo you want to view aligned meshes?").grid(row=0, columnspan = SPAN_WIDTH,
                                                                                                    pady=PADY, padx=PADX)

        btn_yes = tk.Button(self.root, height=1, width=10, text="Yes", 
                            command=lambda:self.visualize())

        btn_no = tk.Button(self.root, height=1, width=10, text="Exit", 
                            command=lambda:self.root.destroy())

        btn_yes.grid(row=1, column=0, sticky="W", columnspan = SPAN_WIDTH, pady=PADY, padx=PADX)
        btn_no.grid(row=1, column=2, sticky="W", columnspan = SPAN_WIDTH, pady=PADY, padx=PADX)


   



if __name__ == "__main__":
    inter = interface()
    inter.setSettings()
    #inter.root.protocol("WM_DELETE_WINDOW", inter.on_closing)
    #inter.alignMeshController()
    inter.root.mainloop()