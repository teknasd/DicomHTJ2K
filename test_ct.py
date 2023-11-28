from htj2k.compression import DicomHTJ2K
import glob
from tqdm import tqdm
# Specify the folder path
folder_path = './data/CT Plain 3mm'

# Use glob to get a list of all files in the folder
files = glob.glob(f'{folder_path}/*.dcm')

# Call the process_file function for each file
for file in tqdm(files, desc="Processing files"):

    if "comp" not in file:
        com = DicomHTJ2K(file)
        com_time = com.compress('RPCL')
        print(f"   compression time: {com_time:.3f} secs")

        # decom = HTJ2K("./data/b8d52e80-c4e3-4a56-b528-286577f0e2d5_comp.dcm",verbose= True)
        decom_time = com.decompress()
        print(f"de-compression time: {decom_time:.3f} secs")

        print(f"   compression ratio: {com.compression_ratio:.3f} ")