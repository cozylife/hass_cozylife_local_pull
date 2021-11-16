# -*- coding: utf-8 -*-
import time
# import udp_discover
import tcp_client

# print(f'{time.time()}')
# a = udp_discover.get_ip()
# print(a)
# exit()
a = tcp_client.tcp_client('192.168.123.57')

print(a.query())
# print(a.control({'1':0}))

# time.sleep(1)
# print(a.control({'1':1}))
