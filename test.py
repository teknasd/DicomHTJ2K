from htj2k.compression import HTJ2K

com = HTJ2K("./data/b8d52e80-c4e3-4a56-b528-286577f0e2d5.dcm")
com_time = com.compress('RPCL')
print(f"   compression time: {com_time:.3f} secs")

decom = HTJ2K("./data/b8d52e80-c4e3-4a56-b528-286577f0e2d5_comp.dcm")
decom_time = decom.decompress()
print(f"de-compression time: {decom_time:.3f} secs")

print(f"   compression ratio: {com.compression_ratio:.3f} ")