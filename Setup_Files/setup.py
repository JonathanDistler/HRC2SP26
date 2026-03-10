from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'stretch_init_pose'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),

        ('share/' + package_name, ['package.xml']),

        # Install config files
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
    ],
    install_requires=['setuptools', 'pyyaml'],
    zip_safe=True,
    maintainer='hello-robot',
    maintainer_email='calebschaefer19@gmail.com',
    description='Stretch robot navigation to named locations',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
    'console_scripts': [
        'initial_pose = stretch_init_pose.initial_pose_publisher:main',
        'goto_location = stretch_init_pose.goto_location:main',
    ],
},
)
