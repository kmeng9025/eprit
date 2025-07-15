from nptdms import TdmsFile
import numpy as np
import scipy.io as sio
import os

def process_raw_file(tdms_path, output_dir):
    """
    Processes a raw .tdms file and saves it as a .mat file.

    Args:
        tdms_path (str): The path to the .tdms file.
        output_dir (str): The directory to save the .mat file in.
    """
    try:
        tdms_file = TdmsFile.read(tdms_path)
        mat_dict = {}
        for group in tdms_file.groups():
            for channel in group.channels():
                channel_name = channel.name
                data = channel[:]
                mat_dict[channel_name] = data

        # Save the data under a specific key
        processed_data = {'processed_data': mat_dict}

        base_filename = os.path.basename(tdms_path)
        mat_filename = os.path.splitext(base_filename)[0] + ".mat"
        output_path = os.path.join(output_dir, mat_filename)
        sio.savemat(output_path, processed_data)
        print(f"Successfully converted {tdms_path} to {output_path}")

    except Exception as e:
        print(f"Error processing {tdms_path}: {e}")

if __name__ == '__main__':
    # Example usage:
    tdms_file_path = 'DATA/241202/8475image4D_18x18_0p75gcm_file.tdms'
    output_directory = 'pipeline'
    process_raw_file(tdms_file_path, output_directory)
