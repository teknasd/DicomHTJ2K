
## What is DicomHTJ2K ?
This is python tool to encode and decode High-Throughput JPEG 2000 (HTJ2K) dicoms. Based on [OpenJPH](https://github.com/aous72/OpenJPH) which is written in C++ and [openjphpy](https://github.com/UM2ii/openjphpy) which is a py wrapper. DicomHTJ2K package coming soon...


**Note: This is an experimental repository.**

## Why use DicomHTJ2K ?
If you want to save storage cost (compression ratio) and not compromise user experience (encode/decode time) htj2k promises to solve both the issues.


## Resources

For more resources regarding HTJ2K, please refer to:
- [HTJ2K White Paper](http://ds.jpeg.org/whitepapers/jpeg-htj2k-whitepaper.pdf)
- [High throughput JPEG 2000 (HTJ2K): Algorithm, performance and potential](https://htj2k.com/wp-content/uploads/white-paper.pdf)
- [High throughput block coding in the HTJ2K compression standard](http://kakadusoftware.com/wp-content/uploads/icip2019.pdf) 



## Which transfer syntax to use ?
Dicom standards recently introduced new transfer syntax for htj2k encodings [link](https://dicom.nema.org/medical/dicom/current/output/html/part05.html#sect_8.2.14)

| Transfer Syntax UID            | Description                      | 
|---------------------------------|----------------------------------|
| 1.2.840.10008.1.2.4.201          | HTJ2K (Lossless Only)            |
| 1.2.840.10008.1.2.4.202          | HTJ2K (Lossless RPCL)            |
| 1.2.840.10008.1.2.4.203          | HTJ2K                            |


## How to use ?

```
from htj2k.compression import DicomHTJ2K

com = DicomHTJ2K("./data/chest_xray.dcm")
com_time = com.compress('RPCL')
print(f"   compression time: {com_time:.3f} secs")

decom_time = com.decompress()
print(f"de-compression time: {decom_time:.3f} secs")

print(f"   compression ratio: {com.compression_ratio:.3f} ")
```

**Note: Currently only works on 8 bit and 16 bit images.**

Please contact for more details / discussions / suggestions / improvements / bugs / support on github issues or on teknas97@gmail.com. 
