from .api.hemistereo.network.messages import matrix_pb2 as hsmat
from .api.hemistereo.network.messages import basic_pb2 as hsbasic
import numpy as np

def unpackMessageToInt64( message ):
    res = hsbasic.Int64()
    message.payload.Unpack( res )
    return res

def unpackMessageToUInt64( message ):
    res = hsbasic.UInt64()
    message.payload.Unpack( res )
    return res

def unpackMessageToInt32( message ):
    res = hsbasic.Int32()
    message.payload.Unpack( res )
    return res

def unpackMessageToUInt32( message ):
    res = hsbasic.UInt32()
    message.payload.Unpack( res )
    return res

def unpackMessageToFloat( message ):
    res = hsbasic.Float()
    message.payload.Unpack( res )
    return res

def unpackMessageToDouble( message ):
    res = hsbasic.Double()
    message.payload.Unpack( res )
    return res

def unpackMessageToBool( message ):
    res = hsbasic.Bool()
    message.payload.Unpack( res )
    return res

def unpackMessageToString( message ):
    res = hsbasic.String()
    message.payload.Unpack( res )
    return res

def unpackMessageToMat( message ):
    mat = hsmat.Matrix()
    message.payload.Unpack( mat )
    return mat

def unpackMessageToNumpy( message ):
    res = unpackMessageToMat( message )
    dtype=None
    if res.depth == 4:
        dtype = np.uint16
    elif res.depth == 9:
        dtype = np.float32
    else:
        dtype = np.uint8
    return np.fromstring(res.data, dtype=dtype).reshape( res.rows, res.cols, res.channels )

