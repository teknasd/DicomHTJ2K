from htj2k.compression import HTJ2K

# com = HTJ2K("./data/CT0.npy")
com = HTJ2K("./data/b8d52e80-c4e3-4a56-b528-286577f0e2d5.dcm")
encode_time = com.compress()
print("encode_time",encode_time)

decom = HTJ2K("./data/b8d52e80-c4e3-4a56-b528-286577f0e2d5_comp.dcm",verbose=True)
decom.decompress()

res = (com.raw_arr == decom.raw_arr).all()
print(res)

'''
comparing md5 hash comp and decomp files as byte wise validation
'''
import hashlib

def calculate_md5(file_path):
    """Calculate the MD5 hash of a file."""
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as file:
        # Read the file in chunks to handle large files
        for chunk in iter(lambda: file.read(4096), b''):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def compare_md5(file1_path, file2_path):
    """Compare the MD5 hash values of two files."""
    md5_file1 = calculate_md5(file1_path)
    md5_file2 = calculate_md5(file2_path)

    return md5_file1 == md5_file2


if compare_md5(com.path, decom.decompressed_dicom_path):
    print("MD5 hashes match. The files are identical.")
else:
    print("MD5 hashes do not match. The files are different.")


'''
compare sizes
'''

import os

def compare_file_sizes(file1_path, file2_path):
    """Compare the sizes of two files."""
    size_file1 = os.path.getsize(file1_path)
    size_file2 = os.path.getsize(file2_path)
    print(f"size_file1: {size_file1} \nsize_file2: {size_file2}")
    return size_file1 == size_file2

if compare_file_sizes(com.path, decom.decompressed_dicom_path):
    print("File sizes match. The files have the same size.")
else:
    print("File sizes do not match. The files have different sizes.")


import os
import pydicom
def compare_img_sizes(file1_path, file2_path):
    """Compare the sizes of two files."""
    size_file1 = os.path.getsize(file1_path)
    size_file2 = os.path.getsize(file2_path)
    ds1 = pydicom.dcmread(file1_path).PixelData
    ds2 = pydicom.dcmread(file2_path).PixelData
    print(f"size_file1: {size_file1} \nsize_file2: {size_file2}")
    print(f"size_img1: {len(ds1)} \nsize_img2: {len(ds2)}")
    ds1 = pydicom.dcmread(file1_path).pixel_array
    ds2 = pydicom.dcmread(file2_path).pixel_array
    print(f"size_img1: {ds1.shape} \nsize_img2: {ds2.shape}")

    return size_file1 == size_file2

if compare_img_sizes(com.path, decom.decompressed_dicom_path):
    print("File sizes match. The files have the same size.")
else:
    print("File sizes do not match. The files have different sizes.")


'''
positional comparision
'''

# def find_first_difference(file1_path, file2_path):
#     """Find the position of the first differing byte in two files."""
#     with open(file1_path, 'rb') as file1, open(file2_path, 'rb') as file2:
#         position = 0
#         byte1 = file1.read()
#         byte2 = file2.read()
#         # print(byte1[:340])
#         # print(byte2[:340])
#         print("sizeof bytes: ",len(byte1), len(byte2))
#         print("matching bytes: ",byte1[:1990] == byte2[:1990])

#         # # Check if both files have reached the end
#         # if not byte1 and not byte2:
#         #     return None  # Files are identical

#         # # If one file has reached the end before the other, or bytes differ
#         # if not byte1 or not byte2 or byte1 != byte2:
#         #     print(byte1,byte2)
#         #     return position

#         position += 1

# position_of_difference = find_first_difference(com.path, decom.decompressed_dicom_path)

# if position_of_difference is None:
#     print("Files are identical.")
# else:
#     print(f"Files differ at byte position {position_of_difference}.")


'''
compare tags
'''

# import pydicom

# def compare_dicom_files(file1_path, file2_path):
#     """Compare DICOM tags of two files and generate a report."""
#     report = []

#     # Load DICOM datasets from files
#     ds1 = pydicom.dcmread(file1_path,stop_before_pixels= True)
#     ds2 = pydicom.dcmread(file2_path,stop_before_pixels = True)

#     # Compare tags and values
#     # all_tags = [tag for tag in dir(ds1) if not callable(getattr(ds1, tag)) and not tag.startswith("_")]
#     all_tags = [tag for tag in dir(ds1) if tag[0].isupper()]
#     print("all_tags",all_tags)
#     for tag in all_tags:
#         value1 = getattr(ds1, tag, None)
#         value2 = getattr(ds2, tag, None)

#         if value1 != value2:
#             report.append(f"failed on Tag {tag} : {value1} vs {value2}")
#         else:
#             report.append(f"success on Tag {tag}  : {value1} vs {value2}")

#     return report

# # Example usage
# file1_path = 'path/to/your/file1.dcm'
# file2_path = 'path/to/your/file2.dcm'

# comparison_report = compare_dicom_files(com.path, decom.decompressed_dicom_path)

# if not comparison_report:
#     print("DICOM files are identical.")
# else:
#     print("DICOM files differ. Comparison report:")
#     for entry in comparison_report:
#         print(entry)
