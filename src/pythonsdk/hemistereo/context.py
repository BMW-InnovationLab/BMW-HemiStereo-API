from .api.hemistereo.network.services import application_pb2_grpc as hsapp
from .api.hemistereo.network.services import application_pb2 as hsapp_msg
import netifaces
import grpc
import numpy as np

class Context:
    def __init__( self, appname = "stereo", server = None, port="8888" ):
        if not server:
            gateways = netifaces.gateways()
            if not "default" in gateways or len(gateways["default"]) == 0:
                raise Exception( "no server specified and default route cannot be determined, please provide a sensor ip address manually" )
            for x in gateways["default"]:
                server = gateways["default"][x][0]
            print( "no server given, using this sensor: " + server )
        if not isinstance( appname, str ):
            raise Exception( "Context.__init__: 'appname' must be a string, got '{}'".format( type( appname ) ) )
        if not isinstance( server, str ):
            raise Exception( "Context.__init__: 'server' must be a string, got '{}'".format( type( server ) ) )
        self.server = server + ":" + port
        self.metadata = [("app", appname )]
        self.chan = grpc.insecure_channel( self.server,
                    options=[
                ('grpc.max_send_message_length', -1),
                ('grpc.max_receive_message_length', -1),
            ])
        self.stub = hsapp.ApplicationServiceStub( self.chan )
        self.activeTopics = []

    def getApplication( self ):
        req = hsapp_msg.GetApplicationRequest()
        return self.stub.GetApplication( request=req, metadata=self.metadata)

    def setReadTopicEnabled( self, topic, enabled = True  ):
        if topic not in self.activeTopics and enabled == True:
            req = hsapp_msg.SetReadTopicEnabledRequest(path=topic, value=True)
            self.stub.SetReadTopicEnabled(request = req, metadata = self.metadata)
            self.activeTopics.append( topic )
        elif enabled == False:
            req = hsapp_msg.SetReadTopicEnabledRequest(path=topic, value=False)
            self.activeTopics = [ x for x in self.activeTopics if x != topic ]
            self.stub.SetReadTopicEnabled(request = req, metadata = self.metadata)

    def readTopic( self, topic ):
        self.setReadTopicEnabled( topic )
        req = hsapp_msg.ReadTopicRequest( path = topic )
        return self.stub.ReadTopic(request = req, metadata = self.metadata )

    def writeTopic( self, topic, value ):
        req = hsapp_msg.WriteTopicRequest( path = topic, data = value )
        return self.stub.ReadTopic(request = req, metadata = self.metadata )

    def getProperty( self, prop ):
        req = hsapp_msg.GetPropertyRequest( path = prop )
        return self.stub.GetProperty(request = req, metadata = self.metadata)

    def setProperty( self, prop, value ):
        if isinstance( value, np.int32 ):
            req = hsapp_msg.SetPropertyRequest( path = prop, value_int32 = value )
        elif isinstance( value, np.int64 ):
            req = hsapp_msg.SetPropertyRequest( path = prop, value_int64 = value )
        elif isinstance( value, np.uint32 ):
            req = hsapp_msg.SetPropertyRequest( path = prop, value_uint32 = value )
        elif isinstance( value, np.uint64 ):
            req = hsapp_msg.SetPropertyRequest( path = prop, value_uint64 = value )
        elif isinstance( value, str):
            req = hsapp_msg.SetPropertyRequest( path = prop, value_string= value )
        elif isinstance( value, np.float32):
            req = hsapp_msg.SetPropertyRequest( path = prop, value_float = value )
        elif isinstance( value, np.float64):
            req = hsapp_msg.SetPropertyRequest( path = prop, value_double = value )
        elif isinstance( value, np.bool):
            req = hsapp_msg.SetPropertyRequest( path = prop, value_bool = value )
        elif isinstance(value, int):
            req = hsapp_msg.SetPropertyRequest( path = prop, value_enum = np.int32( value ) )
        else:
            raise Exception( "type not supported: {}".format( type( value ) ) )
        return self.stub.SetProperty(request = req, metadata = self.metadata)
