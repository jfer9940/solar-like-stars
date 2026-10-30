import numpy as np
import matplotlib.pyplot as plt
from astropy.table import Table
from astropy.table import vstack
from astroquery.simbad import Simbad
from astroquery.casda import Casda
from astropy.coordinates import SkyCoord
from astroquery.utils.tap.core import TapPlus
import astropy.units as u
import os
import re

# Credentials
OPAL_USER = 'jfer9940@uni.sydney.edu.au'
Casda.login(username=OPAL_USER, store_password=True)
print('Credentials accepted')

# Load in the source data
sources = Table.read('data/source_obs_data.csv')
print('Sources loaded')

# Get SkyCoords for our sources
source_coords = []
for i in range(0, len(sources)):
    ra = sources[i]['Archival_ra']
    dec = sources[i]['Archival_dec']
    coords = SkyCoord(ra = ra*u.deg, dec = dec*u.deg, frame='icrs')
    source_coords.append(coords)
print('Coords loaded')

# Logging file for errors
log_file = f"../visibility_files/failed_staging.log"

# CASDA TAP URL
tap = TapPlus(url="https://casda.csiro.au/casda_vo_tools/tap")

# Query the correct data
for coord, src in zip(source_coords, sources['Simbad_ID']):

    # Find any data for this source
    ra = coord.ra.deg
    dec = coord.dec.deg

    tap_qry = ( f"SELECT * FROM ivoa.obscore "
                f"where dataproduct_type='visibility' "
                f"AND 1=CONTAINS(POINT('ICRS', {ra}, {dec}), "
                f"circle('ICRS', s_ra,s_dec, 0.7))")

    job = tap.launch_job_async(tap_qry)
    r = job.get_results()

    # Filter for data I can access
    public_data = Casda.filter_out_unreleased(r)

    # Mask to only get the correct data types/observation lengths
    min_exptime = 60*60 # 1 Hour minimum time
    dataproduct_type = 'visibility' # We want visibility data
    mask = (public_data['dataproduct_type'] == dataproduct_type) & (public_data['t_exptime'] >= min_exptime) # & (np.char.startswith(public_data['filename'], 'scienceData'))
    filtered = public_data[mask]

    # Ensure we only take the closest beam's data
    unique_obs = np.unique(filtered['obs_id']) 
    best_rows = []
    for obs in unique_obs:
        rows = filtered[filtered['obs_id'] == obs]
        min_index = 0 # just take the first one for now
        best_rows.append(rows[min_index])

    # Return a table of visibility files we want to download
    if len(best_rows) > 0:
        result = vstack(best_rows)
    else:
        print(f'No visibility data for {src}')
        continue

    # Create a place to put the data in
    folder_name = re.sub(r'[^a-z0-9_-]', '', src.lower().replace(" ", "_"))
    dir_name = f'../visibility_files/{folder_name}'

    # Download each file into a different folder
    for i in range(0, len(result)):
        row = Table(result[i])
        obs_name = str(row['target_name'][0]).lower()
        try:
            url_list = Casda.stage_data(row)
        except Exception as e:
            print(f"Staging failed for {row}: {e}")
            with open(log_file, "a") as f:
                f.write(f"{obs_name} | {str(e)}\n")
            continue
        savedir = f'{dir_name}/{obs_name}'

        # Skip if folder already exists and is not empty
        if os.path.exists(savedir) and len(os.listdir(savedir)) > 0:
            print(f"Skipping {folder_name}/{obs_name} (already downloaded)")
            continue

        # If it doesn't exist, create it
        os.makedirs(savedir, exist_ok=True)

        # Download the data
        try:
            file_list = Casda.download_files(url_list, savedir=savedir)
            print(f'Downloading {folder_name}/{obs_name}')
        except Exception as e:
            print(f"Downloading failed for {obs_name}: {e}")
            with open(log_file, "a") as f:
                f.write(f"{obs_name} | {str(e)}\n")
            continue
