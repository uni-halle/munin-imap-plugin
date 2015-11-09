# -*- coding: utf-8 -*-

#---
#--- Pyhton
import email
import email.header

def listMessages(conn) :
    """
    @rtype: [?]
    """
    responseTuple = conn.list() # (response, ['mesg_num octets', ...], octets)
    # ('+OK', ['1 30738', '2 4872', '3 3143', '4 5255', '5 3911'], 41)
    if 0 :
        print responseTuple
    msgList = responseTuple[1]

    return list(p.split(' ') for p in msgList)

def iterMessages(conn, msgList, **keywords) :
    """
    @param msgList: result from L{listMessages}

    @keyword newestFirst: If True sort from newest to oldest. Default is False
    @type    newestFirst: bool
    """
    numMessages = msgList # len(M.list()[1])

    # order by date
    reverseFlag = keywords.get('newestFirst', False)
    if reverseFlag :
        # newest first
        msgIterator = reversed(msgList)

    else :
        # oldest first
        msgIterator = msgList

    for (sid, msgSize) in msgIterator :
        responseTuple = conn.retr(sid) # (response, ['line', ...], octets).
        # ('+OK', ['Return-Path: prvs=06403...', ..., '...'], 4382])
        success = responseTuple[0]
        rawMail = "\n".join(responseTuple[1])
        octets2 = responseTuple[2]

        emailObj = email.message_from_string(rawMail)
        #
	#    for headerType, headerValueRaw in email_message.items() :
        #        headerValueAndEncoding =  email.header.decode_header(headerValueRaw)
        #yield (sid, rawMail)
        yield (sid, emailObj)
