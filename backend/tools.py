import socket
import threading
import select
import psycopg2
import IG1_pb2
import world_amazon_pb2

from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint

UPSHOST, UPSPORT = "vcm-14348.vm.duke.edu",33333
WHOST, WPORT = "vcm-14348.vm.duke.edu",23456

# send google protocol buffer message through socket
# args: (socket, protocol buffer object)
# return: None
def send_msg(socket,msg):
    to_send = msg.SerializeToString()
    _EncodeVarint(socket.sendall,len(to_send))
    socket.sendall(to_send)

# recv serialized message through socket
# args: (socket)
# return: a serialized string
def recv_msg(socket):
    var_int_buff = []
    while True:
        buf = socket.recv(1)
        var_int_buff += buf
        msg_len, new_pos = _DecodeVarint32(var_int_buff, 0)
        if new_pos != 0:
            break
    whole_message = socket.recv(msg_len)
    return whole_message

# Connect to world
# args: (protocol buffer object)
# return: socket_world
def connectWorld(cmd):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    world_ip = socket.gethostbyname(WHOST)
    s.connect((world_ip,WPORT))
    send_msg(s,cmd)
    connect_reply = world_amazon_pb2.AConnected()
    connect_reply.ParseFromString(recv_msg(s))

    print("world id: ")
    print(connect_reply.worldid)
    print("result: ")
    print(connect_reply.result)
    # s is socket_world
    return s

# Connect to database
# args: None
# return: the connection
def connect_db():
    conn = psycopg2.connect(
        database="hfojjoyn",
        user="hfojjoyn",
        password="lG-dnQMl1HRXFgTznfCEMrBc-U1RVPy9",
        host="drona.db.elephantsql.com",
        port="5432"
    )
    print("Backend connect to database success!")
    return conn

# Receive world id， and connect to UPS
# args: None
# return: socket_UPS, world_id
def recv_worldid():
    socket_UPS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_UPS.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    socket_UPS.connect((UPSHOST, UPSPORT))
    initmsg = IG1_pb2.UMsg()
    initmsg.ParseFromString(recv_msg(socket_UPS))
    wid = initmsg.initworld.worldid
    ack = initmsg.initworld.seq
    ack_to_UPS(socket_UPS,ack)
    return socket_UPS, wid


# Ack to world
# args: (socket, ack)
# return: None
def ack_to_world(s,ack):
    ack_cmd = world_amazon_pb2.ACommands()
    ack_cmd.acks.append(ack)
    send_msg(s,ack_cmd)

# Ack to UPS
# args: (socket, ack)
# return: None
def ack_to_UPS(s,ack):
    ack_msg = IG1_pb2.AMsg()
    ack_msg.acks.append(ack)
    send_msg(s,ack_msg)
