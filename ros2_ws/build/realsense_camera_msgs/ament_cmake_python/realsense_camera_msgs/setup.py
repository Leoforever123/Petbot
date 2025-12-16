from setuptools import find_packages
from setuptools import setup

setup(
    name='realsense_camera_msgs',
    version='2.0.4',
    packages=find_packages(
        include=('realsense_camera_msgs', 'realsense_camera_msgs.*')),
)
