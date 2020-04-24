import socket
import time
import threading
import select
import psycopg2
import IG1_pb2
import world_amazon_pb2
import tools
import smtplib
from email.mime.text import MIMEText
from email.header import Header

from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint
order_lock_db = threading.Lock()

# send to UPS work horse
def sendToUPS_th(socket_UPS,conn):
    while True:
        # select an AMsg to send
        time.sleep(1)
        with tools.toUPS_lock:
            if(len(tools.toUPS)>0):
                keys = list(tools.toUPS)
                for key in keys:
                #for key in tools.toUPS.keys():
                    if key in tools.toUPS:
                        tools.send_msg(socket_UPS,tools.toUPS[key])

# send to world work horse
def sendToWorld_th(socket_world,conn):
    while True:
        #time.sleep(1)
        #add one purchasemore command to the toWorld if there are orders that is_enough field is false
        with tools.seq_lock:
            APurchasemore = tools.generate_buy(conn)
            if APurchasemore:
                tools.add_toWorld(APurchasemore)
        # select an AMsg to send
        time.sleep(1)
        with tools.toworld_lock:
            if (len(tools.toWorld) > 0):
                keys = list(tools.toWorld)
                for key in keys:
                #for key in tools.toWorld.keys():
                    if key in tools.toWorld:
                        tools.send_msg(socket_world, tools.toWorld[key])

# recv from UPS work horse
def recvFromUPS_th(socket_UPS,conn):
    cursor = conn.cursor()
    timeout = 1
    sender = 'kflin1996@gmail.com'
    smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpObj.starttls()
    smtpObj.login(sender, r'fdsa961224')
    while True:
        # recv the UMsg
        ups_response = IG1_pb2.UMsg()
        #msg = tools.recv_msg_timeout(socket_UPS, timeout)
        msg = tools.recv_msg(socket_UPS)
        if msg == "":
            continue

        ups_response.ParseFromString(msg)
        print("====Recv from UPS: \n"+str(ups_response))
        # handle ack
        if len(ups_response.acks)>0:
            with tools.toUPS_lock:
                for ack in ups_response.acks:
                    print("Ack from UPS: %s", str(ack))
                    keys = list(tools.toUPS)
                    for key in keys:
                    #for key in tools.toUPS.keys():
                        if ack == key and key in tools.toUPS:
                            tools.toUPS.pop(key)

        # handle UOrderPlaced
        if len(ups_response.uorderplaced)>0:
            for order in ups_response.uorderplaced:
                print("From UPS: recv UOrderPlaced!")
                # ack to UPS
                tools.ack_to_UPS(socket_UPS, order.seq)
                # bundle pkgid and truckid
                sql = '''UPDATE amazon_web_order SET truckid = %s WHERE pkgid = %s AND is_order_placed = TRUE;'''
                cursor.execute(sql,(order.truckid, order.pkgid))
                conn.commit()

        if len(ups_response.utruckarrived) > 0:
            for truck in ups_response.utruckarrived:
                print("From UPS: recv UTruckArrived!")
                # ack to UPS
                tools.ack_to_UPS(socket_UPS, truck.seq)
                # search db for this truckid, update db
                with order_lock_db:
                    sql='''UPDATE amazon_web_order SET is_truck_arrived = TRUE WHERE is_truck_arrived = FALSE AND truckid = %s;'''
                    cursor.execute(sql,(truck.truckid,))
                    conn.commit()
                #if order.status is packed, we can generate a APutOnTruck Acommand
                sql = '''SELECT * FROM amazon_web_order WHERE is_truck_arrived = TRUE AND truckid = %s;'''
                cursor.execute(sql, (truck.truckid,))
                orders = cursor.fetchall() # orders = [][]
                for order in orders:
                    if order[16] == 'packed':
                        sql = '''UPDATE amazon_web_order SET is_loaded = TRUE, status = 'loading' WHERE pkgid = %s;'''
                        cursor.execute(sql, (order[0],))
                        conn.commit()
                        with tools.seq_lock:
                            APutOnTruck = tools.generate_load(order)
                            tools.add_toWorld(APutOnTruck)
                # orders = cursor.fetchall()
                # for order in orders:
                #     if order.status == 'packed':
                #         # update database
                #         # TODO
                #         sql = '''UPDATE amazon_web_order SET is_loaded = TRUE, status = 'loading' WHERE pkgid = %s;'''
                #         cursor.execute(sql, (order.pkgid,))
                #         conn.commit()
                #         with tools.seq_lock:
                #             APutOnTruck = tools.generate_load(order)
                #             tools.add_toWorld(APutOnTruck)

        if len(ups_response.upkgdelivered)> 0:
            for deliver in ups_response.upkgdelivered:
                print("From UPS: recv UPkgDelivered")
                # ack to UPS
                tools.ack_to_UPS(socket_UPS, deliver.seq)
                # search db for this pkgid, update order's status to delivered
                sql = '''UPDATE amazon_web_order SET status = 'delivered' WHERE is_delivered = TRUE AND pkgid = %s;'''
                cursor.execute(sql, (deliver.pkgid,))
                conn.commit()
                #----
                sql_fetch = '''SELECT userid from amazon_web_order WHERE pkgid = %s;'''
                cursor.execute(sql_fetch,(deliver.pkgid,))
                row = cursor.fetchone()
                userid = row[0]
                sql_email = '''SELECT email from auth_user WHERE id = %s;'''
                cursor.execute(sql_email,(userid,))
                row = cursor.fetchone()
                user_email = row[0]
                str_to_send = 'Package id: '+str(deliver.pkgid)+' Your order has been delivered!\n\n By Kefan and Yue'
                message = MIMEText(str_to_send,'plain','utf-8')
                message['From'] = Header("mini_Amazon",'utf-8')
                message['To'] = Header("Amazon user",'utf-8')
                sub = 'Order delivered!'
                message['Subject'] = Header(sub,'utf-8')
                try:
                    smtpObj.sendmail(sender,[user_email],message.as_string())
                    print("Success: send email!")
                except smtplib.SMTPException:
                    print("Error: send email!")


# recv from world work horse
def recvFromWorld_th(socket_world,conn):
    cursor = conn.cursor()
    timeout = 1
    while True:
        world_response = world_amazon_pb2.AResponses()
        #msg = tools.recv_msg_timeout(socket_world,timeout)
        msg = tools.recv_msg(socket_world)
        if msg == "":
            continue
        world_response.ParseFromString(msg)
        print("+++++Recv from World: \n"+str(world_response))
        # handle acks
        with tools.toworld_lock:
            for ack in world_response.acks:
                keys = list(tools.toWorld)
                for key in keys:
                    if ack == key and key in tools.toWorld:
                        tools.toWorld.pop(key)

        # handle AErr
        if len(world_response.error) > 0:
            print("From World: recv error！")
            for each in world_response.error:
                print("Error: " + each.err)
                print("Error originseqnum = " + str(each.originseqnum))
                print("Error seqnum = " + str(each.seqnum))
                tools.ack_to_world(socket_world,each.seqnum)

        # recv APurchaseMore(arrived)
        if len(world_response.arrived) > 0:
            print("From World: recv APurchaseMore！")
            for arrive in world_response.arrived:
                # ack to world
                tools.ack_to_world(socket_world,arrive.seqnum)
                # acquire this item's count now in the warehouse(database)
                sql = '''SELECT count FROM amazon_web_product WHERE item_id = %s;'''
                cursor.execute(sql, (arrive.things[0].id,))
                curr_count = cursor.fetchone()
                # the item's count after the replenish
                remaining_items = arrive.things[0].count + curr_count[0]
                sql = '''SELECT * FROM amazon_web_order WHERE is_enough = TRUE AND is_packed = FALSE AND is_order_placed = FALSE AND item_id = %s;'''
                cursor.execute(sql, (arrive.things[0].id,))
                orders = cursor.fetchall()
                for order in orders:
                    # when remaining size>=0, update the order's is_packed and is_order_placed to true
                    if remaining_items >= order[9]:
                        remaining_items -= order[9]
                        # update database (is_packed,is_order_placed,status), generate APack
                        sql = '''UPDATE amazon_web_order SET is_packed = TRUE, status = 'packing' WHERE pkgid = %s;'''
                        cursor.execute(sql, (order[0],))
                        conn.commit()
                        with tools.seq_lock:
                            APack= tools.generate_pack(order)
                            tools.add_toWorld(APack)
                        # update database, generate ASendTruck
                        sql = '''UPDATE amazon_web_order SET is_order_placed = TRUE WHERE pkgid = %s;'''
                        cursor.execute(sql, (order[0],))
                        conn.commit()
                        with tools.seq_lock:
                            ASendtruck = tools.generate_asendtruck(order)
                            tools.add_toUPS(ASendtruck)
                    else:
                        continue
                #update count in warehouse (it should still be 0)
                sql = '''UPDATE amazon_web_product SET count = %s WHERE item_id = %s;'''
                cursor.execute(sql, (remaining_items,arrive.things[0].id))
                conn.commit()

        #recv Apacked(topack)
        if len(world_response.ready) > 0:
            print("From World: recv APacked！")
            for pack in world_response.ready:
                #ack to world
                tools.ack_to_world(socket_world, pack.seqnum)
                #change status to packed (this is useful to the next step)
                with order_lock_db:
                    sql = '''UPDATE amazon_web_order SET status = 'packed' WHERE pkgid = %s;'''
                    cursor.execute(sql, (pack.shipid,))
                    conn.commit()
                sql = '''SELECT * FROM amazon_web_order WHERE pkgid = %s;'''
                cursor.execute(sql, (pack.shipid,))
                order = cursor.fetchone()
                if order[1]: # truckid
                    if order[13] == True: #is_truck_arrived
                        # update database
                        # TODO
                        sql = '''UPDATE amazon_web_order SET is_loaded = TRUE, status = 'loading' WHERE pkgid = %s;'''
                        cursor.execute(sql, (order[0],))
                        conn.commit()
                        with tools.seq_lock:
                            APutOnTruck = tools.generate_load(order)
                            tools.add_toWorld(APutOnTruck)



        #recv ALoaded(loaded)
        if len(world_response.loaded)>0:
            print("From World: recv ALoaded！")
            for load in world_response.loaded:
                #ack to world
                tools.ack_to_world(socket_world, load.seqnum)
                #change status to loaded
                sql = '''UPDATE amazon_web_order SET status = 'loaded' WHERE is_loaded = TRUE AND pkgid = %s;'''
                cursor.execute(sql, (load.shipid,))
                conn.commit()
                #generate AFinishLoading
                sql = '''SELECT * FROM amazon_web_order WHERE pkgid = %s;'''
                cursor.execute(sql, (load.shipid,))
                order = cursor.fetchone()
                with tools.seq_lock:
                    AFinishLoading = tools.generate_afinishloading(order)
                    tools.add_toUPS(AFinishLoading)
                sql = '''UPDATE amazon_web_order SET status = 'delivering', is_delivered = TRUE WHERE status = 'loaded' AND pkgid = %s;'''
                cursor.execute(sql, (load.shipid,))
                conn.commit()

        #recv APackage(packagestatus)
        if len(world_response.packagestatus)>0:
            print("From World: recv APackage")
            for packagestatus in world_response.packagestatus:
                #ack to world
                tools.ack_to_world(socket_world, packagestatus.seqnum)
                #change status to loaded
                sql = '''UPDATE amazon_web_order SET status = %s WHERE pkgid = %s;'''
                cursor.execute(sql, (packagestatus.status, packagestatus.packageid))
                conn.commit()




if __name__ == '__main__':
    #global warehouse_id
    # Connect to database
    conn = tools.connect_db()
    cursor = conn.cursor()
    sql = '''DELETE from amazon_web_warehouse;'''
    cursor.execute(sql)
    conn.commit()
    sql = '''DELETE from amazon_web_order;'''
    cursor.execute(sql)
    conn.commit()
    sql = '''DELETE from amazon_web_product'''
    cursor.execute(sql)
    conn.commit()


    # Receive world ID and connect to UPS
    # TODO
    socket_UPS, wid = tools.recv_worldid()
    print('receive UPS socket ^_^, worldid = (%d)' %(wid))

    # Connect to the world (Warehouse)
    cmd = world_amazon_pb2.AConnect()
    cmd.worldid = int(wid)  # wid from above, TODO
    cmd.isAmazon = True
    warehouse = cmd.initwh.add()
    warehouse.id = 1
    warehouse.x = 10
    warehouse.y = 10
    socket_world = tools.connectWorld(cmd)
    print('receive world socket, connect to world ^_^')
    #cur = conn.cursor()


    # create warehouse
    sql = '''INSERT INTO amazon_web_warehouse (whid, x, y) VALUES (%s, %s, %s)'''
    cursor.execute(sql,(warehouse.id, warehouse.x, warehouse.y))
    conn.commit()

    #handle the communication with world, UPS
    th_world_send = threading.Thread(target=sendToWorld_th, args=(socket_world, conn))
    th_world_recv = threading.Thread(target=recvFromWorld_th, args=(socket_world, conn))
    th_UPS_recv = threading.Thread(target=recvFromUPS_th,args=(socket_UPS, conn))
    th_UPS_send = threading.Thread(target=sendToUPS_th,args=(socket_UPS, conn))

    #start threads
    th_world_send.start()
    th_world_recv.start()
    th_UPS_send.start()
    th_UPS_recv.start()
