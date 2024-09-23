'''
PRE-REQUISITES:

1. DOWNLOAD MATTERPORT PROJECT
$ python matterport-dl.py "https://my.matterport.com/show/?m=<ID>"  # --no-main-asset-download

2. use matterport-decoder to convert .dam files to .obj
# (or https://github.com/willowpsychology/rogue_matterport_archiver)
$ git clone https://github.com/codespacehelp/matterport-decoder.git
$ node matterport-decoder/parse.js <dam-filepath>

3. INSTALL CUBE2SPHERE and BLENDER
- https://pypi.org/project/cube2sphere
- requires Blender added to PATH

4. now run this script.
'''

import os
import shutil
import subprocess
from PIL import Image
from tqdm import tqdm


dimensions = (4096, 2048)
rotation = (0, 0, 180)
downloads_dir = "downloads"
fname = "spherical"
ext = "png"


# Get all directories in the "downloads" directory
matterport_dirs = [d for d in os.listdir(downloads_dir) if os.path.isdir(os.path.join(downloads_dir, d))]
for matterport_id in tqdm(matterport_dirs, desc="Processing Matterport directories"):
    matterport_dir = f"downloads/{matterport_id}"

    models_dir = f"{matterport_dir}/models"
    model_dirs = os.listdir(models_dir)
    
    # Select the first directory
    model_id = model_dirs[0]
    assets_dir = f"{models_dir}/{model_id}/assets"
    pano_dir = os.path.join(assets_dir, "pan/2k/_")
    pano_outdir = os.path.join(assets_dir, "spherical")
    os.makedirs(pano_outdir, exist_ok=True)

    pano_id_list = []
    pano_files = os.listdir(pano_dir)
    for filename in pano_files:
        if "_" in filename:
            split_part = filename.split("_")[0]
            pano_id_list.append(split_part)

    # Remove duplicates by converting the list to a set and back to a list
    pano_id_list = list(set(pano_id_list))

    # Create the spherical images for each ID
    for pano_id in tqdm(pano_id_list, desc=f"Processing panoramas in {matterport_id}"):
        pano_path = os.path.join(pano_dir, f"{pano_id}")

        front = f"{pano_path}_skybox3.jpg"
        back = f"{pano_path}_skybox1.jpg"
        right = f"{pano_path}_skybox2.jpg"
        left = f"{pano_path}_skybox4.jpg"
        top = f"{pano_path}_skybox0.jpg"
        bottom = f"{pano_path}_skybox5.jpg"

        fpath = os.path.join(pano_outdir, f"{pano_id}_{fname}")

        command = ["cube2sphere", front, back, right, left, top, bottom,
                "-r", str(dimensions[0]), str(dimensions[1]), 
                "-R", str(rotation[0]), str(rotation[1]), str(rotation[2]),
                "-f", ext, "-o", fpath]

        subprocess.run(command)

        # Convert PNG to JPG
        png_path = f"{fpath}0001.{ext}"

        with Image.open(png_path) as img:
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(f"{fpath}.jpg", "JPEG", quality=95)

        # Delete the original PNG file
        os.remove(png_path)


    # Get the filename without the extension for the *.dam file in assets_dir
    dam_file = next((f for f in os.listdir(assets_dir) if f.endswith('.dam')), None)
    if dam_file:
        dam_filename = os.path.splitext(dam_file)[0]
    else:
        print(f"No .dam file found in {assets_dir}")
        continue


    # Move "spherical" directory from "assets_dir" to "downloads/{matterport_id}"
    spherical_src = pano_outdir
    spherical_dst = f"downloads/{matterport_id}/spherical"
    shutil.move(spherical_src, spherical_dst)


    # Move *.obj and *.mtl files from "assets_dir" to "downloads/{matterport_id}/3D"
    obj_file = os.path.join(assets_dir, f"{dam_filename}.obj")
    mtl_file = os.path.join(assets_dir, f"{dam_filename}.mtl")
    dst_3d_dir = f"downloads/{matterport_id}/3D"
    os.makedirs(dst_3d_dir, exist_ok=True)

    if os.path.exists(obj_file):
        shutil.move(obj_file, dst_3d_dir)
    if os.path.exists(mtl_file):
        shutil.move(mtl_file, dst_3d_dir)


    # Move matching files from texture directory to 3D directory
    texture_dir = os.path.join(assets_dir, f"_/{dam_filename}_texture_jpg_high")
    if os.path.exists(texture_dir):
        for file in os.listdir(texture_dir):
            if file.startswith(f"{dam_filename}_") and file.endswith(".jpg") and len(file) == len(f"{dam_filename}_000.jpg"):
                src_file = os.path.join(texture_dir, file)
                dst_file = os.path.join(dst_3d_dir, file)
                shutil.move(src_file, dst_file)


    # Assuming spherical_dst and dst_3d_dir are defined earlier in the script
    spherical_dst = os.path.abspath(spherical_dst)
    dst_3d_dir = os.path.abspath(dst_3d_dir)


    # Delete everything else
    for item in os.listdir(f"downloads/{matterport_id}"):
        item_path = os.path.abspath(os.path.join(f"downloads/{matterport_id}", item))
        
        if item_path not in [spherical_dst, dst_3d_dir]:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
