from numpy import linalg
from scipy.optimize import linear_sum_assignment
from scipy.spatial import distance_matrix, KDTree
from scipy.optimize import linear_sum_assignment as Hungary
from scipy.sparse import csr_matrix, identity, find
from scipy.sparse.csgraph import minimum_spanning_tree, shortest_path
import numpy as np
from pprint import pprint
from auto3dgm_nazar import jobrun
from auto3dgm_nazar.jobrun import jobrun
from auto3dgm_nazar.jobrun import job
from auto3dgm_nazar.jobrun.jobrun import JobRun
from auto3dgm_nazar.jobrun.job import Job
import lap

class Correspondence:
    #params: self,
    #meshes: either a mesh object or a list (should be list) or a dictionary of mesh objects
    #meshes: a list of meshes 
    #globalize: flag for performing globalized pairwise alignment (default:yes)
    #mirror: flag for allowing mirrored meshes (default: no)
    #reference_index= index of the mesh that other meshes are aligned against
    
    def __init__(self, meshes, globalize=1, mirror=0, initial_alignment=None):
        #assumes that meshes is an ordered list of meshes
        self.globalizeparam=globalize
        self.mirror=mirror
        self.meshes=meshes
        self.initial_alignment=initial_alignment
        if self.initial_alignment:
            self.initial_pa_alignment=self.localize()
        n = len(meshes)
        n_pts = meshes[0].vertices.shape[0]

        job_data = self.generate_job_data()
        job_params = self.generate_params()
        job_func = self.generate_func()

        new_job = Job(data=job_data, params=job_params, func=job_func)
        new_jobrun = JobRun(job=new_job)
        output = new_jobrun.execute_jobs()
        #dependent on changing line 52 from jobrun (job_dict['output']['results'].... -> job_dict['output'] = results_dict)
        #also depends on results_dict being in d->float, p->permutation r-> rotaiton mapping
        self.results_dict = output['output']
        
        self.d_ret = np.empty([n, n])
        #self.p_ret = np.empty([n, n, n_pts], dtype=int)
        self.p_ret = {}
        #what is permutation
        self.r_ret = np.array([[None for x in range(n)] for y in range(n)])


        for key in self.results_dict.keys():
            #key will be a tuple
            self.d_ret[key[0]][key[1]] = self.results_dict[key]['d']

            x = self.results_dict[key]['p']
            if key[0] not in self.p_ret:
                self.p_ret[key[0]] = {}
            self.p_ret[key[0]][key[1]] = self.results_dict[key]['p']
            #print(self.results_dict[key]['p'],flush=True)
            self.r_ret[key[0]][key[1]] = self.results_dict[key]['r']
        self.pairwise_alignment = {'d': self.d_ret, 'r': self.r_ret, 'p': self.p_ret}    

        if self.globalizeparam:
            self.mst_matrix = Correspondence.find_mst(self.d_ret)
            self.globalized_alignment = self.globalize(self.pairwise_alignment, self.mst_matrix)

    def localize(self):
        if not self.initial_alignment:
            return
        p = {}
        r = np.array([[None for x in range(len(self.initial_alignment['r']))] for y in range(len(self.initial_alignment['r']))])
        for i in range(0, len(self.initial_alignment['r'])):
            for j in range(0, len(self.initial_alignment['r'])):            
                r[i][j] = self.initial_alignment['r'][i].T @ self.initial_alignment['r'][j]
                if i not in p:
                    p[i] = {}
                p_temp = self.initial_alignment['p'][j] @ self.initial_alignment['p'][i].T
                p[i][j] = self.permutation_sparse_to_flat(p_temp)
        return {'r': r, 'p': p}


    def generate_job_data(self):
        ret = {}
        for indexf, first in enumerate(self.meshes):
            for indexs, second in enumerate(self.meshes):
                if not Correspondence.has_pair(indexf, indexs, ret):
                    if self.initial_alignment is None:
                        initial_alignment = None
                    else:
                        initial_alignment = {
                            'r': self.initial_pa_alignment['r'][indexf][indexs],
                            'p': self.initial_pa_alignment['p'][indexf][indexs]
                        }
                    val = Correspondence.dict_val_gen(first, second, initial_alignment=initial_alignment)
                    toopl = (indexf, indexs)
                    ret[toopl] = val
                
        return ret

    def generate_params(self):
            return {'mirror': self.mirror}

    def generate_func(self):
        return self.align


    @staticmethod
    def dict_val_gen(first, second, initial_alignment=None):
        newDict = {'mesh1': first, 'mesh2': second, 'initial_alignment': initial_alignment}
        return newDict

    @staticmethod
    def has_pair(key1, key2, dictionary):
        tooplf = (key1, key2)
        toopls = (key2, key1)
        if (tooplf in dictionary.keys()) or (toopls in dictionary.keys()):
            #for testing, this has been set to False, Typically, should be set to True
            return False
        return False

    @staticmethod
    def find_mst(distance_matrix):
        return minimum_spanning_tree(csr_matrix(distance_matrix)).toarray()

    @staticmethod
    def graphshortestpaths(graph, index, reference):
        '''
        returns a [dist, pat] object with dist (double of distance between index and reference) and path (1xN vector representing path from reference->index)
        '''
        [dist_matrix, predecessors] = shortest_path(graph, return_predecessors=True)
        dist = dist_matrix[reference, index]
        pat = Correspondence.getpath(predecessors, index, reference)
        return [dist, pat]

    @staticmethod
    def globalize(pa, tree, base=0, type='mst'):
        '''
        takes a pairwise alignment (pa) formatted as a 3-entry array [D, R, P] and a tree (NP-matrix) and returns
        the global alignment obtained by propagating the tree as a list
        '''
        n = len(tree)
        [r, c] = np.nonzero(tree)
        mm = min(r[0], c[0])
        MM = max(r[0], c[0])
        pa_r = pa['r']
        pa_p = pa['p']
        N = pa_p[mm][MM].shape[0]

        retR = [None] * n
        retP = [None] * n

        if type is 'mst':
            for li in range(0, n):
                [dist, pat] = Correspondence.graphshortestpaths(tree+tree.transpose(), li, base)
                P = identity(N, dtype=int)
                R = np.identity(3)
                #test = range(21)
                for lj in range(1, len(pat)):
                    #print(pa_p[pat[lj]][pat[lj-1]],flush=True)
                    P = P @ Correspondence.permutation_flat_to_sparse(pa_p[pat[lj]][pat[lj-1]])
                    R = pa_r[pat[lj], pat[lj-1]] @ R
                #print(P,flush=True)
                #print(test,flush=True)
                retR[li] = R
                retP[li] = P
        return {'r': retR, 'p': retP}               

    @staticmethod
    def getpath(predecessors, index, reference):
        ancestors = predecessors[reference]
        tracer=index
        ret=[]
        while(tracer != reference):
            ret.append(tracer)
            tracer = ancestors[tracer]
        ret.append(reference)
        #ret.reverse()
        return ret

    @staticmethod
    def permutation_flat_to_sparse(p):
        data = np.ones(p.shape[0], dtype=int)
        cols = np.array(range(0,p.shape[0]), dtype=int)
        return csr_matrix((data, (p, cols)), shape=(p.shape[0], p.shape[0]))

    @staticmethod
    def permutation_sparse_to_flat(p):
        return find(p)[0]

    @staticmethod
    # An auxiliary method for computing the initial pairwise-alignment
    # Computes the principal components of two meshes and all possible rotations of the 3-axes)
    # params: mesh1, mesh2 meshes that have vertices that are 3 x n matrices
    #        mirror: a flag for whether or not mirror images of the shapes should be considered
    def principal_component_alignment(mesh1, mesh2, mirror):
        mirror = 1
        X = mesh1.vertices.T
        Y = mesh2.vertices.T
        #print(X)
        #print(Y)
        UX, DX, VX = linalg.svd(X, full_matrices=False)
        UY, DY, VY = linalg.svd(Y, full_matrices=False)
        #print(UX)
        #print(UY)
        #print(UX.T)
        #print(UY.T)
        P=[]
        R=[]

        P.append(np.array([1, 1, 1]))
        P.append(np.array([1, -1, -1]))
        P.append(np.array([-1, -1, 1]))
        P.append(np.array([-1, 1, -1]))
        if (mirror == 1):
            P.append(np.array([-1, 1, 1]))
            P.append(np.array([1, -1, 1]))
            P.append(np.array([1, 1, -1]))
            P.append(np.array([-1, -1, -1]))
        for i in P:
            R.append(np.dot(np.dot(UX, np.diag(i)), UY.T))
        return R

    @staticmethod
    # Computes the best possible initial alignment for meshes 1 and 2
    # Mesh 1 is used as the reference
    # params: mesh1, mesh2 meshes that have vertices that are 3 x n matrices
    #        mirror: a flag for whether or not mirror images of the shapes should be considered
    def best_pairwise_PCA_alignment(mesh1, mesh2, mirror):
        R = Correspondence.principal_component_alignment(mesh1, mesh2, mirror)
        permutations = []
        min_cost = np.ones(len(R)) * np.inf
        for rot, i in zip(R, range(len(R))):
            cost = distance_matrix(mesh1.vertices, np.dot(rot, mesh2.vertices.T).T)**2
            # The hungarian algorithm:
            # V1_ind, V2_ind = linear_sum_assignment(cost)
            trash, V2_ind, garbage = lap.lapjv(cost)
            min_cost[i] = trash
            permutations.append(V2_ind)

        best_rot_ind = np.argmin(min_cost)
        best_permutation = permutations[best_rot_ind]
        best_rot = R[best_rot_ind]
        d = min_cost[best_rot_ind]

        return {'p': best_permutation, 'r': best_rot, 'd': d}

    @staticmethod
    # Returns the meshed aligned by the initial PCA component pairing.
    # Everything is aligned against the mesh specified by the reference_index
    def initial_rotation(self):
        mesh1 = self.mesh_list[self.reference_index]
        Rotations = []
        for i in self.mesh_list:
            Rotations.append(self.best_pairwise_PCA_alignment(mesh1, i, self))
        return Rotations

    @staticmethod
    def permutation_from_rotation(mesh1, mesh2, R):
        cost = distance_matrix(mesh1.vertices, np.dot(R, mesh2.vertices.T).T)**2
        trash, V2_ind, garbage = lap.lapjv(cost)
        #V1_ind, V2_ind = linear_sum_assignment(cost)
        return V2_ind

    @staticmethod
    # Computes the Local Generalized Procrustes Distance between meshes.
    # NOTE: Params R_0, M_0 needs specification.
    def locgpd(mesh1, mesh2, R_0=None, M_0=None, max_iter=1000, mirror=False):
        # best_permutation and best_rot come from PCA
        if M_0 is None:
            M_0 = np.ones([len(mesh1.vertices), len(mesh1.vertices)])

        if R_0 is None:
            best_permutation, best_rot, d = Correspondence.best_pairwise_PCA_alignment(mesh1, mesh2, mirror)
        else:
            best_rot = R_0
            best_permutation = Correspondence.permutation_from_rotation(mesh1, mesh2, R_0)

        
        print(mesh1.name + ' to ' + mesh2.name)
        #print(best_rot)
        #print(best_permutation)

        V1 = mesh1.vertices.T
        V2 = mesh2.vertices.T
        #newV2 = np.dot(best_rot, V2)
        newV2 = V2

        i = 0
        while True:
            newV2= V2[:,best_permutation]
            err = V1 - np.dot(best_rot, newV2)
            #print("after Hungary", np.linalg.norm(err))
            
            # Do Kabsch
            cur_rot = Correspondence.Kabsch(V1.T, newV2.T)
            #newV2 = np.dot(cur_rot, newV2)
            err = V1 - np.dot(cur_rot, V2)
            #print("after Kabsch", np.linalg.norm(err))
            
            # Do Hungary
            cur_cost = distance_matrix(V1.T, np.dot(cur_rot, V2).T)**2
            cur_trash, cur_permutation, garbage = lap.lapjv(cur_cost)
            
            #if i > max_iter or cur_trash - best_trash > 0 or ((abs(cur_trash - best_trash)<1e-5*best_trash)):
            if np.linalg.norm(err) < 0.00000001 or i > max_iter or np.sum((cur_permutation - best_permutation) != 0) < 1:
                break
            else:
                if i % 1000 == 0:
                    print(str(i) + " iterations",flush=True)
                    # print("current iteration is:", i)
                    # print("current error is: ", np.sqrt(cur_trash))
            # update
            best_permutation = cur_permutation
            best_rot = cur_rot
            i += 1

        #d = np.sum((cur_permutation - best_permutation))
        d = np.sqrt(cur_trash)
        Rotate = best_rot
        print(d)
        Permutate = cur_permutation
        gamma = 1.5 * Correspondence.ltwoinf(V1 - newV2)

        return {'d': d, 'r': Rotate, 'p': Permutate, 'g': gamma}

    @staticmethod
    def ltwoinf(X):
        """l2-inf norm of x, i.e.the maximum 12 norm of the columns of x"""
        d = np.sqrt(max(np.square(X).sum(axis=0)))
        return d

    @staticmethod
    def Kabsch(A, B):
        assert len(A) == len(B)

        N = A.shape[0]  # total points

        centroid_A = np.mean(A, axis=0)
        centroid_B = np.mean(B, axis=0)

        # centre the points
        AA = A - np.tile(centroid_A, (N, 1))
        BB = B - np.tile(centroid_B, (N, 1))

        # dot is matrix multiplication for array
        H = np.dot(AA.T, BB)
        U, S, Vt = linalg.svd(H)
        R = np.dot(U, Vt)
        return R

    @staticmethod
    def align(mesh1, mesh2, mirror, initial_alignment=None):
        n = len(mesh1.vertices)
        if not initial_alignment:
            initial_alignment = Correspondence.best_pairwise_PCA_alignment(mesh1=mesh1, mesh2=mesh2, mirror=mirror)
        alignDict = Correspondence.locgpd(mesh1=mesh1, mesh2=mesh2, R_0=initial_alignment['r'], M_0=np.ones((n, n)), mirror=mirror)
        return alignDict
