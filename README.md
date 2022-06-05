# SAMS Align

## Installation
1. Go to https://github.com/hkirvesl/Auto3dgm-matlab **TODO** replace with wherever our installation goes
2. Click Clone/Download -> Download ZIP
3. Save somewhere and unzip
4. Open up the command line to the SAMS Align directory
5. Run the following command to install dependancies
```
pip install -r requirements.txt
```

## Running SAMS Align
1. Open up the command line to the SAMS Align directory
2. Run the following command
```
python SAMS_align.py
```
Note: Depending on the installation of python, the command could be `python3` instead of `python`

3. Follow the steps from the popup dialog
4. After alignment finishes, a dialog will pop up to visualize the meshes.

## Additional Options

If you want to skip the interface, you can simply comment out the command `inter.setSettings()` in SAMS_align.py at the bottom of the page and uncomment `inter.alignMeshController()`. This will use the settings.json file for the settings.