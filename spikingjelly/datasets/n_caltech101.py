from typing import Any, Callable, cast, Dict, List, Optional, Tuple
import numpy as np
import spikingjelly.datasets as sjds
from torchvision.datasets.utils import extract_archive
import os
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import time
from ..configure import max_threads_number_for_datasets_preprocess


class NCaltech101(sjds.NeuromorphicDatasetFolder):
    def __init__(
            self,
            root: str,
            data_type: str = 'event',
            frames_number: int = None,
            split_by: str = None,
            duration: int = None,
            custom_integrate_function: Callable = None,
            custom_integrated_frames_dir_name: str = None,
            transform: Optional[Callable] = None,
            target_transform: Optional[Callable] = None,
    ) -> None:
        '''
        :param root: root path of the dataset
        :type root: str
        :param data_type: `event` or `frame`
        :type data_type: str
        :param frames_number: the integrated frame number
        :type frames_number: int
        :param split_by: `time` or `number`
        :type split_by: str
        :param duration: the time duration of each frame
        :type duration: int
        :param custom_integrate_function: a user-defined function that inputs are ``events, H, W``.
            ``events`` is a dict whose keys are ``['t', 'x', 'y', 'p']`` and values are ``numpy.ndarray``
            ``H`` is the height of the data and ``W`` is the weight of the data.
            For example, H=128 and W=128 for the DVS128 Gesture dataset.
            The user should define how to integrate events to frames, and return frames.
        :type custom_integrate_function: Callable
        :param custom_integrated_frames_dir_name: The name of directory for saving frames integrating by ``custom_integrate_function``.
            If ``custom_integrated_frames_dir_name`` is ``None``, it will be set to ``custom_integrate_function.__name__``
        :type custom_integrated_frames_dir_name: str or None
        :param transform: a function/transform that takes in
            a sample and returns a transformed version.
            E.g, ``transforms.RandomCrop`` for images.
        :type transform: callable
        :param target_transform: a function/transform that takes
            in the target and transforms it.
        :type target_transform: callable

        If ``data_type == 'event'``
            the sample in this dataset is a dict whose keys are ``['t', 'x', 'y', 'p']`` and values are ``numpy.ndarray``.

        If ``data_type == 'frame'`` and ``frames_number`` is not ``None``
            events will be integrated to frames with fixed frames number. ``split_by`` will define how to split events.
            See :class:`spikingjelly.datasets.cal_fixed_frames_number_segment_index` for
            more details.

        If ``data_type == 'frame'``, ``frames_number`` is ``None``, and ``duration`` is not ``None``
            events will be integrated to frames with fixed time duration.

        If ``data_type == 'frame'``, ``frames_number`` is ``None``, ``duration`` is ``None``, and ``custom_integrate_function`` is not ``None``:
            events will be integrated by the user-defined function and saved to the ``custom_integrated_frames_dir_name`` directory in ``root`` directory.
            Here is an example from SpikingJelly's tutorials:

            .. code-block:: python

                from spikingjelly.datasets.dvs128_gesture import DVS128Gesture
                from typing import Dict
                import numpy as np
                import spikingjelly.datasets as sjds
                def integrate_events_to_2_frames_randomly(events: Dict, H: int, W: int):
                    index_split = np.random.randint(low=0, high=events['t'].__len__())
                    frames = np.zeros([2, 2, H, W])
                    frames[0] = sjds.integrate_events_segment_to_frame(events, H, W, 0, index_split)
                    frames[1] = sjds.integrate_events_segment_to_frame(events, H, W, index_split, events['t'].__len__())
                    return frames

                root_dir = 'D:/datasets/DVS128Gesture'
                train_set = DVS128Gesture(root_dir, train=True, data_type='frame', custom_integrate_function=integrate_events_to_2_frames_randomly)

                from spikingjelly.datasets import play_frame
                frame, label = train_set[500]
                play_frame(frame)
        '''
        super().__init__(root, None, data_type, frames_number, split_by, duration, custom_integrate_function, custom_integrated_frames_dir_name, transform, target_transform)
    @staticmethod
    def resource_url_md5() -> list:
        '''
        :return: A list ``url`` that ``url[i]`` is a tuple, which contains the i-th file's name, download link, and MD5
        :rtype: list
        '''
        url = 'https://www.garrickorchard.com/datasets/n-caltech101'
        return [
            ('Caltech101.zip', url, '66201824eabb0239c7ab992480b50ba3'),
            ('Caltech101_annotations.zip', url, '25e64cea645291e368db1e70f214988e'),
            ('ReadMe(Caltech101)-SINAPSE-G.txt', url, 'd464b81684e0af3b5773555eb1d5b95c'),
            ('ReadMe(Caltech101).txt', url, '33632a7a5c46074c70509f960d0dd5e5')
        ]

    @staticmethod
    def downloadable() -> bool:
        '''
        :return: Whether the dataset can be directly downloaded by python codes. If not, the user have to download it manually
        :rtype: bool
        '''
        return False

    @staticmethod
    def extract_downloaded_files(download_root: str, extract_root: str):
        '''
        :param download_root: Root directory path which saves downloaded dataset files
        :type download_root: str
        :param extract_root: Root directory path which saves extracted files from downloaded files
        :type extract_root: str
        :return: None

        This function defines how to extract download files.
        '''
        zip_file = os.path.join(download_root, 'Caltech101.zip')
        print(f'Extract [{zip_file}] to [{extract_root}].')
        extract_archive(zip_file, extract_root)


    @staticmethod
    def load_origin_data(file_name: str) -> Dict:
        '''
        :param file_name: path of the events file
        :type file_name: str
        :return: a dict whose keys are ``['t', 'x', 'y', 'p']`` and values are ``numpy.ndarray``
        :rtype: Dict

        This function defines how to read the origin binary data.
        '''

        return sjds.load_ATIS_bin(file_name)

    @staticmethod
    def get_H_W() -> Tuple:
        '''
        :return: A tuple ``(H, W)``, where ``H`` is the height of the data and ``W` is the weight of the data.
            For example, this function returns ``(128, 128)`` for the DVS128 Gesture dataset.
        :rtype: tuple
        '''
        return 180, 240

    @staticmethod
    def read_bin_save_to_np(bin_file: str, np_file: str):
        events = NCaltech101.load_origin_data(bin_file)
        np.savez(np_file,
                 t=events['t'],
                 x=events['x'],
                 y=events['y'],
                 p=events['p']
                 )
        print(f'Save [{bin_file}] to [{np_file}].')


    @staticmethod
    def create_events_np_files(extract_root: str, events_np_root: str):
        '''
        :param extract_root: Root directory path which saves extracted files from downloaded files
        :type extract_root: str
        :param events_np_root: Root directory path which saves events files in the ``npz`` format
        :type events_np_root:
        :return: None

        This function defines how to convert the origin binary data in ``extract_root`` to ``npz`` format and save converted files in ``events_np_root``.
        '''
        t_ckp = time.time()
        extract_root = os.path.join(extract_root, 'Caltech101')
        with ThreadPoolExecutor(max_workers=min(multiprocessing.cpu_count(), max_threads_number_for_datasets_preprocess)) as tpe:
            # too many threads will make the disk overload
            for class_name in os.listdir(extract_root):
                bin_dir = os.path.join(extract_root, class_name)
                np_dir = os.path.join(events_np_root, class_name)
                os.mkdir(np_dir)
                print(f'Mkdir [{np_dir}].')
                for bin_file in os.listdir(bin_dir):
                    source_file = os.path.join(bin_dir, bin_file)
                    target_file = os.path.join(np_dir, os.path.splitext(bin_file)[0] + '.npz')
                    print(f'Start to convert [{source_file}] to [{target_file}].')
                    tpe.submit(NCaltech101.read_bin_save_to_np, source_file,
                               target_file)


        print(f'Used time = [{round(time.time() - t_ckp, 2)}s].')
