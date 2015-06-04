'''
Created on May 29, 2015

@author: Spencer Lee
'''

from Connection_Flags import *
import Message
import socket
import sys
import select
import os
from __builtin__ import False



clearwin = lambda: os.system('cls')
clearunix = lambda: os.system('clear')

clear = clearwin

def clientInit(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as msg:
        print 'Socket create failed'
        print msg
        sys.exit(0)
        
    try:
        sock.connect((host, port))
    except socket.error as msg:
        print 'Connect failed'
        print msg
        sys.exit(0)
    
    return sock

class Client_State:
    LogIn, Offline, Subs, Post, Hash, Follow, Main = range(7)

class Client(object):
    '''
    classdocs
    '''


    def __init__(self, host = 'localhost', port = 8681):
        '''
        Constructor
        '''
        self.user = ''
        self.unread_messages = 0
        self.sock = clientInit(host, port)
        self.login_status = False
        
        self.delimiter = '};{'
        self.alt_delimeter = '::'
        
        self.read_list = [sys.stdin, self.sock]
        self.write_list = []
        
        self.live_messages = []
        
        self.menu_state = Client_State.Main
        
    def assembleQuit(self):
        quitStr = str(ClientFlags.Quit) + self.delimiter
        return quitStr
        
    def assembleLogInString(self, username, password):
        loginStr =  (str(ClientFlags.LogIn) + self.delimiter +
                     username + self.delimiter + password)
        return loginStr
    
    def assembleReqMsgStr(self, subs):
        reqMsgStr = (str(ClientFlags.GetMsg) + self.delimiter +
                     self.user)
        if subs:
            reqMsgStr += self.delimiter
            for s in subs:
                reqMsgStr += s + self.alt_delimeter
                
        return reqMsgStr
    
    def assembleSubReq(self):
        reqSubStr = (str(ClientFlags.GetSubs) + self.delimiter +
                     self.user)
        return reqSubStr
    
    def assembleFollReq(self):
        reqFolStr = (str(ClientFlags.GetFollowers) + self.delimiter +
                     self.user)
        return reqFolStr  
    
    def assembleAddSub(self, target):
        addSubStr = (str(ClientFlags.AddSub) + self.delimiter +
                     self.user + self.delimiter + target)
        return addSubStr
        
    def assembleDelSub(self, target):
        addSubStr = (str(ClientFlags.DelSub) + self.delimiter +
                     self.user + self.delimiter + target)
        return addSubStr 
    
    def assembleHashSearch(self, tag):
        hashSerStr = (str(ClientFlags.HSearch) + self.delimiter +
                      self.user + self.delimiter + tag)
        return hashSerStr
    
    def assembleLogOut(self):
        logOutStr = (str(ClientFlags.Logout) + self.delimiter +
                     self.user)
        return logOutStr
    
    def clientAssembleMsg(self, dataStr):
        breakDown = dataStr.split(self.delimiter)
        hashtags = breakDown[3].split(self.alt_delimeter)
        print breakDown[1] + ':'
        print breakDown[2]
        hashStr = ''
        for h in hashtags:
            hashStr += h + ' '
        print hashStr
        print'--------------------------------------------------------------------------------'
        
    
    def clientLogIn(self):
        
        while self.login_status == False:
            username = raw_input('Enter Username: ')
            if username == 'QUIT':
                dataStr = self.assembleQuit()
                print dataStr
                
                #self.sock.close()
                sys.exit()
                
            password = raw_input('Enter Password')
            
            loginStr = self.assembleLogInString(username, password)
            
            self.sock.send(loginStr)
            
            serverValid = False
            while serverValid == False:
                sockData = self.sock.recv(1024)
                breakDown = sockData.split(self.delimiter)
                if breakDown[0] == ServerFlags.LogResp:
                    serverValid = True
            
            if int(breakDown[2]) >= 0:
                self.login_status = True
                self.user = username
                self.unread_messages = int(breakDown[2])
                
                self.menu_state = Client_State.Main
                return
            
    def clientLogOut(self):
        dataStr = self.assembleLogOut()
        
        self.sock.send(dataStr)
        
        self.user = ''
        self.unread_messages = 0
        self.login_status = False
        del self.live_messages[:]
        
        self.menu_state = Client_State.LogIn
        return
        
    def clientRecvMsg(self, msgType):
        moreMessages = True
        while moreMessages == True:
            dataStr = self.sock.recv(1024)
            breakDown = dataStr.split(self.delimiter)
            if breakDown[0] == ServerFlags.EndTrans:
                moreMessages = False
                continue
            if breakDown[0] != msgType:
                if breakDown[0] == ServerFlags.NewMsg:
                    newMsg = Message.Message.fromString(dataStr,'};{','::')
                    self.live_messages.append(newMsg)
                else:
                    continue
            newMsg = Message.Message.fromString(dataStr,'};{','::')
            self.clientPrintMsg(newMsg)
            
    def clientRecvSubs(self):
        moreSubs = True
        subList = []
        while moreSubs == True:
            dataStr = self.sock.recv(1024)
            breakDown = dataStr.split(self.delimiter)
            if breakDown[0]== ServerFlags.EndTrans:
                moreSubs = False
            if breakDown[0] != ServerFlags.Sub and breakDown[0] != ServerFlags.Follow:
                if breakDown[0] == ServerFlags.NewMsg:
                    newMsg = Message.Message.fromString(dataStr,'};{','::')
                    self.live_messages.append(newMsg)
                else:
                    continue
            sub = breakDown[2]
            if sub:
                subList.append(sub)
                
        return subList
    
    def clientRecvSubResp(self):
        recing = True
        while recing == True:
            dataStr = self.sock.recv(1024)
            breakDown = dataStr.split(self.delimiter)
            if breakDown[0] == ServerFlags.SubResp:
                if int(breakDown[2]) == 1:
                    print 'Successfully Subscribed'
                    return
                elif int(breakDown[2] == -1):
                    print 'Error user not found'
                    return   
            elif breakDown[0] == ServerFlags.NewMsg:
                newMsg = Message.Message.fromString(dataStr,'};{','::')
                self.live_messages.append(newMsg)  
            
    def clientCheckInputs(self):
        readable = select.select(self.read_list, [], [], 0)[0]
        for r in readable:
            if r is self.sock:
                pass
            elif r is sys.stdin:
                inpt = r.getline()
                return inpt
            
        return ''
        
        
    def validateMenuSelection(self, lower, upper, alt):
        validInput = False
        inpt = ''
        while validInput == False:
            while inpt == '':
                #inpt = self.clientCheckInputs()
                inpt = raw_input(':')
            inInt = int(inpt)
            if lower <= inInt <= upper or inInt == alt:
                validInput = True
            else:
                print 'Invalid Selection'
        return inpt
    
    def clientMainMenu(self):
        print'--------------------------------------------------------------------------------'
        for m in self.live_messages:
            m.printMsg()
            
        print 'Welcome ' + self.user +'. You have ' + str(self.unread_messages) + ' unread messages'
        print 'Menu Options'
        print '1: See Offline Messages'
        print '2: Edit Subscriptions'
        print '3: Post A Message'
        print '4: Hashtag Search'
        print '5: See Followers'
        print '9: Logout'
        
        inInt = int(self.validateMenuSelection(1, 5, 9))

        if inInt < 9:
            self.menu_state = inInt
        else:
            self.clientLogOut()
        return
    
    def clientOffMsgMenu(self):
        print '1: View all offline messages'
        print '2: Select from subscriptions'
        print '0: Return to Main Menu'
        
        inInt = int(self.validateMenuSelection(0, 2, 0))
        
        clear()
        if inInt == 0:
            self.menu_state = Client_State.Main
            return
        elif inInt == 1:
            sendStr = self.assembleReqMsgStr()
            
            self.sock.send(sendStr)
            self.clientRecvMsg(ServerFlags.OldMsg)
        
        elif inInt == 2:
            sendStr = self.assembleSubReq()
            self.sock.send(sendStr)
            
            subList = self.clientRecvSubs()
            c = 0
            for s in subList:
                print str(c) + ': ' + s
                c += 1
                
            print 'Select messages from which subscriptions to view, separate by spaces:'
            print 'Enter nothing to return to man menu'
            choices = raw_input(':')
            if not choices:
                self.menu_state = Client_State.Main
                return
            cSubs = choices.split(' ')
            lSubs = []
            for i in cSubs:
                lSubs.append(subList[int(i)])
            sendStr = self.assembleReqMsgStr(lSubs)
            
            self.sock.send(sendStr)
            self.clientRecvMsg(ServerFlags.OldMsg)
           
            
        raw_input('Press Enter to return to main menu')    
        self.menu_state = Client_State.Main  
        return
         
    def clientSubsMenu(self):
        print '1: Add a subscription'
        print '2: Drop a subscription'
        print '0: Return to Main Menu'
        
        inInt = int(self.validateMenuSelection(0, 2, 0))
        
        clear()
        if inInt == 0:
            self.menu_state = Client_State.Main
        elif inInt == 1:
            print 'Enter user or hashtag to subscribe to'
            print 'leave blank to return to main menu: '
            target = raw_input(':')
            if not target:
                self.menu_state = Client_State.Main
                return
            sendStr = self.assembleReqMsgStr(target)
            self.sock.send(sendStr)
            self.clientRecvSubResp()
        
        elif inInt == 2:
            sendStr = self.assembleSubReq()
            self.sock.send(sendStr)
            
            subList = self.clientRecvSubs()
            c = 0
            for s in subList:
                print str(c) + ': ' + s
                c += 1
                
            print 'Select a subscription to unsubscribe from'
            print 'Enter nothing to return to man menu: '
            choice = raw_input(':')
            if not choice:
                self.menu_state = Client_State.Main
                return 
            
            sendStr = self.assembleDelSub(subList[int(choice)])
            self.sock.send(sendStr)
            print 'Subscription removed'
           
            
        raw_input('Press Enter to return to main menu')    
        self.menu_state = Client_State.Main  
        return
        
        self.menu_state = Client_State.Main
    def clientPostMenu(self):
        print 'Enter a message followed by Enter, leave blank to return to main menu'
        
        valid = False
        while valid == False:
            msgText = raw_input(':')
            if not msgText:
                self.menu_state = Client_State.Main
                return 
            if len(msgText) > 140:
                print 'Length of message too long, must be under 140 characters'
                print 'Please enter a changed message or leave blank to return to main menu: '   
            else:
                valid = True        
            self.menu_state = Client_State.Main
            
            newMsg = Message.Message(self.user, msgText)
            
            print 'Enter any hashtags separated by spaces: '
            tags = raw_input(':')
            if tags:
                tagSplit = tags.split(' ')
                newMsg.messageAddHashtags(tagSplit)
            
            print 'If this is a private message, please specify recipients separated by spaces'
            print 'Otherwise just press Enter: '
            rcvers = raw_input(':')
            if rcvers:
                rcvsplit = rcvers.split(' ')
                newMsg.messageAddReceivers(rcvsplit)
                
            sendStr = str(ClientFlags.Post) + newMsg.messageStringFormat(self.delimiter, self.alt_delimeter, True)
            
            self.sock.send(sendStr)
            
        raw_input('Message Posted, press Enter to return to main menu')
        self.menu_state = Client_State.Main
        return
    
    def clientHashSearchMenu(self):
        print 'Enter a Hashtag followed by Enter'
        print 'leave blank to return to main menu: '
        tag = raw_input(':')
        if not tag:
            self.menu_state = Client_State.Main
            return         
        
        sendStr = self.assembleHashSearch(tag)
        
        self.sock.send(sendStr)
        
        self.clientRecvMsg(ServerFlags.HashMsg)
        
        raw_input('Press Enter to return to main menu')    
        self.menu_state = Client_State.Main  
        return

    
    def clientFollowMenu(self):
        sendStr = self.assembleFollReq()
        self.sock.send(sendStr)
        
        follList = self.clientRecvSubs()
        c = 0
        for s in follList:
            print str(c) + ': ' + s
            c += 1
        raw_input('Press Enter to return to main menu')
        self.menu_state = Client_State.Main

    
    menus = [clientLogIn, clientOffMsgMenu, 
             clientSubsMenu, clientPostMenu, clientHashSearchMenu,
             clientFollowMenu, clientMainMenu]
    
    def clientMainLoop(self):
        
        while True:
            clear()
            self.menus[self.menu_state](self)
            
def main():
    tClient = Client('localhost',8681)
    tClient.clientMainLoop()


if __name__ == "__main__":
    main()   
        