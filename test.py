from htj2k.compression import HTJ2K

# com = HTJ2K("./data/CT0.npy")
com = HTJ2K("./data/b8d52e80-c4e3-4a56-b528-286577f0e2d5.dcm")
encode_time = com.compress()
print("encode_time",encode_time)

decom = HTJ2K("./data/b8d52e80-c4e3-4a56-b528-286577f0e2d5_comp.dcm")
decom.decompress()

res = (com.raw_arr == decom.raw_arr).all()
print(res)