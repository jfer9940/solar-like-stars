import argparse
from pathlib import Path
import os

# -----------------------------
# Be a good HPC citizen
# -----------------------------

os.nice(19)

# -----------------------------
# Parse command line arguments
# -----------------------------
parser = argparse.ArgumentParser(description="Process visibility data")
parser.add_argument("--sb_path", required=True, type=str,
                    help="Path to SB folder, e.g., /.../flash_348")
parser.add_argument("--ms_file", required=True, type=str,
                    help="Name of measurement set file")
parser.add_argument("--ra", required=True, type=str,
                    help="Right Ascension (proper motion corrected)")
parser.add_argument("--dec", required=True, type=str,
                    help="Declination (proper motion corrected)")
parser.add_argument("--ds_name", required=True, type=str,
                    help="Name for output .ds file")
parser.add_argument("--band", required=True, type=str)

args = parser.parse_args()

# -----------------------------
# Initialize paths
# -----------------------------
SB_path = Path(args.sb_path)
ms_file = args.ms_file
RA_corPM = args.ra
Dec_corPM = args.dec
DS_name = args.ds_name
obs_band = args.band

ms_path = SB_path / ms_file
print(ms_path)
# -----------------------------
# Preprocessing and create model
# -----------------------------
os.chdir(SB_path)
wsclean_model_path = SB_path / 'wsclean_model'
wsclean_model_exists = wsclean_model_path.exists()
print('wsclean_model path:', wsclean_model_path, 'exists:', wsclean_model_exists)

model_file_exists = False
if wsclean_model_exists:
    model_file_path = wsclean_model_path / 'wsclean-MFS-I-model.fits'
    model_file_exists = model_file_path.exists()
    print('model_file path:', model_file_path, 'exists:', model_file_exists)

if not model_file_exists:
    print(f"Missing necessary files, starting {ms_file} create-model")

    cmd1 = f"dstools-askap-preprocess {ms_path}"
    print(f"Executing: {cmd1}")
    result1 = os.system(cmd1)
    print("Preprocessing completed" if result1 == 0 else f"Failed, return code {result1}")

    cmd2 = f"dstools-create-model -v -B {obs_band} {ms_path}"
    print(f"Executing: {cmd2}")
    result2 = os.system(cmd2)
    print("Model creation completed" if result2 == 0 else f"Failed, return code {result2}")
else:
    print(f"{ms_file} create-model already completed, skipping processing")

# -----------------------------
# Insert model and subtract
# -----------------------------
subtracted_ms_files = [f for f in os.listdir(SB_path) if f.endswith('.subtracted.ms')]
subtracted_ms_file = SB_path / subtracted_ms_files[0] if subtracted_ms_files else None

if not subtracted_ms_files:
    print(".subtracted.ms file does not exist, executing insert & subtract commands")

    cmd3 = f"dstools-insert-model -p {RA_corPM} {Dec_corPM} {wsclean_model_path} {ms_path}"
    print(f"Executing: {cmd3}")
    result3 = os.system(cmd3)
    print("Model insert completed" if result3 == 0 else f"Failed, return code {result3}")

    cmd4 = f"dstools-subtract-model -S {ms_path}"
    print(f"Executing: {cmd4}")
    result4 = os.system(cmd4)
    print("Model subtract completed" if result4 == 0 else f"Failed, return code {result4}")
else:
    print(".subtracted.ms file exists, skipping processing")

# -----------------------------
# Extract model
# -----------------------------
subtracted_ms_files = [f for f in os.listdir(SB_path) if f.endswith('.subtracted.ms')]
subtracted_ms_file = SB_path / subtracted_ms_files[0] if subtracted_ms_files else None

cmd5 = f"dstools-extract-ds -u 500 -p {RA_corPM} {Dec_corPM} {subtracted_ms_file} {SB_path / (DS_name + '.ds')}"
print(f"Executing: {cmd5}")
result5 = os.system(cmd5)
print("Model extract completed" if result5 == 0 else f"Failed, return code {result5}")
