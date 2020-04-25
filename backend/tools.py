import socket
import threading
import select
import psycopg2
import IG1_pb2
import world_amazon_pb2

from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint

##################################global variables###################################################

# sequence number for messages to send
seq_num = 1
seq_lock = threading.Lock()

# A dict stores <seq_num, ACommand> for world
toWorld = {}
# the lock for the dict
toworld_lock = threading.Lock()

# A dict stores <seq_num, AMsg> for UPS
toUPS = {}
#the lock for the dict
toUPS_lock = threading.Lock()

#for connection with UPS and World
UPSHOST, UPSPORT = "vcm-14579.vm.duke.edu",33333
WHOST, WPORT = "vcm-14579.vm.duke.edu",23456

#################################global variables#####################################################

###################### helper functions for send and recv messages(including send acks) #####################

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
    print("=====Recv message:\n"+str(whole_message))
    return whole_message

# recv serialized message with timeout
# args: (socket, timeout(in second))
# return: a serialized string (normal), or empty string(if timeout is reached)
def recv_msg_timeout(socket,timeout):
    var_int_buff = []
    ready = select.select([socket], [], [], timeout)
    if ready[0]:
        while True:
            buf = socket.recv(1)
            var_int_buff += buf
            msg_len, new_pos = _DecodeVarint32(var_int_buff, 0)
            if new_pos != 0:
                break
        whole_message = socket.recv(msg_len)
        return whole_message
    return ""

# Ack to world
# args: (socket, ack)
# return: None
def ack_to_world(s,ack):
    ack_cmd = world_amazon_pb2.ACommands()
    ack_cmd.acks.append(ack)
    ack_cmd.disconnect = False
    send_msg(s,ack_cmd)

# Ack to UPS
# args: (socket, ack)
# return: None
def ack_to_UPS(s,ack):
    ack_msg = IG1_pb2.AMsg()
    ack_msg.acks.append(ack)
    send_msg(s,ack_msg)

################################# helper functions for send and recv messages############################


#################################connect to UPS, WORLD, DB #############################################

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
        database="oryhumzm",
        user="oryhumzm",
        password="1cv9iF1fSqRoes-F9NHEUe2FnbSdWJY2",
        host="drona.db.elephantsql.com",
        port="5432"
    )
    print("Backend connect to database success!")
    return conn

#################################connect to UPS, WORLD, DB #############################################

#########################generate ACommands############################

#insert into toWorld
#args: (seq_num(全局变量), msg)
def add_toWorld(msg):
    global seq_num
    toWorld[seq_num]=msg
    seq_num=seq_num+1

# generate APurchasemore command to world from orders(from database)
def generate_buy(conn):
    cursor = conn.cursor()
    # append purchase more Acommand to the  global dict toWorld
    # fetch one product that is not enough in the warehouse
    sql = '''SELECT item_id,item_name FROM amazon_web_order WHERE is_enough = FALSE;'''
    cursor.execute(sql)
    buying_product = cursor.fetchone()
    if buying_product:
        print("Generate APurchaseMore")
        # calculate the number of this particular product we need to buy from the world
        # update the is_enough field to true
        sql = '''SELECT pkgid, purchase_num FROM amazon_web_order WHERE is_enough = FALSE AND item_id = %s;'''
        cursor.execute(sql, (buying_product[0],))
        wh_purchase_num = 0
        orders = cursor.fetchall()
        for order in orders:
            wh_purchase_num += order[1]
            sql = '''UPDATE amazon_web_order SET is_enough = TRUE WHERE pkgid = %s;'''
            cursor.execute(sql, (order[0],))
            conn.commit()
        # generate ACommands
        Acmd = world_amazon_pb2.ACommands()
        Acmd.disconnect = False
        tobuy = Acmd.buy.add()
        tobuy.whnum = 1  # we only have one warehouse currently
        tobuy.seqnum = seq_num
        item = tobuy.things.add()
        item.id = buying_product[0]
        item.description = buying_product[1]
        item.count = wh_purchase_num # buy exactly the orders need
        return Acmd
    return None

def generate_pack(order):
    print("Generate APack")
    Acmd = world_amazon_pb2.ACommands()
    Acmd.disconnect = False
    topack = Acmd.topack.add()
    topack.whnum = 1
    topack.shipid = order[0]
    topack.seqnum = seq_num
    item = topack.things.add()
    item.id = order[8]
    item.description = order[7]
    item.count = order[9]
    return Acmd

def generate_load(order):
    print("Generate APutOnTruck")
    Acmd = world_amazon_pb2.ACommands()
    Acmd.disconnect = False
    toload = Acmd.load.add()
    toload.whnum = 1
    toload.truckid = order[1]
    toload.shipid = order[0]
    toload.seqnum = seq_num
    return Acmd

def generate_query(order):
    print("Generate AQuery")
    Acmd = world_amazon_pb2.ACommands()
    Acmd.disconnect = False
    query = Acmd.queries.add()
    query.packageid = order[0]
    query.seqnum = seq_num
    return Acmd

#########################generate ACommands############################

#########################generate AMsgs################################

#insert into toUPS
#args: (seq_num(全局变量), msg)
def add_toUPS(msg):
    global seq_num
    toUPS[seq_num]=msg
    seq_num=seq_num+1

def generate_asendtruck(order):
    print("Generate ASendTruck")
    Amsg = IG1_pb2.AMsg()
    tosend = Amsg.asendtruck.add()
    tosend.whinfo.whid = 1
    tosend.whinfo.x = 10
    tosend.whinfo.y = 10
    tosend.x = order[4]
    tosend.y = order[5]
    tosend.pkgid = order[0]
    tosend.upsid = order[3]
    tosend.seq = seq_num
    product = tosend.products.add()
    product.id = order[8]
    product.description = order[7]
    product.count = order[9]
    return Amsg

def generate_afinishloading(order):
    print("Generate AFinishLoading")
    Amsg = IG1_pb2.AMsg()
    tosend = Amsg.afinishloading.add()
    tosend.pkgid = order[0]
    tosend.truckid = order[1]
    tosend.seq = seq_num
    return Amsg

#########################generate AMsgs#################################
