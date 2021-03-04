PythonSDK
=========


This library should serve as starting point and example on how to use the application service / gRPC interface of the
HemiStereo applications. It depends on the hemistereo/api repository to generate protobuf files.

If you are using the HemiStereo platform for the first time and/or just bought a new sensor for testing, consider to
install 3dvl-jupyter on the sensor, this comes with a full python environment and some examples for getting you started.
Please refer to the [documentation](https://docs.3dvisionlabs.com/hs-nx/software/python_getting_started.html) for
instructions on how to install it.

Release
-------

These files are containing the proto-buf generated sources as well: 
[Release Page](https://git.3dvisionlabs.com/3dvisionlabs/software/hemistereo/pythonsdk/-/releases/1.0.2)

Clone the repository
--------------------

It is strongly advisable to clone the repository including the "api" sub-repository, please use the following
command for cloning:

~~~.bash
git clone --recurse-submodules https://git.3dvisionlabs.com/3dvisionlabs/software/hemistereo/pythonsdk.git
~~~

Installation
------------

Make sure you checked out the git-submodule "api", and check the folder contents. There should be ```*.proto``` files in
there.

Using pip:

~~~~.bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install .
~~~~

This should install the dependencies (from  requirements.txt), build and install the project to your local python site-packages.

Troubleshooting
---------------

- pip install did return OK, but you experience problems during ```import hemistereo```, issuing ```python3 setup.py
  build``` may give more detailed information on what is going on.

- pip is "confused": if you are installing some modules from apt repositories and some via pip. If
  you observe issues which show version discrepancies, we highly recommend using only pip as installation source. If you
  installed e.g. python3-protobuf via apt (e.g.  automatically as dependency of some other project), you may either: (A)
  install a python virtual environment 
  ([external link](https://uoa-eresearch.github.io/eresearch-cookbook/recipe/2014/11/26/python-virtual-env/))
  and all requirements in
  there or (B) use a user-private pip-only installation, which can be "forced" by e.g. ```pip3 install --reinstall
  protobuf```, which will be of higher priority than the apt package.

- different python versions may be competing: make sure not to switch between different python3 versions during package
  installation. We also saw a case where the system's python interpreter was a python3.7 and the pip package has been
  installed via apt for python3.6. This setup created severe problems. Better use ```python3 -m pip``` for selecting the
  correct pip for your python interpreter.

- protobuf files (python stubs) are not generated: ```import hemistereo``` shows errors like ```ImportError: cannot
  import name 'application_pb2_grpc'``` (or something else with pb2 and grpc in the name). Either there are issues with
  the protobuf and grpcio-tools installation or something went wrong while checking out the git-submodule "api", please
  make sure these steps succeeded.

Usage
-----

For a detailed usage description, please refer to the [HemiStereo online documentation](https://docs.3dvisionlabs.com/hs-nx/software/python_getting_started.html).

Contact
-------

If you have further questions, requests or experience any issues with the modules, please reach out to us: support@3dvisionlabs.com.
