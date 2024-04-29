# Auto3dgm_Python

Auto3dgm_Python is an end-to-end implementation of Auto3dgm in Python. Compared to previous releases, Auto3dgm_Python contains 1) a GUI for ease of initiating analyses, 2) interactive visualization for quick check of alignment success, 3) multi-core processing architecture for more rapid analysis

Please see instructions.pdf for installation help

NEW: DataCleaningScript.py will attempt to clean your data. It is highly recommended that you run this prior to Auto3dgm_Python. Once you edit the meshDir and outputDir variables to reflect your data path, it will go through every mesh, clean and smooth them, and output them into one of four categories: meshes that could not be cleaned (badMeshes), disc topology meshes, sphere topology meshes, and other 2-manifold meshes that are not simply connected. **It is highly recommended that you only work with meshes coming from one of the four output folders, and not mixing the contents of the folders.** Note that MacOS users have experienced some issues with completing this script. The specific reason is unknown as of writing.
