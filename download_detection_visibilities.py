# Import packages
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

# CASDA setup
OPAL_USER = 'jfer9940@uni.sydney.edu.au'
Casda.login(username=OPAL_USER, store_password=True)
tap = TapPlus(url="https://casda.csiro.au/casda_vo_tools/tap")

# Read in necessary data
sources = Table.read('data/source_obs_data.csv')

detection_table = Table(
    rows=[
        ("CD-31  8535", "VAST", 74341, 0, 0),
        ("CD-75   652", "EMU", 70504, 0, 0),
        ("HD  82533", "RACS", 22462, 0, 0),
        ("HD  82533", "RACS", 22339, 0, 0),
        ("HD  82533", "VAST", 45965, 0, 0),
        ("HD  82533", "VAST", 47044, 0, 0),
        ("HD  82533", "VAST", 49127, 0, 0),
        ("HD 102982", "RACS", 21927, 0, 0),
        ("HD 102982", "VAST", 64834, 0, 0),
        ("HD 102982", "WALLABY", 50099, 0, 0),
        ("HD 104919", "EMU", 55363, 0, 0),
        ("HD 104919", "VAST", 62276, 0, 0),
        ("HD 104919", "VAST", 62277, 0, 0),
        ("HD 156097", "VAST", 50450, 0, 0),
        ("HD 168210", "RACS", 67352, 0, 0),
        ("HD 175897", "EMU", 74285, 0, 0),
        ("HD 217344", "VAST", 64709, 0, 0),
    ],
    names=("StarName", "Survey", "SBID", "RA", "DEC")
)

detection_table["RA"] = np.full(len(detection_table), np.nan, dtype=float)
detection_table["DEC"] = np.full(len(detection_table), np.nan, dtype=float)

for row in detection_table:
    src_name = row['StarName']
    sources_table_row = sources[sources['Simbad_ID'] == src_name]
    row['RA'] = float(sources_table_row['Archival_ra'].value)
    row['DEC'] = float(sources_table_row['Archival_dec'].value)

# Query CASDA for the visibility files
for row in detection_table:

    source_name = row['StarName']
    folder_name = re.sub(r'[^a-z0-9_-]', '', source_name.lower().replace(" ", "_"))
    dir_name = f'../visibility_files/{folder_name}'

    # Get coords
    ra = row['RA']
    dec = row['DEC']

    #SBID
    sbid = row['SBID']
    query_sbid = f'ASKAP-{sbid}'

    # Query CASDA
    tap_qry = ( f"SELECT * FROM ivoa.obscore "
                f"where dataproduct_type='visibility' "
                f"AND 1=CONTAINS(POINT('ICRS', {ra}, {dec}), "
                f"circle('ICRS', s_ra,s_dec, 0.5))"
                f"AND obs_id = '{query_sbid}'")

    job = tap.launch_job_async(tap_qry)
    r = job.get_results()
    public_data = Casda.filter_out_unreleased(r)
    
    # If there is data: Create the directory and download the file
    if len(public_data) > 0:
        obs_name = str(public_data['target_name'][0]).lower()
        savedir = f'{dir_name}/{obs_name}'
        os.makedirs(savedir, exist_ok=True)

        url_list = Casda.stage_data(public_data)
        file_list = Casda.download_files(url_list, savedir=savedir)

    else: 
        print(f"No data for SB{sbid}")

print('Done!')
