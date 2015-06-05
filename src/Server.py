'''
Created on May 22, 2015

@author: Spencer Lee
'''

from Connection_Flags import *
import Message
import User
import socket
import select
import sys
import Queue

def serverInit(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as msg:
        print 'Socket create failed'
        print msg
        sys.exit(0)
            
    try:
        sock.bind((host,port))
    except socket.error as msg:
        print 'Socket bind failed'
        print msg
        sock.close()
        sys.exit(0)
    
    return sock

#Enumerations 

class Server(object):


    def __init__(self, HOST, PORT):
        self.sock = serverInit(HOST, PORT)
        self.sock.listen(15)
        self.User_List = []
        self.messages = []
        
        self.Read_List = [sys.stdin, self.sock]
        self.Write_List = []
        self.message_queues = {}
        self.delimiter = '};{'
        self.altDelimeter = '::'

        self.messages_at_boot = len(self.messages)

    def updateMAB(self):
        self.messages_at_boot = len(self.messages)
        
    def serverFindUser(self, user):
        userMatches = [x for x in self.User_List if x.username == user]
        if not userMatches:
            return None
        else:
            return userMatches[0]
        
    def serverCloseConnection(self, conn):
        '''
        connMatches = [x for x in self.Connections if x[0] == conn]
        for m in connMatches:
            self.Connections.remove(m)
        '''
        if conn in self.Write_List:
            self.Write_List.remove(conn)
            
        if conn in self.Read_List:
            self.Read_List.remove(conn)
            conn.close() 
            
        del self.message_queues[conn]
        
    def serverAddConnection(self, conn, addr):
        connMatches = [x for x in self.Connections if x[0] == conn]
        connTuple = (conn, addr, '')
        if not connMatches:
            self.Connections.append(connTuple)
        else:
            self.serverCloseConnection(conn)
            self.Connections.append(connTuple)
            
        
    def serverCreateResponse(self, conn, flag, user, *args):
        reply = ''
        if flag == ServerFlags.Login:
            reply = (str(ServerFlags.Login) + self.delimiter + 
                     user + self.delimiter + str(args[0]))
            
        elif flag == ServerFlags.SubResp:
            reply = (str(ServerFlags.SubResp) + self.delimiter + 
                     user + self.delimiter + str(args[0]))
            
        elif flag == ServerFlags.Sub or flag == ServerFlags.Follow:
            reply = (str(flag) + self.delimiter +
                     user + self.delimiter + str(args[0]))
        
        elif ServerFlags.OldMsg <= flag <= ServerFlags.NewMsg:
            reply = (str(flag) + self.delimiter + 
                     user + self.delimiter +
                     args[0].messageStringFormat(self.delimiter, self.alt_delimeter, False))
                    
        elif flag == ServerFlags.EndTrans:
            reply (str(flag) + self.delimiter +
                   user)     
            
        else:
            return
        
        self.message_queues[conn].put(reply)
        if conn not in self.Write_List:
            self.Write_List.append(conn)
    
    def serverClientQuit(self, conn, dataString):
        self.serverCloseConnection(conn)
            
    def serverLogIn(self, conn, logInString):
        breakDown = logInString.split(self.delimiter)
        userMatches = [x for x in self.User_List if x.username == breakDown[1]]
        if not userMatches:
            self.serverResponse(conn, ClientFlags.LogIn, breakDown[1], -1)
            return
        for m in userMatches:
            if breakDown[2] == m.password:
                m.connection = conn
                '''
                connMatches = [x for x in self.Connections if x[0] == conn]
                for c in connMatches:
                    connTuple = (conn,c[1],m.username)
                    self.Connections.remove(c)
                    self.Connections.append(connTuple)
                '''
                self.serverResponse(conn, ClientFlags.LogIn, breakDown[1], len(m.offlineMessages))
                return
        self.serverResponse(conn, ClientFlags.LogIn,breakDown[1], -1)
        return
    
    def serverLogOut(self, conn, logOutString):
        breakDown = logOutString.split(self.delimiter)
        '''
        addrMatches = [x for x in self.Connections if x[0] == conn and breakDown[1] == x[2]]
        for m in addrMatches:
                self.serverResponse(conn, ClientFlags.LogOut, 1)
                connTuple = (conn,m[1],'')
                self.Connections.remove(m)
                self.Connections.append(connTuple)
                return 1
        '''
        userMatches = [x for x in self.User_List if x.username == breakDown[1]]
        for m in userMatches:
                m.connection = None

        return
        
    def serverGetMsg(self, conn, dataString):
        breakDown = dataString.split(self.delimiter)
        user = [x for x in self.User_List if x.username == breakDown[1]][0]
        if int(breakDown[0]) == ClientFlags.GetMsg:
            msgList = user.offlineMessages
            if breakDown[2]:
                for s in breakDown[2]:
                    msgMatches = [x for x in msgList if x.poster == s]
                    for m in msgMatches:
                        self.serverCreateResponse(conn, ServerFlags.OldMsg, breakDown[1],m)
            else:
                for m in msgList:
                    self.serverCreateResponse(conn, ServerFlags.OldMsg, breakDown[1],m)
        
        elif int(breakDown[0]) == ClientFlags.HSearch:
            for m in reversed(self.messages):
                if breakDown[2] in m.hashtags:
                    self.serverCreateResponse(conn, ServerFlags.HashMsg, breakDown[1],m)
                    
        self.serverCreateResponse(conn, ServerFlags.EndTrans, breakDown[1])
    
    def serverGetSub(self, conn, dataString):
        breakDown = dataString.split(self.delimiter)
        user = [x for x in self.User_List if x.username == breakDown[1]][0]
        for s in user.subscriptions:
            self.serverCreateResponse(conn, ServerFlags.SubResp, breakDown[1], s)
        for s in user.hashsubs:
            self.serverCreateResponse(conn, ServerFlags.SubResp, breakDown[1], s)
            
        self.serverCreateResponse(conn, ServerFlags.EndTrans, breakDown[1])
         
    def serverAddSub(self,conn, dataString):
        breakDown = dataString.split(self.delimiter)
        if breakDown[2][0] != '#':
            userMatches = [x for x in self.User_List if x.username == breakDown[2]]
            if not userMatches:
                self.serverResponse(conn, ClientFlags.Sub, -1)
            else:
                users = [x for x in self.User_List if x.username == breakDown[1]]
                for u in users:
                    u.userSub(breakDown[2])
                for u in userMatches:
                    u.userFollow(breakDown[1])
                self.serverResponse(conn, ClientFlags.Sub, 1)
        else:
            users = [x for x in self.User_List if x.username == breakDown[1]]
            for u in users:
                u.userSub(breakDown[2])
            self.serverResponse(conn, ClientFlags.Sub, 1)
            
    def serverUnsub(self,conn, dataString):
        breakDown = dataString.split(self.delimiter)
        userMatches = [x for x in self.User_List if x.username == breakDown[1]]
        if not userMatches:
            return
        else:
            if breakDown[2][0] != '#':
                users = [x for x in self.User_List if x.username == breakDown[2]]
                for u in users:
                    if breakDown[1] in u.followers:
                        u.userUnfollow(breakDown[1])
                for u in userMatches:
                    u.userUnsub(breakDown[2])
            else:
                for u in userMatches:
                    u.userUnsub(breakDown[2])
        return
    
    def serverPost(self,conn, dataString):
        breakDown = dataString.split(self.delimiter)
        newMessage = Message.Message(breakDown[1], breakDown[2])
        
        tags = breakDown[3].split('::')
        newMessage.messageAddHashtags(tags)
        
        receivers = breakDown[4].split('::')
        newMessage.messageAddReceivers(receivers)
        
        '''
        usr = self.serverFindUser(breakDown[1])
        if usr is None:
            return
        else:
            usr.userPostMessage(newMessage)
        '''   
        usr = [x for x in self.User_List if x.username == breakDown[1]][0]
        self.messages.append(newMessage)
            
        if not newMessage.receivers:
            for f in usr.followers:
                follow = [x for x in self.User_List if x.username == f][0]
                if follow is None:
                    continue
                else:
                    if follow.connection is None:
                        follow.offlineMessages.append(newMessage)
                    else:
                        '''
                        msgStr = (str(ServerFlags.NewMsg) + follow.username +
                                  newMessage.messageStringFormat(self.delimiter, self.altDelimeter, False))
                        self.message_queues[follow.connection].put(msgStr)                        
                        if follow.connection not in self.Write_List:
                            self.Write_List.append(follow.connection)    
                        '''
                        self.serverCreateResponse(conn, ServerFlags.NewMsg, follow.username, newMessage)

                            
            for h in newMessage.hashtags:
                for u in self.User_List:
                    if h in u.hashsubs and u.username not in usr.followers:
                        if u.connection is None:                   
                            u.offlineMessages.append(newMessage)
                            
                        else:
                            self.serverCreateResponse(conn, ServerFlags.NewMsg, follow.username, newMessage)
                        '''
                        msgStr = (str(ServerFlags.NewMsg) + u.username +
                                  newMessage.messageStringFormat(self.delimiter, self.altDelimeter, False))
                        self.message_queues[u.connection].put(msgStr)
                        
                        if u.connection not in self.Write_List:
                            self.Write_List.append(conn)
                        '''                           
        else:
            for r in newMessage.receivers:
                rcv = [x for x in self.User_List if x.username == r][0]
                if rcv is None:
                    continue
                else:
                    if rcv.connection is None:
                        rcv.offlineMessages.append(newMessage)
                    else:
                        '''
                        msgStr = (str(ServerFlags.NewMsg) + rcv.username +
                                  newMessage.messageStringFormat(self.delimiter, self.altDelimeter, False))
                        self.message_queues[rcv.connection].put(msgStr)
                        if rcv.connection not in self.Write_List:
                            self.Write_List.append(rcv.connection)  
                        '''
                        self.serverCreateResponse(conn, ServerFlags.NewMsg, follow.username, newMessage)
        
    serverResponses = [serverLogIn, serverLogOut, serverGetMsg,
                       serverGetSub, serverGetSub, serverAddSub,
                       serverUnsub, serverPost, serverGetMsg,
                       serverClientQuit]        
     
    def serverProcessData(self, conn, data):
        breakDown = data.split(self.delimiter)
        
        self.serverResponses[int(breakDown[0])](self, conn, data)
    
    
    def serverAdminMessagecount(self):
        return len(self.messages) - self.messages_at_boot

    def serverAdminUsercount(self):
        uCount = 0
        for u in self.User_List:
            if u.connection is None:
                pass
            else:
                uCount += 1

        return uCount

    def serverAdminStoredcount(self):
        mCount = 0
        for u in self.User_List:
            mCount += len(u.offlineMessages)

        return mCount

    def serverAdminNewuser(self):
        uName = raw_input('Enter new User Name')
        pWord = raw_input('Enter password:')
        matches = [x for x in self.User_List if x.username == uName ]
        if matches:
            print 'Error User already exists'
            return
        newUser = User.User(uName,pWord)
        self.User_List.append(newUser)  
        print 'New User ' + uName + ' Created'
        
    def serverAdminQuit(self):
        for r in self.Read_List:
            if r is self.sock or r is sys.stdin:
                continue
            r.close()
        self.sock.close()
        sys.exit() 

    def serverAdminCmd(self, command):
        if command == 'messagecount':
            count = self.serverAdminMessagecount()
            print 'New messages since server activation: ' + str(count)
        elif command == 'usercount':
            count = self.serverAdminusercount()
            print 'Logged on Users: ' + str(count)
        elif command == 'storedcount':
            count = self.serverAdminStoredcount()
            print 'Stored Messages' + str(count)
        elif command == 'newuser':
            self.serverAdminNewuser()
        else:
            print 'Invalid Admin Command'
        
        return
              
       
    def RunServer(self):
        while(1):
            '''
            for u in self.User_List:
                if u.connection is None:
                    continue
                else:
                    for m in u.received_messages:
                        if m.status == Message.MessageStatus.unread:
                            message_pkt = str(ServerFlags.Post) + m.messageStringFormat(self.delimiter,'::')
                            
                            self.message_queues[m.connection].put(message_pkt)
                            if m.connection not in self.Write_List:
                                self.Write_List.append(m.connection)
            '''      
                      
            readable, writeable, errored = select.select(self.Read_List, self.Write_List, [])
            for r in readable:
                if r is self.sock:
                    conn = self.sock.accept()[0]
                    conn.setblocking(0)
                    self.Read_List.append(conn)
                    #self.serverAddConnection(conn, addr)
                    self.message_queues[conn] = Queue.Queue()
                else:
                    data = r.recv(1024)
                    if data:
                        self.serverProcessData(r, data)
                    #Close Connection Cause might need to remove 
                    else:
                        pass
                        #self.serverCloseConnection(r)
                        
            for w in writeable:
                try:
                    next_msg = self.message_queues[w].get_nowait()
                except Queue.Empty:
                    continue
                else:
                    w.send(next_msg)
            
            for e in errored:
                self.serverCloseConnection(e)
                
                
def setupUsers(tServer):
    user1 = User.User('alice', '1234')
    user1.userSub('chris')
    user1.userSub('dennis')
    user1.userSub('#alpha')
    
    user1.userFollow('bob')
    user1.userFollow('chris')
    
    user2 = User.User('bob', 'qwer')
    user2.userSub('alice')
    user2.userSub('#bravo')
    user2.userSub('#charlie')
    
    user2.userFollow('chris')
    
    user3 = User.User('chris', 'asdf')
    user3.userSub('alice')
    user3.userSub('bob')
    user3.userSub('dennis')
    
    user3.userFollow('alice')


    user4 = User.User('dennis', 'zxcv')
    
    user4.userFollow('alice')   
    user4.userFollow('chris')
    
    #user5 = User.User('eli', 'yuiop')  
    
def setupMessages(tServer):
    msg1 = Message.Message('alice', 'This is a test')
    msg1.messageAddHashtags(['#alpha'])
    
    msg2 = Message.Message('alice', 'This a another test')
    msg2.messageAddHashtags(['#alpha'])
    
    msg3 = Message.Message('bob', 'This is a test from bob')
    msg3.messageAddHashtags(['#alpha', '#bravo'])
    
    msg4 = Message.Message('dennis', 'I am just trying stuff')
    msg4.messageAddHashtags(['#charlie'])
    
    msg5 = Message.Message('dennis', 'One of Everything')
    msg5.messageAddHashtags(['#alpha', '#bravo', '#charlie'])
    
    msgStrs = [str(ClientFlags.Post) + msg1.messageStringFormat(tServer.delimiter, tServer.alt_delimeter, True),
               str(ClientFlags.Post) + msg2.messageStringFormat(tServer.delimiter, tServer.alt_delimeter, True),
               str(ClientFlags.Post) + msg3.messageStringFormat(tServer.delimiter, tServer.alt_delimeter, True),
               str(ClientFlags.Post) + msg4.messageStringFormat(tServer.delimiter, tServer.alt_delimeter, True),
               str(ClientFlags.Post) + msg5.messageStringFormat(tServer.delimiter, tServer.alt_delimeter, True)]
    
    for m in msgStrs:
        tServer.serverPost(None,m)
        
    tServer.updateMAB()
               
def setupTestBench(tServer):                     
    setupUsers(tServer)
    setupMessages(tServer)
   
                   
def main():
    tServer = Server('localhost', 8681)
    setupTestBench(tServer)
    tServer.RunServer()
    
    

