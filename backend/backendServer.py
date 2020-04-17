import socket
import threading
import select
import psycopg2

from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint

# IP and port for backend server
HOST, PORT = socket.gethostbyname(socket.gethostname()), 33333

# IP and port for world (warehouse)
WHOST, WPORT = "vcm-12452.vm.duke.edu", 23456

# IP and port for UPS
# TODO
UPSHOST, UPSPORT = "vcm-12452.vm.duke.edu", 22222

# warehouse number
warehouse_num = 1
warehouse_lock = threading.Lock()

# ship id
ship_id = 1
ship_id_lock = threading.Lock()

# sequence number
seqnum = 1
seq_lock = threading.Lock()

# A dict stores <seqnum, ACommand> for world
commands_to_world = {}

# TODO
# Socket connecting to world (necessary?)
socket_world = -1

# APutOnTruck Waitlist
APutOnTruck_WL = []

# A dict stores <shipid, APutOnTruck> for UPS

# send google protocol buffer message through socket
# args: (socket, protocol buffer object)
# return: None
def send_msg(socket,msg):
    temp = []
    to_send = msg.SerializeToString()
    _EncodeVarint(temp.append,len(to_send))
    socket.sendall("".join(temp))
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
    connect_reply = amazon_pb2.AConnected()
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
    ack_cmd = amazon_pb2.ACommands()
    ack_cmd.acks.append(ack)
    send_msg(s,ack_cmd)

# Ack to UPS
# args: (socket, ack)
# return: None
def ack_to_UPS(s,ack):
    ack_msg = IG1_pb2.AMsg()
    ack_msg.acks.append(ack)
    send_msg(s,ack_msg)





if __name__ == '__main__':
    global warehouse_num
    # Connect to database
    conn = connect_db()

    # Receive world ID and connect to UPS
    # TODO
    socket_UPS, wid = recv_worldid()

    # Connect to the world (Warehouse)
    cmd = amazon_pb2.AConnect()
    cmd.worldid = int(wid)  # wid from above, TODO
    cmd.isAmazon = True
    warehouse = cmd.initwh.add()
    with warehouse_lock:
        warehouse.id = warehouse_num
        warehouse_num += 1
    warehouse.x = 8
    warehouse.y = 8
    socket_world = connectWorld(cmd)

    # Connect to Web-server (as a server, Accept)


    #