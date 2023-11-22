from htj2k.compression import HTJ2K

# com = HTJ2K("./data/CT0.npy")
com = HTJ2K("./data/AA002.dcm")
encode_time = com.compress()
print("encode_time",encode_time)

com = HTJ2K("./data/compressed/AA002.dcm")
com.decompress()