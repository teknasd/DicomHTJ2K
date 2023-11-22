import numpy as np
import cv2
import os
import subprocess
from enum import Enum
from typing import Union
import tempfile
import pydicom as dcm
from pydicom.encaps import encapsulate
import re

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

    def __init__(self):
        pass

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
        print(os.getcwd())
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
            args += ['-precints', __format_args(precints)]
        if tile_offset:
            args += ['-tile_offset', __format_args(tile_offset)]  
        if tile_size:
            args += ['-tile_size', __format_args(tile_size)] 
        if image_offset:
            args += ['-image_offset', __format_args(image_offset)] 
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
        print(cmd)

        print(output)
        print(output.stdout)
        # return output.stdout
        # If successful, return encode time. Otherwise raise error
        if output.stdout:
            encode_time = float(output.stdout.decode('utf-8').replace('Elapsed time = ', ''))
            print(f"encoded in ... {encode_time} secs")
            return encode_time
        else:
            print("failed")
            raise ValueError(output.stderr.decode('utf-8'))

        


  



class HTJ2K(HTJ2KBase):

    def __init__(self,path = None):
        if path:
            self.path = path
            self.name = self.path.split("/")[-1].split(".")[0]
            self.base_path = os.path.abspath(os.getcwd())
            self.encoded_jph_path = f"{self.base_path}/data/encoded/{self.name}.jph"
            self.compressed_dicom_path = f"{self.base_path}/data/compressed/{self.name}.dcm"
            print(self.base_path)
            # os.makedirs(f'../temp/encoded/', exist_ok=True)

        self.encoder_params = {
        'num_decomps' : 5,
        # 'qstep' : 0.0039,
        'reversible' : True,
        # 'color_trans' : True,
        'prog_order' : ProgressionOrder.RPCL,
        'block_size' : (32,32),
        # 'precints' : None,
        # 'tile_offset' : None,
        # 'tile_size' : None,
        # 'image_offset' : None,
        'tileparts' : Tileparts.R,
        'tlm_marker' : True,
        }   


    def _compress(self,
        filename : str,
        img : np.ndarray, 
        strict : bool = False,
        **kwargs,
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
                encode_time = super().compress(temp.name, filename, **kwargs)
                print("encode_time >>>",encode_time)
                temp.flush()
            return encode_time



    def _decompress(self):
        pass


    def compress(self):
        if self.path.endswith(".dcm"):
            dicom = dcm.dcmread(self.path)
            print(dicom.file_meta.TransferSyntaxUID)
            print(dicom.file_meta.TransferSyntaxUID.name)
            print(dicom.BitsAllocated)
            img = dicom.pixel_array
            np.save(self.path.replace(".dcm",".npy"), img)
        else:
            img = np.load(f'{self.path}')
        print(img.shape)
        filename = self.encoded_jph_path
        encode_time = self._compress(
        filename = filename,
        img = img,
        strict = False,
        num_decomps = self.encoder_params['num_decomps'],
        # qstep = encoder_params['qstep'],
        reversible = self.encoder_params['reversible'],
        # color_trans = encoder_params['color_trans'],
        prog_order = self.encoder_params['prog_order'],
        block_size = self.encoder_params['block_size'],
        # precints = encoder_params['precints'],
        # tile_offset = encoder_params['tile_offset'],
        # tile_size = encoder_params['tile_size'],
        # image_offset = encoder_params['image_offset'],
        tileparts = self.encoder_params['tileparts'],
        tlm_marker = self.encoder_params['tlm_marker'],
        )


        if type(encode_time) == float:
            frame_data = []
            print(os.getcwd())
            filename = self.encoded_jph_path    
            with open(filename, 'rb') as f:
                data = f.read()
            frame_data.append(data)
            encapsulated_data = encapsulate(frame_data)
            dicom.PixelData = encapsulated_data
            from pydicom.uid import JPEG2000,UID 
            JPEG2000MCLossless = UID("1.2.840.10008.1.2.4.96")
            dicom.file_meta.TransferSyntaxUID = UID('HTJ2K')
            # dicom.save_as('./data/new.dcm')
            dicom.save_as(self.compressed_dicom_path)

        return encode_time


    def decompress(self):
        pass


def decoded_bytes(filename):
  """
  Calculates the number of bytes decoded using location of tile-part markers in bytestream

  ## Arguments:
  filename : str
    Path to HTJ2K file

  ## Returns:
  array-like : 
    Size (in bytes) for each tile-part arranged by progression order
  """
  SOT = b'\xff\x90'
  EOI = b'\xff\xd9'
  with open(filename, 'rb') as f:
    bytes = np.array([i.start() for i in re.finditer(b'|'.join((SOT, EOI)), f.read())][1:])
  return bytes
  
def subresolution(resolution, decomposition):
  """
  Calculates sub-resolution of decomposition

  ## Arguments:
  resolution : array-like
    Resolution of image (x,y)
  decomposition : int
    Decomposition level (zero-indexed)

  ## Returns:
  array-like : 
    Sub-resolution i.e resolution of image at given decomposition level (x,y)
  """
  x, y = resolution
  return x // 2**decomposition, y // 2**decomposition

