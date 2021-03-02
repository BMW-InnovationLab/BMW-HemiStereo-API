import setuptools
import setuptools.command.build_py
import distutils.cmd
import distutils.command
import os
import re
import subprocess

def concat( dirname, filename ):
    return dirname + "/" + filename

def crawl( dirname ):
    dirs = [ concat( dirname, d ) for d in os.listdir( dirname ) if os.path.isdir( concat( dirname, d ) ) ]
    
    subdirs = []
    for d in dirs:
        subdirs += crawl( d )

    return [dirname] + subdirs

def createInit( dirname ):
    initfile = concat( dirname, "__init__.py" )
    if not os.path.isfile( initfile ):
        #files = [ f for f in os.listdir( dirname ) if os.path.isfile( concat( dirname, f ) ) ]
        #files = [ f[:-3] for f in files if re.match( ".*\.py", f ) ]
        with open( initfile, "w" ) as out:
            pass
            #for f in files:
                #out.write( "from .{} import *\n".format( f ) )
    else:
        print( "init file present in {}, skipping...".format( dirname ) )


with open("README.md", "r") as fh:
    long_description = fh.read()

print( "transforming api..." )
result = subprocess.call("rm -rf hemistereo/api && cp -r api hemistereo/", shell=True)
result = subprocess.call("find hemistereo -name *.proto -exec sed -i '/import \\\"google\/protobuf/b; s/import \\\"/import \\\"hemistereo\/api\//g' {} \\;", shell=True)

print( "generating grpc code..." )
args = " --proto_path=./ --python_out=. --grpc_python_out=. $(find hemistereo -name *proto)"
#args = "--proto_path=./api -I ./api --python_out=hemistereo/api --grpc_python_out=hemistereo/api $(find api/hemistereo/api -name *proto)"
result = subprocess.call("python3 -m grpc_tools.protoc " + args, shell=True)
print( "result", result )

print( "generating init files..." )
dirs = crawl("hemistereo/api")
for d in dirs:
    print( d, "..." )
    createInit(d)

setuptools.setup(
    name="hemistereo",
    version="1.0.2",
    author="3dvisionlabs",
    author_email="support@3dvisionlabs.com",
    description="HemiStereo sample and wrapper module",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.3dvisionlabs.com:3dvisionlabs/software/hemistereo/pythonsdk.git",
    packages = setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
