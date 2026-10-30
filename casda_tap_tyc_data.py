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

# Get our data for HD 104919
hd104919_table = sources[sources['Simbad_ID'] == 'TYC 8927-1888-1']

# Logging file for errors
log_file = f"../visibility_files/failed_staging.log"

# CASDA TAP URL
tap = TapPlus(url="https://casda.csiro.au/casda_vo_tools/tap")

# Get source coords
ra = hd104919_table['Archival_ra'][0]
dec = hd104919_table['Archival_dec'][0]

# Retrieve data
tap_qry = ( f"SELECT * FROM ivoa.obscore "
            f"where dataproduct_type='visibility' "
            f"AND 1=CONTAINS(POINT('ICRS', {ra}, {dec}), "
            f"circle('ICRS', s_ra,s_dec, 0.7))")

job = tap.launch_job_async(tap_qry)
r = job.get_results()

# Filter for data I can access
public_data = Casda.filter_out_unreleased(r)

# Mask to only get the correct data type (i think this is redundant but oh well)
dataproduct_type = 'visibility'
mask = (public_data['dataproduct_type'] == dataproduct_type)
filtered = public_data[mask]

# Download each file into a different folder

dir_name = f'../visibility_files/tyc_8927-1888-1'

for i in range(0, len(filtered)):
    row = Table(filtered[i])
    obs_name = str(row['obs_id'][0]).lstrip('ASKAP-')
    try:
        url_list = Casda.stage_data(row)
    except Exception as e:
        print(f"Staging failed for {row}: {e}")
        with open(log_file, "a") as f:
            f.write(f"{obs_name} | {str(e)}\n")
        continue
    savedir = f'{dir_name}/{obs_name}'
    print(savedir)

    # Skip if folder already exists and is not empty
    if os.path.exists(savedir) and len(os.listdir(savedir)) > 0:
        print(f"Skipping {dir_name}/{obs_name} (already downloaded)")
        continue

    # If it doesn't exist, create it
    os.makedirs(savedir, exist_ok=True)

    # Download the data
    try:
        file_list = Casda.download_files(url_list, savedir=savedir)
        print(f'Downloaded {dir_name}/{obs_name}')

    except Exception as e:
        print(f"Downloading failed for {row}: {e}")
        with open(log_file, "a") as f:
            f.write(f"{obs_name} | {str(e)}\n")
        continue
