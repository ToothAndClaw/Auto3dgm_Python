import auto3dgm_nazar
import time
start_time = time.time()

dataset_coll = auto3dgm_nazar.dataset.datasetfactory.DatasetFactory.ds_from_dir("fixtures/sample")
orig_meshes = dataset_coll.datasets[0]

ss = auto3dgm_nazar.mesh.subsample.Subsample(pointNumber=[100, 200], meshes=orig_meshes)
ss_res = ss.ret

low_res_meshes = []
for name, mesh in ss_res[100]['output']['output'].items():
	mesh.name = name
	low_res_meshes.append(mesh)

high_res_meshes = []
for name, mesh in ss_res[200]['output']['output'].items():
	mesh.name = name
	high_res_meshes.append(mesh)

m1 = low_res_meshes[0]

#imp.reload(auto3dgm_nazar.analysis.correspondence)
corr = auto3dgm_nazar.analysis.correspondence.Correspondence(meshes=low_res_meshes)
print("--- %s seconds ---" % (time.time() - start_time))
#imp.reload(auto3dgm_nazar.analysis.correspondence)
#corr_high = auto3dgm_nazar.analysis.correspondence.Correspondence(meshes=high_res_meshes, initial_alignment=ga)

#corr2 = auto3dgm_nazar.analysis.correspondence.Correspondence(meshes=low_res_meshes)
