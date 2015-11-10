# -*- coding: utf-8 -*-

#---
#--- Pyhton
from __future__ import print_function
import email
import email.header
from builtins import bytes

def listMessages(conn) :
    """
    @rtype: [?]
    """
    responseTuple = conn.list() # (response, ['mesg_num octets', ...], octets)
    # ('+OK', ['1 30738', '2 4872', '3 3143', '4 5255', '5 3911'], 41)
    if 0 :
        print(responseTuple)
    msgList = responseTuple[1]

    return list(p.split(b' ') for p in msgList)

def iterMessages(conn, msgList, **keywords) :
    """
    @param msgList: result from L{listMessages}

    @keyword newestFirst: If True sort from newest to oldest. Default is False
    @type    newestFirst: bool
    """
    numMessages = msgList # len(M.list()[1])

    # order by date
    newestFirst = keywords.get('newestFirst', False)
    if newestFirst  :
        msgIterator = reversed(msgList)
    else :
        msgIterator = msgList

    for (sid, msgSize) in msgIterator :
        #print(repr(sid))
        responseTuple = conn.retr(sid.decode('utf-8')) # (response, ['line', ...], octets).
        # ('+OK', ['Return-Path: prvs=06403...', ..., '...'], 4382])
        success = responseTuple[0]
        messageLines = responseTuple[1]
#        print(repr(message))
 #       continue
        rawMail = u"\n".join(line.decode('utf-8') for line in messageLines)
        octets2 = responseTuple[2]

        emailObj = email.message_from_string(rawMail)

        yield (u"sid.%s" % (sid,), emailObj)
