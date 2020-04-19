import socket
import threading
import select
import psycopg2
import IG1_pb2
import world_amazon_pb2
import tools

from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint

# warehouse id
warehouse_id = 1
warehouse_lock = threading.Lock()

# ship id(pkgid, tracking number)
ship_id = 1
ship_id_lock = threading.Lock()

# sequence number
seqnum = 1
seq_lock = threading.Lock()

# A dict stores <seqnum, ACommand> for world
commands_to_world = {}

# APutOnTruck Waitlist
APutOnTruck_WL = []

# A dict stores <shipid, APutOnTruck> for UPS

#handleUPS
def handleUPS(socket_UPS, conn):
    while True:
        pass

#handleWorld
def handleWorld(socket_world, conn):
    while True:
        pass

if __name__ == '__main__':
    #global warehouse_id
    # Connect to database
    conn = tools.connect_db()

    # Receive world ID and connect to UPS
    # TODO
    socket_UPS, wid = tools.recv_worldid()
    print('receive UPS socket, worldid = (%d)' %(wid))

    # Connect to the world (Warehouse)
    cmd = world_amazon_pb2.AConnect()
    cmd.worldid = int(wid)  # wid from above, TODO
    cmd.isAmazon = True
    warehouse = cmd.initwh.add()
    with warehouse_lock:
        warehouse.id = warehouse_id
        warehouse_id += 1
    warehouse.x = 8
    warehouse.y = 8
    socket_world = tools.connectWorld(cmd)
    print('receive world socket, connect to world ^_^')

    #handle the communication with world, UPS
    threadworld = threading.Thread(target=handleWorld, args=(socket_world, conn))
    threadUPS = threading.Thread(target=handleUPS, args=(socket_UPS, conn))
    #start threads
    threadworld.start()
    threadUPS.start()