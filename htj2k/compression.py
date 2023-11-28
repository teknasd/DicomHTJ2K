import numpy as np
import cv2
import os
import subprocess
from enum import Enum
from typing import Union
import tempfile
import pydicom as dcm
from pydicom.encaps import encapsulate,decode_data_sequence
import re
from pydicom.uid import JPEG2000,UID,ImplicitVRLittleEndian
from pydicom._uid_dict import UID_dictionary
import copy
import warnings
# https://dicom.nema.org/medical/dicom/current/output/html/part05.html#sect_8.2.14
'''
'1.2.840.10008.1.2.4.201': ('HTJ2K (Lossless Only)', 'Transfer Syntax', 'Default Transfer Syntax for DICOM', '', 'HTJ2K_Lossless_Only'),
'1.2.840.10008.1.2.4.202': ('HTJ2K (Lossless RPCL)', 'Transfer Syntax', 'Default Transfer Syntax for DICOM', '', 'HTJ2K_Lossless_RPCL'),
'1.2.840.10008.1.2.4.203': ('HTJ2K', 'Transfer Syntax', 'Default Transfer Syntax for DICOM', '', 'HTJ2K')
'''

HTJ2K_TRANSFER_SYNTAX_LIST_CODES = ['1.2.840.10008.1.2.4.201','1.2.840.10008.1.2.4.202','1.2.840.10008.1.2.4.203']
HTJ2K_TRANSFER_SYNTAX_LIST_NAMES = ['HTJ2K (Lossless Only)','HTJ2K (Lossless RPCL)','HTJ2K', 'Transfer Syntax']

class ProgressionOrder(Enum):
    """
    Collection of progression orders supported by OpenJPH.
    According to the JPEG 2000 codec, progression order lets you specify the order in which packets will appear in a given file and may have a significant impact on the time and memory usage required to encode and/or decode the image. Default is RPCL.
    """
    LRCP = 'LRCP'
    RLCP = 'RLCP'
    RPCL = 'RPCL'
    PCRL = 'PCRL'
    CPRL = 'CPRL'

class Tileparts(Enum):
    """
    Collection of tilepart grouping supported by OpenJPH.
    According to the JPEG 2000 codec, tileparts define the group of packets that are written together. Tile parts can be grouped by resolution (R), layer, or component (C), depending on which progression order you use. By default, no grouping option is selected and the file is written sequentially.
    """
    R = 'R'
    C = 'C'
    RC = 'RC'
class HTJ2KBase():

    def __init__(self,verbose):
        self.verbose = verbose

    def __format_args(self,
        x : Union[np.ndarray, tuple, list],
        ) -> str:
        """
        Formats comma-separated sequence of values for OpenJPH interpretation.

        ## Arguments
        x (array-like): 
        Sequence of values paired values {x,y},{x,y},...,{x,y}

        ## Returns
        str : 
        Formatted comma-separated sequence of values
        """
        x = np.array(x, dtype=int)
        if x.ndim == 1:
            x = np.expand_dims(x, axis=0)
        formatted_str = []
        for x_i in x:
            if len(x_i) != 2:
                raise ValueError('Invalid value! Input must be a sequence of two comma-separated values, enclosed within curly braces. See usage.')
        formatted_str += [f'{{{x_i[0]},{x_i[1]}}}']
        return ','.join(formatted_str)

    def compress(
        self,
        input_path : str,
        output_path : str,
        num_decomps : int = 5,
        qstep : float = 0.0039,
        reversible : bool = False,
        color_trans : bool = True,
        prog_order : ProgressionOrder = ProgressionOrder.RPCL,
        block_size : Union[np.ndarray, tuple[int, int], list[int]] = (64,64),
        precints : Union[np.ndarray, list[tuple[int,int]]] = None,
        tile_offset : Union[np.ndarray, tuple[int, int], list[int]] = None,
        tile_size : Union[np.ndarray, tuple[int, int], list[int]] = None,
        image_offset : Union[np.ndarray, tuple[int, int], list[int]] = None,
        tileparts : Tileparts = None,
        tlm_marker : bool = False,
        ) -> float:
        """
        Python wrapper for OpenJPH's :func:`ojph_compress`.

        ## Arguments
        input_path : str 
            Input file name (either pgm or ppm)
        output_path : str
            Output file name
        num_decomps : int, optional
            Number of decompositions. Defaults to 5.
        qstep : float, optional
            Quantization step size for lossy compression; quantization steps size for all subbands are derived from this value. Defaults to 0.0039 for 8-bit images.
        reversible : bool, optional
            This should be false to perform lossy compression using the 9/7 wavelet transform; or true to perform reversible compression, where the 5/3 wavelet is employed with lossless compression. Defaults to False.
        color_trans : bool, optional
            This option employs a color transform, to transform RGB color images into the YUV domain. This option should not be used with YUV images, because they have already been transformed. If there are three color components that are downsampled by the same amount then the color transform can be true or false. This option is also available when there are more than three colour components, where it is applied to the first three colour components. It has already been applied to convert the original RGB or whatever the original format to YUV. Defaults to True.
        prog_order : backend.ProgressionOrder, optional
            Progression order and can be one of: LRCP, RLCP, RPCL, PCRL, CPRL. Defaults to RPCL. See :func:`ProgressionOrder` for more details.
        block_size : array-like, optional
            {x,y} where x and y are the height and width of a codeblock. Defaults to (64,64).
        precints : array-like, optional
            {x,y},{x,y},...,{x,y} where {x,y} is the precinct size starting from the coarest resolution; the last precinct is repeated for all finer resolutions.
        tile_offset : array-like, optional 
            {x,y} tile offset.
        tile_size : array-like, optional
            {x,y} tile width and height..
        image_offset : array-like, optional
            {x,y} image offset from origin.
        tileparts : backend.Tileparts, optional
            Employs tilepart divisions at each resolution, indicated by the letter R, and/or component, indicated by the letter C. By default, no grouping option is selected and the file is written sequentially.
        tlm_marker : bool, optional
            Inserts a TLM markers in bytestream. Defaults to False.

        ## Returns
        float : 
            Time taken to encode image data.
        """  
        if self.verbose: print(os.getcwd())
        # Construct arguments using default values
        args = [
            './ojph_compress',
            '-i', f'{input_path}',
            '-o', f'{output_path}',
            '-num_decomps', f'{num_decomps}'.lower(),
            '-prog_order', prog_order.value,
            '-block_size', self.__format_args(block_size),
            '-tlm_marker', f'{tlm_marker}'.lower(),
        ]
        # Only apply color transform from RGB to YUV for 3-channel ppm images
        if '.ppm' in input_path:
            args += [
            '-colour_trans', f'{color_trans}'.lower(),
            ]
        # Only include quantization step if lossless/non-reversible
        if reversible == True:
            args += [
            '-reversible', 'true',
            ]
        elif reversible == False:
            args += [
            '-qstep', f'{qstep}',
            '-reversible', 'false',
            ]
        else:
            raise ValueError('Invalid value! `reversible` must be a boolean')
        # Add optional arguments as needed
        if precints:
            args += ['-precints', self.__format_args(precints)]
        if tile_offset:
            args += ['-tile_offset', self.__format_args(tile_offset)]  
        if tile_size:
            args += ['-tile_size', self.__format_args(tile_size)] 
        if image_offset:
            args += ['-image_offset', self.__format_args(image_offset)] 
        if tileparts:
            args += ['-tileparts', tileparts.value]
        # Execute `ojph_compress` in background

        # Get the current working directory
        original_cwd = os.getcwd()

        # Change the CWD to your project's root directory
        project_root = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_root)
        output = subprocess.run(
            args,
            capture_output = True
        )
        os.chdir(original_cwd)
        cmd = " ".join(args)
        if self.verbose: print(cmd)
        if self.verbose: print(output)
        if self.verbose: print(output.stdout)
        # return output.stdout
        # If successful, return encode time. Otherwise raise error
        if output.stdout:
            encode_time = float(output.stdout.decode('utf-8').replace('Elapsed time = ', ''))
            if self.verbose: print(f"encoded in ... {encode_time} secs")
            return encode_time
        else:
            if self.verbose: print("Process failed")
            raise ValueError(output.stderr.decode('utf-8'))

    def decompress(self,
        input_path : str,
        output_path : str,
        skip_res : Union[int, np.ndarray, tuple[int,int], list[int]] = None,
        resilient : bool = False,
        ) -> float:
        """
        Python wrapper for OpenJPH's :func:`ojph_expand`.

        ## Arguments
        input_path : str
        input file name
        output_path : str
        output file name (either pgm or ppm)
        skip_res : array-like, optional
        x,y a comma-separated list of two elements containing the number of resolutions to skip. You can specify 1 or 2 parameters; the first specifies the number of resolution for which data reading is skipped. The second is the number of skipped resolution for reconstruction, which is either equal to the first or smaller. If the second is not specified, it is made to equal to the first. Defaults to None.
        resilient : bool, optional
        Makes decoder to be more tolerant of errors in the codestream. Defaults to False.

        ## Returns
        float : 
        Time taken to decode image data.
        """  
        if self.verbose: print("input_path:",input_path)
        # Construct arguments using default values
        args = [
        './ojph_expand',
        '-i', f'{input_path}',
        '-o', f'{output_path}',
        '-resilient', f'{resilient}'.lower(),
        ]
        # Add optional argument as needed
        if skip_res:
            # `skip_res` can be list of two numbrs or just a single number
            if isinstance(skip_res, (list, tuple, np.ndarray)):
                # Check if `skip_res` args are valid before append
                if len(skip_res) != 2:
                    raise ValueError('Invalid value! `skip_res` must be x,y a comma-separated list of two elements containign the number of resolutions to skip')
                    args += [
                    '-skip_res', f'{skip_res[0]},{skip_res[1]}'
                    ]
            else:
                args += [
                '-skip_res', f'{skip_res}'
                ]

        # Get the current working directory
        original_cwd = os.getcwd()

        # Change the CWD to your project's root directory
        project_root = os.path.dirname(os.path.abspath(__file__))
        if self.verbose: print(original_cwd,project_root)
        os.chdir(project_root)
        if self.verbose: print("expand cmd: "," ".join(args))
        # Execute `ojph_expand` in background
        output = subprocess.run(
            args, 
            capture_output=True
            )
        os.chdir(original_cwd)
        # If successful, return decode time. Otherwise raise error
        if output.stdout:
            return float(output.stdout.decode('utf-8').replace('Elapsed time = ', ''))
        else:
            if self.verbose: print("Process failed")
            raise ValueError(output.stderr.decode('utf-8'))
        
class HTJ2K(HTJ2KBase):
    def __init__(self,path = None,verbose :bool = False):
        if path:
            self.path = path
            self.name = self.path.split("/")[-1].split(".")[0]
            self.base_path = os.path.abspath(os.getcwd())
            self.encoded_jph_path = f"{self.base_path}/data/encoded_{self.name}.jph"
            self.compressed_dicom_path = f"{self.base_path}/data/{self.name}_comp.dcm"
            self.decompressed_dicom_path = f"{self.base_path}/data/{self.name}_decomp.dcm"
            self.verbose = verbose
            super().__init__(verbose)

    def _compress(self,
        filename : str,
        img : np.ndarray, 
        encoder_params : dict,
        strict : bool = False,
        ) -> float:
            """
            Encodes array containing image data into HTJ2K bytestream using OpenJPH.

            ## Arguments:
            filename : str 
                Output file name (either jph or j2c for backwards compatibility with JPEG 2000)
            img : np.ndarray 
                An array containing image data. Currently only 8-bit and 16-bit unsigned integers (uint8 and uint16) are supported. If pixel values fall outside the range [0, 65535], an error may be raised (strict mode) or values will be clipped (non-strict mode). Precision is automatically chosen based on image data's dynamic range.
            strict : bool, optional 
                Enables strict mode for encoder. Strict mode stops encoding if paths do not exist or pixel values are being clipped. Defaults to False.
            **kwargs
                Modifies encoder parameters. See documentation for :func:`backend.ojph_compress`.

            ## Returns:
            float : 
                Time taken to encode image data.
            """
            global __PRECISION_WARNING
            # Create parent directory for output file in non-strict mode
            if not strict:
                dirname = os.path.dirname(filename)
                if dirname:
                    os.makedirs(dirname, exist_ok=True)
            # Check precision of input image
            # Due to limitations in this implementation, only uint8 + uint16 are supported
            if img.dtype != np.uint8 or img.dtype != np.uint16:
                min_val, max_val = np.min(img), np.max(img)
                # Check if input image exceeds precision supported by uint16
                if min_val < 0 or max_val > 65535:
                    # Raise error in strict mode. Otherwise, warn once and clip image
                    if strict:
                        raise ValueError('Precision Error! Currently only 8-bit and 16-bit unsigned integers (uint8 and uint16) are supported')
                    else:
                        if not __PRECISION_WARNING:
                            warnings.warn('Precision Warning! Currently only 8-bit and 16-bit unsigned integers (uint8 and uint16) are supported. Pixel values will be clipped in non-strict mode')
                            __PRECISION_WARNING = True
                # Transform input image into correct dtype
                # This automatically clips pixel values in non-strict mode
                if max_val > 255:
                    img = img.astype(np.uint16)
                else:
                    img = img.astype(np.uint8)
            # TODO: Add support for 3-channel ppm files
            # Using temporary files to automatically clear intermediate pgm files
            encode_time = 0
            with tempfile.NamedTemporaryFile(suffix='.pgm', prefix='encode_') as temp:
                # Write intermediate pgm file
                cv2.imwrite(temp.name, img)
                # Encode pgm using backend
                encode_time = super().compress(temp.name, filename, **encoder_params)
                if self.verbose: print("encode_time >>>",encode_time)
                temp.flush()
            return encode_time

    def _decompress(self,
        filename : str,
        **kwargs
        ) -> tuple[np.ndarray, float]:
        """
        Decodes HTJ2K bytestream into array containing image data using OpenJPH.

        ## Arguments:
        filename : str 
            Input file name (either jph or j2c) 
        **kwargs :
            Modifies decoder parameters. See documentation for :func:`backend.ojph_expand`.

        ## Returns:
        np.ndarray :
            An array containing image data.
        float : 
            Time taken to decode image data.
        """
        # Using temporary files to automatically clear intermediate pgm files
        with tempfile.NamedTemporaryFile(suffix='.pgm', prefix='encode_') as temp:
            # Decode to pgm using backend
            decode_time = super().decompress(filename, temp.name, **kwargs)
            # Read intermediate pgm file
            img = cv2.imread(temp.name, cv2.IMREAD_UNCHANGED)
            temp.flush()
        return img, decode_time

    def compress(self,tsyntax = 'HTJ2K'):
        if self.path.endswith(".dcm"):
            dicom = dcm.dcmread(self.path)
            if self.verbose: print(dicom.file_meta.TransferSyntaxUID)
            if self.verbose: print(dicom.file_meta.TransferSyntaxUID.name)
            if self.verbose: print(dicom.BitsAllocated)
            if self.verbose: print(dicom.ImageType)
            # print(f" -------- \n{dicom} \n-------------")
            self.original_size = len(dicom.PixelData)
            if self.verbose: print("size of PixelData :",self.original_size)
            img = dicom.pixel_array
            # np.save(self.path.replace(".dcm",".npy"), img)
        else:
            img = np.load(f'{self.path}')

        self.raw_arr = img
        if self.verbose: print(img.size,img.shape)
        self.encoder_params = {
            'num_decomps' : 5,
        }   
        if tsyntax == "RPCL": # RPCL htj2k compression
            self.encoder_params['reversible'] = True
            self.encoder_params['tileparts'] = Tileparts.R
            self.encoder_params['tlm_marker'] = True
            self.encoder_params['prog_order'] = ProgressionOrder.RPCL
            self.encoder_params['block_size'] = (32,32)
            self.transfer_syntax = '1.2.840.10008.1.2.4.202'
        elif tsyntax == "Lossless":
            self.encoder_params['reversible'] = True
            self.encoder_params['tileparts'] = Tileparts.R
            self.encoder_params['tlm_marker'] = True
            self.encoder_params['prog_order'] = ProgressionOrder.RPCL
            self.encoder_params['block_size'] = (64,64)
            self.transfer_syntax = '1.2.840.10008.1.2.4.201'
        else: #Lossy
            self.encoder_params['reversible'] = False
            self.encoder_params['qstep'] = 0.0039
            self.transfer_syntax = '1.2.840.10008.1.2.4.203'
        



        encode_time = self._compress(
            filename = self.encoded_jph_path,
            img = img,
            strict = False,
            encoder_params = self.encoder_params
        )

        if type(encode_time) == float:
            frame_data = []
            with open(self.encoded_jph_path, 'rb') as f:
                data = f.read()
            frame_data.append(data)
            encapsulated_data = encapsulate(frame_data)
            self.compressed_size = len(encapsulated_data)
            dicom.PixelData = encapsulated_data 
            dicom.file_meta.TransferSyntaxUID = UID(self.transfer_syntax)
            dicom.is_little_endian = True
            dicom.is_implicit_VR = False
            dicom.save_as(self.compressed_dicom_path)
            self.compression_ratio = float(self.original_size) / self.compressed_size
            # print(f" -------- SAVED DICOM FILE : \n{dicom} \n-------------")
        return encode_time

    def decompress(self):
        if self.path.endswith(".dcm"):
            dicom = dcm.dcmread(self.path)
            if self.verbose: print(dicom.file_meta.TransferSyntaxUID)
            if self.verbose: print(dicom.file_meta.TransferSyntaxUID.name)
            if dicom.file_meta.TransferSyntaxUID not in HTJ2K_TRANSFER_SYNTAX_LIST_CODES:
                raise TypeError(f"TransferSyntaxUID is not in {HTJ2K_TRANSFER_SYNTAX_LIST_CODES}")
            if self.verbose: print(dicom.BitsAllocated)
            if self.verbose: print(dicom.ImageType)
            if self.verbose: print(dicom.SOPClassUID)
            if self.verbose: print(f" -------- \n{dicom} \n-------------")
            bin_pix_data = decode_data_sequence(dicom.PixelData)
            if self.verbose: print("list size: ",len(bin_pix_data),type(bin_pix_data))
            if self.verbose: print("byte size: ",len(bin_pix_data[0]),type(bin_pix_data[0]))
            with tempfile.NamedTemporaryFile(suffix='.jph', prefix='encode_',mode='wb') as temp:
                temp.write(bin_pix_data[0])
                if self.verbose: print("temp file stored at:", temp.name)
                img, decode_time = self._decompress(temp.name)
                temp.flush()
            if self.verbose: print(img.size,img.shape,img.dtype)
            self.raw_arr = img
            ## different way to convert img to bytes
            # bin_pix_data = img.tobytes()
            # if self.verbose: print("bin_pix_data",type(bin_pix_data),len(bin_pix_data))
            # frame_data = []
            # frame_data.append(bin_pix_data)
            # encapsulated_data = encapsulate(frame_data)
            dicom.PixelData = img.tobytes()
            if self.verbose: print("size of PixelData :",len(dicom.PixelData))
            dicom.file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
            dicom.save_as(self.decompressed_dicom_path)
            return decode_time
            # print(f" -------- \n{dicom} \n-------------")
        else:
            img = np.load(f'{self.path}')