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








if __name__ == '__main__':
    global warehouse_num
    # Connect to database
    conn = psycopg2.connect(
        database = "hfojjoyn",
        user = "hfojjoyn",
        password = "lG-dnQMl1HRXFgTznfCEMrBc-U1RVPy9",
        host = "drona.db.elephantsql.com",
        port = "5432"
    )
    print("Backend connect to database success!")

    # Receive world ID
    # TODO


    # Connect to the world (Warehouse)
    cmd = amazon_pb2.AConnect()
    cmd.worldid = int(wid)  # wid from above, TODO
    cmd.isAmazon = True
    warehouse = cmd.initwh.add()
    with warehouse_lock:
        warehouse.id = warehouse_num
        warehouse_num += 1
    warehouse.x = 3
    warehouse.y = 4
    socket_world = connectWorld(cmd)


    # Connect to Web-server (as a server, Accept)


    #