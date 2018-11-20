import requests
import socket
import struct
import json
import threading
import time
import mcrcon

import logging

#tellraw @a {"text":"mdzzzz"}

# 第一步，创建一个logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # Log等级总开关
# 第二步，创建一个handler，用于写入日志文件
logfile = 'test.log'
fh = logging.FileHandler(logfile, mode='a')
fh.setLevel(logging.INFO)  # 输出到file的log等级的开关
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)  # 输出到console的log等级的开关
# 第三步，定义handler的输出格式
formatter = logging.Formatter("[%(asctime)s %(levelname)s]  %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# 第四步，将logger添加到handler里面
logger.addHandler(fh)
logger.addHandler(ch)


dmkwait = 0.5
oldbuf = b''
nowbuf = b''

socketcounter = 0

def getroomid(roomid):
  response = requests.get('http://api.live.bilibili.com/room/v1/Room/room_init/?id='+str(roomid))
  roomjson = json.loads(response.text)
  realroomid = roomjson.get('data').get('room_id')
  return realroomid

def sendmsg(msg):
  rcon.command('tellraw @a {"text":"'+msg+'"}')       #如果服务器支持tellraw...效果最好
 #rcon.command('me '+msg)          #Nukkit等服务器，退而求其次
 # rcon.command('say '+msg)           #远古版本，只能say了。。。

def readsocket(data):
  body=data[16:]
  fmt="!ihhii"+str(len(body))+"s"
  x,x,x,action,x,bodydata = struct.unpack(fmt, data);
  if action==3:
    logger.info("人气值")
  elif action==5:
    dmkjson = json.loads(bodydata)
    cmd = dmkjson.get('cmd')
    if cmd == "DANMU_MSG":
      detail=dmkjson.get("info")
      dmk=detail[1]
      user=detail[2][1]
      msg="§f[§2§lbilibili§f]§6§l"+user+":§f§l"+dmk
      sendmsg(msg)
      logger.info(msg)
    if cmd == "SEND_GIFT":
      detail=dmkjson.get("data")
      giftname=detail.get("giftName")
      user=detail.get("uname")
      num=str(detail.get("num"))
      msg="§f[§2§lbilibili§f]§f§l感谢§6§l"+user+"§f§l赠送§4§l"+giftname+"§f§lx"+num
      sendmsg(msg)
      logger.info(msg)
  else:
    logger.warn("未知数据")

def socketfinder(buf):
  global oldbuf
  global nowbuf
  global dmkwait
  global socketcounter
  nowbuf = buf
  oldbuf += nowbuf
  pos = oldbuf.find(b"\x00\x10\x00\x00")
  if pos == -1:
    logger.debug("没有找到header")
  else:
    length,=struct.unpack("!i",oldbuf[pos-4:pos])
    havelength=len(oldbuf[pos-4:])
    logger.debug("完整数据包length="+str(length)+"当前数据包havelength="+str(havelength))
    if havelength >= length:
      data=oldbuf[pos-4:pos-4+length]
      socketcounter += 1
      logger.debug("取得数据:"+str(data))
      logger.info("取得第"+str(socketcounter)+"条数据")
      readsocket(data)
      
      
      
      
      #time.sleep(dmkwait)
      
      
      
      
      oldbuf=nowbuf
    else:
      logger.debug("找到header但数据包不完整")


def senddatapack(action,body):
  bodybytes=bytes(body,encoding='utf-8')
  length = len(bodybytes)+16
  fmt="!ihhii"+str(len(bodybytes))+"s"
  ss = struct.pack(fmt, length, 16, 1, action,1,bodybytes);
  s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, length)
  s.send(ss)
  buf=s.recv(32)
  while len(buf):
    logger.debug(buf)
    socketfinder(buf)
    #time.sleep(0.05)
    buf = s.recv(32)

def heart():
  logger.info("正在发送心跳包")
  try:
    senddatapack(2, "")
  except Exception as e:
    logger.error(e)
  global timer  #定义变量
  timer = threading.Timer(30,heart)   #60秒调用一次函数
  timer.start()    #启用定时器

def main():
  global rcon
  host=str(input("服务器地址:"))
  port=int(input("Rcon端口:"))
  pw=str(input("Rcon管理密码:"))
  rcon = mcrcon.MCRcon()
  rcon.connect(host, port, pw)
  msg="§4§l弹幕机已连接!"
  sendmsg(msg)
  roomid=getroomid(int(input("输入直播间号:")))
  logger.info("真实房间号:"+str(roomid))
  try:
    global s
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect(('livecmt-1.bilibili.com',788))
    s.setblocking(False)
    timer = threading.Timer(1,heart)  #首次启动
    timer.start()
    clientid="146284628274713"
    strr='{"roomid":'+str(roomid)+',"uid":'+clientid+',"protover": 1,"platform": "web","clientver": "1.4.0"}'
    logger.debug(strr)
    senddatapack(7, strr)

  except Exception as e:
    logger.error(e)


threads = []
mt = threading.Thread(target=main)
threads.append(mt)
mt.setDaemon(True)
mt.start()


while True:
  time.sleep(1000)
  a=input("输入Q退出")
  if a=="Q":
    #timer.stop()
    msg="§4§l弹幕机已退出!"
    sendmsg(msg)
    s.close()
    exit()

