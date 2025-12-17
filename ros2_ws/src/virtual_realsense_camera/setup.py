from setuptools import find_packages, setup

package_name = 'virtual_realsense_camera'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='root@todo.todo',
    description='Virtual RealSense-like camera node',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'virtual_camera_node = virtual_realsense_camera.virtual_camera_node:main',
            'virtual_color_camera_node = virtual_realsense_camera.virtual_color_camera_node:main',
            'virtual_depth_camera_node = virtual_realsense_camera.virtual_depth_camera_node:main',
            'rgbd_image_saver = virtual_realsense_camera.image_saver_node:main',
            'http_camera_bridge = virtual_realsense_camera.http_camera_bridge_node:main',
        ],
    },
)
