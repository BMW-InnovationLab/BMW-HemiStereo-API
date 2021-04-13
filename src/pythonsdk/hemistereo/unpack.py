from .api.hemistereo.network.messages import matrix_pb2 as hsmat
from .api.hemistereo.network.messages import capturemetadata_pb2 as hsmeta
from .api.hemistereo.network.messages import message_pb2 as hsmsg
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

def unpackMessageToMessageMap( message ):
    msgMap = hsmsg.MessageMap()
    message.data.payload.Unpack(msgMap)
    res = {}
    for k in msgMap.map.keys():
        res[k] = msgMap.map.get(k)
    return res

def unpackMessageToMeta( message ):
    meta = hsmeta.CaptureMetadata()
    message.payload.Unpack( meta )
    return meta

def unpackMessageToMat( message ):
    mat = hsmat.Matrix()
    message.payload.Unpack( mat )
    return mat

def unpackMessageToNumpy( message ):
    mat = unpackMessageToMat( message )
    dtype=None
    if mat.depth == 4:
        dtype = np.uint16
    elif mat.depth == 9:
        dtype = np.float32
    else:
        dtype = np.uint8
    return np.fromstring(mat.data, dtype=dtype).reshape( mat.rows, mat.cols, mat.channels )
