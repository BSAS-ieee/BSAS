from web3 import Web3
import json

#import numpy as np
import random
import threading
import socket
import struct

from scipy.interpolate import lagrange
import time 

#time_start = time.time()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# 获取ganache中创建的账户(虚拟的私有链节点)
w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

accounts_all = w3.eth.accounts
accounts = accounts_all[1:len(accounts_all)-5]
processors = accounts_all[len(accounts_all)-5:]
reward_account = accounts_all[0:1]

print(len(accounts_all))
print(len(accounts))
print(len(processors))
print(len(reward_account))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
###########################################################秘密共享#############################################################################

map = [[2260.6,80.148,0.29263,0.0030199],[2260.6,70.183,0.29263,0.0030199],[2532.4,137.79,-0.43167,0.0066776],[2532.4,129.88,-0.43167,0.0066776],[3747.3,195.76,-0.85270,0.010318],[3747.3,186.00,-0.85270,0.010318]]
c_dict = {'R003':0,'R004':1,'R009':2,'R010':3,'R016':4,'R017':5,}
cars_num = 60
speed_list=[50, 60, 70, 80, 90, 100, 110, 120]
cars_list = []                   #车辆list
DIGITAL_NUM = 0                  #保留小数位数
SPEED_RANDOM_NUM = 1000          #速度随机数范围
cars_port_list=[]                #车辆端口list
x_Fx_list_all=[]                 #所有车辆的所有车速的映射对list[  [  [x,Fx],[x,Fx],[x,Fx],...   ],[],[],[],...   ]

TRADING_CONTRACT_ADDR = '0xEd4D9cC874fC76F0845A4B0F5cbafa01a6A2290e'                   #Trading合约地址  
PROCESSING_CONTRACT_ADDR = '0xC31332706199ea4CD451872C24F9c78B594Fdcf7'                #Processing合约地址 

#生成每辆车的端口号
for i in range(cars_num):
    p=20000+i
    cars_port_list.append(p)

def emission_function(num):              #计算成本函数   计算速度对应的能耗
    m=[]
    for x in range(5, 141, 5):
        m.append((map[num][0] + map[num][1] * x + map[num][2] * x ** 2 + map[num][3] * x ** 3) / x)
    return m
'''
for i in range(6):
    mm = emission_function(i)
    print('type',i,mm)
'''

class Car:
    def __init__(self, _no, _speed=70, _type = 0, _port = 20000):
        self.car_no = _no                                                   #车辆序号
        self.car_speed = _speed                                             #车速
        self.type = _type                                                   #车辆类型
        self.car_energy = emission_function(self.type)                      #车辆碳排放量
        self.port = _port                                                   #车辆端口
        self.speed_random=round(random.uniform(1, SPEED_RANDOM_NUM),DIGITAL_NUM)                            #车量对应车速随机数
        self.cars_speed_random = [0] * cars_num                             #所有车量的随机数list
        self.cars_speed_fxs = [0.0] * cars_num                              #所有车辆   利用本车fx计算的值
        self.cars_speed_fxs_o = [0.0] * cars_num                            #来自其他车辆fx计算的值
        self.Fx=0.0                                                         #总能耗函数
        self.a_1 = random.randint(1, 10)                                    #fx的2次项系数
        self.a_2 = random.randint(1, 10)                                    #fx的1次项系数
        #self.a_1 = 1                                    #fx的2次项系数
        #self.a_2 = 1                                    #fx的1次项系数
        self.cars_speed_random[_no] = self.speed_random                     #将自己的速度随机数写入随机数list
        self.cars_speed_fxs[_no] = round(self.fx_generate(self.speed_random),DIGITAL_NUM)      #将自己的fx写入fx_list
        self.cars_speed_fxs_o[_no] = round(self.fx_generate(self.speed_random),DIGITAL_NUM)     #将自己的fx写入fx_list_o

    def fx_generate(self,x):                     #fx计算
        index=self.car_speed/5-1                          #速度对应的能耗索引
        fx = self.a_1*x**2 + self.a_2*x + self.car_energy[int(index)]
        return fx

    #发送速度随机数
    def send_x(self,_rec_port):

        udp_socket_send_x = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket_send_x.bind(('127.0.0.1', self.port))
        # print('发送车辆端口', self.port)
        #b = self.speed_random.to_bytes(length=2,byteorder='big',signed=False)
        b = struct.pack('f', self.speed_random)

        for k in range(800):
            udp_socket_send_x.sendto(b,('127.0.0.1', _rec_port))
        udp_socket_send_x.close()

    #接收速度随机数
    def receive_x(self):

        udp_socket_receive_x = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket_receive_x.bind(('127.0.0.1', self.port))

        # print('接收车辆端口', self.port)

        rec_x_data = udp_socket_receive_x.recvfrom(1024)
        rec_x_data_msg = rec_x_data[0]            #发送方发送的内容

        #rec_x_data_msg = int.from_bytes(rec_x_data_msg, byteorder='big', signed=False)
        lf = [i for i in rec_x_data_msg]
        rec_x_data_msg = struct.unpack('f', struct.pack('4B', *lf))[0]

        rec_x_data_port = rec_x_data[1][1]        #发送方端口
        car_port_index = cars_port_list.index(rec_x_data_port)
        self.cars_speed_random[car_port_index] = round(rec_x_data_msg,DIGITAL_NUM)
        rec_x_data_msg_fx =self.fx_generate(rec_x_data_msg)
        self.cars_speed_fxs[car_port_index] = round(rec_x_data_msg_fx,DIGITAL_NUM)
        udp_socket_receive_x.close()

    #发送fx
    def send_fx(self,_rec_port):

        udp_socket_send_fx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket_send_fx.bind(('127.0.0.1', self.port))
        car_port_index = cars_port_list.index(_rec_port)
        send_fx_num = self.cars_speed_fxs[car_port_index]
        b_fx = struct.pack('f', send_fx_num)
        # print('发送车辆端口', self.port)
        for k in range(800):
            udp_socket_send_fx.sendto(b_fx, ('127.0.0.1', _rec_port))
        udp_socket_send_fx.close()

    #接收fx
    def receive_fx(self):

        udp_socket_receive_fx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket_receive_fx.bind(('127.0.0.1', self.port))
        # print('接收车辆端口', self.port)


        rec_x_data = udp_socket_receive_fx.recvfrom(1024)
        rec_x_data_msg = rec_x_data[0]  # 发送方发送的内容

        lf = [i for i in rec_x_data_msg]
        rec_fx_form_other_cars = struct.unpack('f', struct.pack('4B', *lf))[0]
        rec_fx_form_other_cars = round(rec_fx_form_other_cars, DIGITAL_NUM)              #发送方数据    保留3位小数
        rec_x_data_port = rec_x_data[1][1]  # 发送方端口

        car_port_index = cars_port_list.index(rec_x_data_port)
        self.cars_speed_fxs_o[car_port_index] = rec_fx_form_other_cars

        udp_socket_receive_fx.close()

    #获取x，Fx
    def get_x_Fx(self):
        for fx in self.cars_speed_fxs_o:
            self.Fx+=fx
        return [self.speed_random, round(self.Fx,DIGITAL_NUM)]

#线程事务
event_x = threading.Event()
event_fx = threading.Event()

#发送x
def threading_send_x(_car: Car,_port):
    event_x.wait()
    _car.send_x(_port)
    # print(threading.current_thread().getName())

#接收x
def threading_receive_x(_car: Car):
    _car.receive_x()
    # print(threading.current_thread().getName())

#发送fx
def threading_send_fx(_car: Car,_port):
    event_fx.wait()
    _car.send_fx(_port)
    # print(threading.current_thread().getName())

#接收fx
def threading_receive_fx(_car: Car):
    _car.receive_fx()
    # print(threading.current_thread().getName())

import datetime
start_time=datetime.datetime.now()

is_car_exist=False
for speed in speed_list:

    if not is_car_exist:
        #创建车辆
        print('加载车辆...')
        for c in range(cars_num):
            c_type = random.randint(0,5)
            cars_list.append(Car(c,speed,c_type,cars_port_list[c]))

        print('车辆数：',len(cars_list))
        is_car_exist=True
    else:
        for c in range(cars_num):
            cars_list[c].car_speed = speed
            cars_list[c].speed_random=round(random.uniform(1, SPEED_RANDOM_NUM),DIGITAL_NUM)
            cars_list[c].Fx=0.0
            cars_list[c].cars_speed_fxs[c] = round(cars_list[c].fx_generate(cars_list[c].speed_random),DIGITAL_NUM)
            cars_list[c].cars_speed_fxs_o[c] = round(cars_list[c].fx_generate(cars_list[c].speed_random),DIGITAL_NUM)
            cars_list[c].cars_speed_random[c] = cars_list[c].speed_random

    print('映射对计算中...')

    #各辆车之间传输x----------------------------------------------------------------
    #发送并接收x
    for i in range(cars_num):
        for j in range(cars_num):
            if i!=j:
                port = cars_port_list[j]
                t_r_x = threading.Thread(target=threading_receive_x, args=(cars_list[j],))
                t_s_x = threading.Thread(target=threading_send_x, args=(cars_list[i],port,))
                t_r_x.start()
                # time.sleep(0.0001)
                t_s_x.start()
                event_x.set()
                t_r_x.join()
                t_s_x.join()
                print('==')

    #----------------------------------------------------------------------------

    #各辆车之间传输fx----------------------------------------------------------------
    #发送并接收fx
    for i in range(cars_num):
        for j in range(cars_num):
            if i!=j:
                port = cars_port_list[j]
                t_r_fx = threading.Thread(target=threading_receive_fx, args=(cars_list[j],))
                t_s_fx = threading.Thread(target=threading_send_fx, args=(cars_list[i],port,))
                t_r_fx.start()
                # time.sleep(0.0001)
                t_s_fx.start()
                event_fx.set()
                t_r_fx.join()
                t_s_fx.join()
                print('==')

    #----------------------------------------------------------------------------

    x_Fx_list=[]
    for car in cars_list:
        x_Fx_list.append(car.get_x_Fx())
    print()
    x_Fx_list_all.append(x_Fx_list)

    '''
    for i in range(cars_num):
        print('car_',i,'  type:',cars_list[i].type)
        print('speed_random',cars_list[i].cars_speed_random)
        print('fx',cars_list[i].cars_speed_fxs)
        print('fx_o',cars_list[i].cars_speed_fxs_o)
        print('Fx',cars_list[i].Fx)
    '''

end_time=datetime.datetime.now()

for i, speed in enumerate(speed_list):
    print('速度为{0}km/h的映射对：{1}'.format(speed,x_Fx_list_all[i]))

cars_mappings_list=[]
for i in range(cars_num):
    car_mapping=[]
    for j in range(len(x_Fx_list_all)):
        car_mapping.append(x_Fx_list_all[j][i])
    car_m = [n for a in car_mapping for n in a ]
    car_m_int = [int(x*10**DIGITAL_NUM) for x in car_m]
    cars_mappings_list.append(car_m_int)

print(cars_mappings_list)                                  #每辆车的速度-能耗映射对，【70，80，90...】
print('耗时(时:分:秒)：', end_time-start_time)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#########################################################  调用Trading Contract  ###############################################################
# 调用Receive函数 接受车辆上传的映射对

time_start = time.time()

class First():
    def __init__(self):
        self.web3 = Web3(Web3.WebsocketProvider("ws://127.0.0.1:8545"))
        self.A=[]
        # 检查是否连接成功
        if self.web3.eth.getBlock(0) is None:
            print("Failed to connect!")
        elif self.web3.isConnected(): 
            with open(r'/home/seed/Desktop/Try_Again/build/contracts/Trading_abi.json', 'r') as abi_definition:
                # preabi = abi_definition.read()
                self.abi = json.load(abi_definition)
                #print('===============================',self.abi)
                # myabi = self.abi
                self.TradingAddr = TRADING_CONTRACT_ADDR
                self.Trading = self.web3.eth.contract(address=self.TradingAddr,abi=self.abi)
                print("Successfully connected")
            print(self.Trading.all_functions())
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("Trading Contract 收集车辆映射对:")

    def ReceiveTX(self, account, car_no, mapping):
        self.A = self.Trading.functions.ReceiveCD(account,mapping).transact({
            'from':account,
            'to':self.TradingAddr
        })

        print("车辆",car_no,"加密后的映射值a:",self.A)
        print(self.A) 

e1 = First()
for i in range(len(accounts)):
    e1.ReceiveTX(accounts[i],i+1,cars_mappings_list[i])

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 调用Send函数 发送车辆的映射对给Processors
class Second():
    def __init__(self):
        self.web3 = Web3(Web3.WebsocketProvider("ws://127.0.0.1:8545"))
        self.SA=[]
        # 检查是否连接成功
        if self.web3.eth.getBlock(0) is None:
            print("Failed to connect!")
        elif self.web3.isConnected(): 
            with open(r'/home/seed/Desktop/Try_Again/build/contracts/Trading_abi.json', 'r') as abi_definition:
                # preabi = abi_definition.read()
                self.abi = json.load(abi_definition)
                #print('===============================',self.abi)
                # myabi = self.abi
                self.TradingAddr = TRADING_CONTRACT_ADDR
                self.Trading = self.web3.eth.contract(address=self.TradingAddr,abi=self.abi)
                print("Successfully connected")
            #print(self.Trading.all_functions())
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    def SendTX(self,car_num):
        self.SA = self.Trading.functions.SendTX(car_num).call()
        print("发送车辆数据:",self.SA)
        return self.SA
        #print("Trading Contract 发送 Miners 车辆映射对:")

    def Out_put_car_num(self):
        self.c_num = self.Trading.functions.R_car_num().call()
        print("汽车数量:",self.c_num)
        return self.c_num
e2 = Second()
e2.Out_put_car_num()
mapping_list=[]

for i in range(len(accounts)):
    
    mmmm = e2.SendTX(i+1)
    mmm = [float(x)/(10**DIGITAL_NUM) for x in mmmm]
    mapping_list.append(mmm)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#########################################################  调用Processing Contract  ############################################################

r_processor = random.randint(0,4)               #随机选择leader

from collections import Counter
# 计算拉格朗日插值
wat=[]
for i,sp in enumerate(speed_list): 
    x=[]
    r=[]
    for map_l in mapping_list:
        x.append(map_l[2*i])
        r.append(map_l[2*i+1])
    x_repeat_dict = dict(Counter(x))
    x_r_list = [key for key,value in x_repeat_dict.items() if value > 1]
    if x_r_list:
        for x_i in x_r_list:
            x_i_in=x.index(x_i)
            x.remove(x[x_i_in])
            r.remove(r[x_i_in])
    #print(x,r)
    #print(len(x),len(r))
    print()

    x_3 = []
    r_3 = []
    index_x = random.sample(range(0,len(x)-1),3)
    for o in range(3):
        x_3.append(x[index_x[o]])
        r_3.append(r[index_x[o]])
    print(x_3,r_3)
    la=lagrange(x_3,r_3)

    print("速度为{0}km/h时的能耗：{1}".format(sp,int(la(0))))
    wat.append(int(la(0)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#获得推荐速度
i=wat.index(min(wat))
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print('获得推荐速度:{0}km/h'.format(speed_list[i]))

speed_r = speed_list[i]

print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#调用ReSpeed函数 接收推荐速度
class Third():
    def __init__(self):
        self.map = ''       
        self.web3 = Web3(Web3.WebsocketProvider("ws://127.0.0.1:8545"))
        # 检查是否连接成功
        if self.web3.eth.getBlock(0) is None:
            print("Failed to connect!")
        elif self.web3.isConnected():
            with open(r'/home/seed/Desktop/Try_Again/build/contracts/Processing_abi.json', 'r') as abi_definition:
                self.abi = json.load(abi_definition)
                # print('===============================', self.abi)
                self.ProcessingAddr = PROCESSING_CONTRACT_ADDR
                self.Processing = self.web3.eth.contract(address=self.ProcessingAddr, abi=self.abi)
                print("Successfully connected")

                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    def ReSpeed(self):
        self.map = self.Processing.functions.ReSpeed(speed_r).transact({
            'from':processors[r_processor],
            'to':self.ProcessingAddr
        })
        print("上传 Processing Contract 推荐速度为:{0}km/h".format(self.map))
        return self.map

    def SeSpeed(self):
        p = self.Processing.functions.SeSpeed().call()
        return p

P1 = Third()
P1.ReSpeed()

print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
###########################################################  调用Trading Contract  #############################################################
#调用Resp_s函数 获取从Processing合约中return的推荐速度
class Forth():
    def __init__(self):
        self.map = ''  
        self.web3 = Web3(Web3.WebsocketProvider("ws://127.0.0.1:8545"))
        # 检查是否连接成功
        if self.web3.eth.getBlock(0) is None:
            print("Failed to connect!")
        elif self.web3.isConnected():
            with open(r'/home/seed/Desktop/Try_Again/build/contracts/Trading_abi.json', 'r') as abi_definition:
                self.abi = json.load(abi_definition)
                # print('===============================', self.abi)
                self.TradingAddr = TRADING_CONTRACT_ADDR
                self.Trading = self.web3.eth.contract(address=self.TradingAddr, abi=self.abi)
                print("Successfully connected")

                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    
    def Resp_s(self):
        self.pro_addr=PROCESSING_CONTRACT_ADDR
        self.map = self.Trading.functions.Resp_s(self.pro_addr).call()
        print("Processing Contract 返回 Trading Contract:{0}km/h".format(self.map))
        return self.map

T1 = Forth()
T1.Resp_s()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

time_end = time.time()    #结束计时
time_c= time_end - time_start   #运行所花时间
print('time cost', time_c, 's')



