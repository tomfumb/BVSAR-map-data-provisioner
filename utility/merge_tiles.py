import os
import re

from PIL import Image


overlay_dir = "/Users/tc/data/personal/BVSAR/provisioning/output/canvec_trans"
base_dir = "/Users/tc/data/personal/BVSAR/provisioning/output/google_hybrid_LTEyOC4xMTUzLjg0MzMtMTI2LjA3NDk1NS43ODgxNjE4"
out_dir = "/Users/tc/data/personal/BVSAR/provisioning/output/google_canvec"

for subdir, dirs, files in os.walk(overlay_dir):
    file_count = 0
    file_count_total = len(files)
    for file in files:
        file_count += 1
        if re.match(r"\d+\.png", file):
            overlay_file = os.path.join(subdir, file)
            relative_path = overlay_file.replace(overlay_dir, "")
            save_file = "{0}{1}".format(out_dir, relative_path)
            if os.path.exists(save_file):
                print ("skipping {0}/{1} {2}".format(file_count, file_count_total, save_file))
            else:
                print ("overlaying {0}/{1} {2}".format(file_count, file_count_total, save_file))
                overlay_image = Image.open(overlay_file).convert("RGBA")
                base_file = "{0}{1}".format(base_dir, relative_path)
                base_image = Image.open(base_file)
                for i in range(256):
                    for j in range(256):
                        coord = (i,j)
                        values = overlay_image.getpixel(coord)
                        if values[3] > 0:
                            base_image.putpixel(coord, values)

                save_dir = "/".join(save_file.split("/")[:-1])
                os.makedirs(save_dir, exist_ok=True)
                base_image.quantize(method=2).save(save_file)
