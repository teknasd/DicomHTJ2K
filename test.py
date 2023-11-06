from compression import HTJ2K

com = HTJ2K("./data/CT0.npy")
encode_time = com.compress()
print("encode_time",encode_time)