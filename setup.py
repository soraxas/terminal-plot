from setuptools import setup

setup(
    name='tensorboard-termplot',
    version='1.0.0',
    description='View tensorboard stats inside terminal.',
    author='Tin Lai (@soraxas)',
    author_email='oscar@tinyiu.com',
    license='MIT',
    url='https://github.com/soraxas/tensorboard-termplot',
    keywords='tui tensorboard termplot stats',
    python_requires='>=3.6',
    packages=['tensorboard_termplot'],
    install_requires=[
        'tensorboard',
        'plotext',
    ],
    entry_points={
        'console_scripts': [
            'tensorboard-termplot=tensorboard_termplot.main:run'
        ]
    },
    classifiers=[
        'Environment :: Console',
        'Framework :: Matplotlib',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Desktop Environment',
        'Topic :: Terminals',
        'Topic :: Utilities',
    ],

)
