# Imports
import numpy as np
import matplotlib.pyplot as plt
from astropy.table import Table
from astropy.table import vstack
from astroquery.gaia import Gaia
import tqdm
from astropy.table import join
from scipy.optimize import root_scalar
from astroquery.simbad import Simbad
from ipyaladin import Aladin
from astroquery.casda import Casda
from astropy.coordinates import SkyCoord
from astroquery.utils.tap.core import TapPlus
import astropy.units as u
import anywidget
import ipywidgets
import ipyaladin
import os
import re
import pandas as pd
from pathlib import Path
from astropy.table import unique

# OPAL Login
OPAL_USER = 'jfer9940@uni.sydney.edu.au'
Casda.login(username=OPAL_USER, store_password=True)

# Load in data
sources = Table.read('data/source_obs_data.csv')
star_table = sources[sources['Simbad_ID'] == 'HD   8558']

# CASDA TAP URL
tap = TapPlus(url="https://casda.csiro.au/casda_vo_tools/tap")
cutout_path = '../cutouts/hd8558_cutouts'

# Get source coords
ra = star_table['Archival_ra'][0]
dec = star_table['Archival_dec'][0]

source_coords = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")

# Query for cutouts
image_types = ['I', 'V']
# sbid_list = [50048, 82373, 52548, 66866, 67022]
sbid_list = [13298]
# Query continuum restored images for the requested SBIDs
obs_ids = ",".join(f"'ASKAP-{int(sbid)}'" for sbid in sbid_list)
pol_string = ",".join(f"'/{pol}/'" for pol in image_types)

img_qry = f"""
SELECT *
FROM ivoa.obscore
WHERE obs_id IN ({obs_ids})
AND dataproduct_subtype = 'cont.restored.t0'
AND pol_states IN ({pol_string})
"""

job = tap.launch_job_async(img_qry)
r_detections = job.get_results()
r_detections = Casda.filter_out_unreleased(r_detections)

# Convert to dataframe
r_df = r_detections.to_pandas()

# Retain the existing filename/collection filters
filename = np.array(r_df['filename'], dtype=str)
collection = np.array(r_df['obs_collection'], dtype=str)

mask = (
    (np.char.find(filename, 'raw') == -1) &
    (np.char.find(filename, 'alt') == -1) &
    (np.char.find(filename, 'highres') == -1) &
    (np.char.find(filename, 'iqr') == -1) &
    (np.char.find(collection, 'BETA') == -1)
)

r_df = r_df.loc[mask].copy()

# Download the data in loops
url_loop_length = 5

# The size of the cutout. This will be the length
# of each edge of the square cutout
cutout_width = 1 * u.arcmin

print('Staging the noise files')
clean_url_list = []
r_filenames = np.array(r_df['filename'])
# I'm keeping it to one loop here, for demonstration purposes
for url_ in range((len(r_filenames) + url_loop_length - 1) // url_loop_length):
    url_filenames = r_filenames[url_ * url_loop_length: (url_ + 1) * url_loop_length]
    print(url_filenames)
    url_r_df = r_df[r_df['filename'].isin(url_filenames)]
    url_list = Casda.cutout(Table.from_pandas(url_r_df),
                            coordinates=source_coords, radius=cutout_width)
    # I find it annoying to download the checksum files
    # with the files I actually want
    for row in url_list:
        if 'checksum' not in row:
            clean_url_list.append(row)

    print('Downloading the files')
     # Now we can download that batch of files
    filelist = Casda.download_files(clean_url_list,
                                    savedir=cutout_path)

    # Here I rename the downloaded files. They come out with
    # quite nasty filenames that don't give you wany real info.
    # So I give them back their original names
    for cf, cutf in enumerate(filelist):
        cube_id = 'cube-' + (cutf.split('-imagecube-')[-1]).split('.fits')[0]

        source_row = r_df[r_df['obs_publisher_did'] == cube_id]

        og_name = source_row['filename'].item()

        new_name = os.path.join(cutout_path, og_name)

        os.rename(cutf, new_name)
    # Changing the file names does mean that you'll have to do
    # checks yourself to avoid downloading the same cutout twice
    clean_url_list = []
