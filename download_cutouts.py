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
print('Imported data')

# OPAL Login
OPAL_USER = 'jfer9940@uni.sydney.edu.au'
Casda.login(username=OPAL_USER, store_password=True)

# Load in data
sources = Table.read('data/source_obs_data.csv')
observations = Table.read('data/2026.01.16_12_07_51_SRSC_Var_alldetections.csv')
source_identifiers = Table.read('data/2026.01.16_12_07_51_SRSC_Static.csv')

# Get our list of detections
source_list = list(sources['Simbad_ID'])
source_identifiers = [source_identifiers['Identifier'][source_identifiers['Simbad_ID'] == source][0] for source in source_list]
source_obs = vstack([observations[observations['Identifier'] == ident] for ident in source_identifiers])
source_obs_askap = source_obs[source_obs['Radio_telescope'] == 'ASKAP']

# Cutout preparation
tap = TapPlus(url="https://casda.csiro.au/casda_vo_tools/tap")
cutout_path = '../cutouts/'
obs_ids = list(source_obs_askap['unique_obs_id'])
sb_ids = [f"ASKAP-{obs_id.removeprefix('SB').split('_')[0]}" for obs_id in obs_ids]
print('Ready to start cutouts')

# Cutout loop
for source in sources:
    
    # Source info
    source_coords = SkyCoord(source['Archival_ra']*u.deg, source['Archival_dec']*u.deg)
    source_name = source['Simbad_ID']
    print(f'Starting {source_name}')
    source_name = re.sub(r'[^a-z0-9_-]', '', source_name.lower().replace(" ", "_"))
    
    # Set up the query for stokes V observations
    image_type = 'V'
    tap_qry = (F"SELECT * FROM ivoa.obscore where(pol_states = '/{image_type}/' and "
               F"dataproduct_subtype = 'cont.restored.t0') "
               F"AND 1 = CONTAINS(POINT('ICRS',{source_coords.ra.deg},{source_coords.dec.deg}),s_region)")
    
    # Run the query
    job = tap.launch_job_async(tap_qry)
    r = job.get_results()
    r = Casda.filter_out_unreleased(r)
    
    # Select only the matches
    r_detections = r[np.isin(r['obs_id'], sb_ids)]
    
    # Filter our any other data types that might be in here
    filename = np.array(r_detections['filename'], dtype=str)
    collection = np.array(r_detections['obs_collection'], dtype=str)
    
    mask = (
        (np.char.find(filename, 'raw') == -1) &
        (np.char.find(filename, 'alt') == -1) &
        (np.char.find(filename, 'highres') == -1) &
        (np.char.find(filename, 'iqr') == -1) &
        (np.char.find(collection, 'BETA') == -1)
    )
    
    r_detections = r_detections[mask]
    r_df = r_detections.to_pandas()

    # Download the data in loops
    url_loop_length = 5
    
    # The size of the cutout. This will be the length
    # of each edge of the square cutout
    cutout_width = 4 * u.arcmin
    
    print('Staging the noise files')
    clean_url_list = []
    r_filenames = np.array(r_df['filename'])
    # I'm keeping it to one loop here, for demonstration purposes
    for url_ in np.arange((len(r_filenames) // url_loop_length) + 1)[:2]:
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
        
            new_name = F'{cutout_path}{source_name}_{og_name}'
        
            os.rename(cutf, new_name)
        # Changing the file names does mean that you'll have to do
        # checks yourself to avoid downloading the same cutout twice
        clean_url_list = []
