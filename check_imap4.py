#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
#
# Copyright (C) 2005 Bertera Pietro <pietro@bertera.it>
# Copyright (C) 2012 Bernhard Schmidt <berni@birkenwald.de>
# Copyright (C) 2015 David Lukas Müller <david-lukas.mueller@itz.uni-halle.de>

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.GPL" in the source distribution for more information.

#---
#--- Python
import optparse # von Python 2.3 bis Python 2.6 (usage 'argparse' from Python 2.7 on)
import os
import socket
import sys
import time

#---
#--- Python (Mail)
import imaplib
import email

#---
#--- Plugin Stuff
import cli_helpers
import nagios_stuff

#---
#--- Munin Constants (http://munin-monitoring.org/wiki/HowToWritePlugins)

MONITOR_GRAPH_TITLE = "IMAP login time"
MONITOR_GRAPH_LABEL = "imap_login_time"
MONITOR_MEASURED_VARIABLE = "imap_login_time"

MUNIN_VALUE_CANNOT_LOGIN = -100.0
MUNIN_VALUE_CANNOT_CONNECT = -200.0
MUNIN_VALUE_MINIMUM = min(MUNIN_VALUE_CANNOT_LOGIN, MUNIN_VALUE_CANNOT_CONNECT)

SOCKET_TIMEOUT_SECONDS = 5

ENV_NAME_IMAP_HOST = "IMAP_HOST"
ENV_NAME_IMAP_PASS = "IMAP_PASSWORD"
ENV_NAME_IMAP_USER = "IMAP_USER"

#---
class CLI(cli_helpers.BaseCLI) :

    _SINGLETON_INSTANCE = None #: Singleton Pattern

    def __init__(self) :
        cli_helpers.BaseCLI.__init__(self,
                                     ENV_NAME_IMAP_USER,
                                     ENV_NAME_IMAP_PASS,
                                     ENV_NAME_IMAP_HOST)

    def MapNagiosReturnCode(self, nagiosReturnCode) :
        """
        @param nagiosReturnCode: Following values are specified
            - 0 = OK
            - 1 = WARNING
            - 2 = CRITICAL
            - 3 = UNKNOWN
        @type  nagiosReturnCode: int
        """
        if True :
            return 0
        return nagiosReturnCode

def iterMailboxNames(conn) :
    """
    @param conn: The IMAP4-Connection
    @type  conn: imaplib.IMAP4 | imaplib.IMAP4_SSL
    """
    (listCode, listResult) = conn.list() # Unterschied zu IMAP4.lsub ?
    for mbString in listResult :
        mbParts = mbString.split('"/"')
        mbNameWithQuotes = mbParts[-1].strip()
        firstPart = mbParts[0].strip()[1:-1]
        markers = list(m.lower().strip() for m in firstPart.split(' '))
        if mbNameWithQuotes.startswith('"') or mbNameWithQuotes.startswith("'") :
            mbName = mbNameWithQuotes[1:-1]
        else :
            mbName = mbNameWithQuotes
        yield mbName, markers



def iterMailboxContent_sequentialID(conn, mbName) :
    """
    @precondition: Mailbox must be SELECTED
    @return: generator[(id, rawMail)]
    """
    # Sequential IDs (SID)
    sidResult, sidData = conn.search(None, "ALL") # returns sequential id
    sid_string = sidData[0]
    sid_list = sid_string.split() # separated by SPACE

    for sid in reversed(sid_list) :
        mailResult, mailData = conn.fetch(sid, "(RFC822)") # feth the body
        sid_raw_email = mailData[0][1]
        yield (sid, raw_email)
        break



def iterMailboxContent_uniqueID(conn, mbName) :
    """
    @precondition: Mailbox must be SELECTED
    @return: generator[(id, rawMail)]
    """
    # Unique IDs (UID)
    uidResult, uidData = conn.uid('search', None, "ALL")
    uid_list = uidData[0].split()
    for uid in reversed(uid_list) :
        mailResult, mailData = conn.uid('fetch', uid, '(RFC822)')
        raw_email = mailData[0][1]
        yield (uid, raw_email)
        break



def printMailboxesWithItemCount(conn) :
    """
    List details for all mailboxes
    """
    print
    print "  %-20s | #count | marked | other attributes" % ("Mailbox",)
    print "  %s-+--------+--------+-%s" % ("-"*20,"-"*20)
    for mailbox, markers in iterMailboxNames(conn) :
        (okSelect, msgCountList) = conn.select(mailbox, readonly = True)
        isMarked = '\marked' in markers
        attributeSet = set(markers)
        attributeSet.discard('\marked')
        attributeSet.discard('\unmarked')
        markerString = "MARKED" if isMarked else "  NO  "
        attributeString = ", ".join(sorted(attributeSet))
        msgCount = msgCountList[0]

        if 0 :
            acl = M.myrights(mailbox) # works only with ACL

        if 0 :
            quotaRoots = M.getquotaroot(mailbox) # works only with QUOTA

        if 0 :
            (okCheck, checkResultList) = conn.check()
            checkResult = checkResultList[0]

        print "  %(mailbox)-20s | %(msgCount)5s  | %(markerString)6s | %(attributeString)s " % locals()

def printMailboxesWithLatestMail(conn) :
    """
    Prints all mailboxes with the lates message on top
    """
    for mailbox, markers in iterMailboxNames(conn) :
        (okSelect, msgCountList) = conn.select(mailbox, readonly = True)
        print "%(mailbox)s" % locals()
        #iterMailboxContent = iterMailboxContent_sequentialID
        iterMailboxContent = iterMailboxContent_uniqueID

        for id, rawMail in iterMailboxContent(conn, mailbox) :
            email_message = email.message_from_string(rawMail)
            print "UID = %(id)s" % locals()
            emailTo =email_message['To']
            emailFrom = email.utils.parseaddr(email_message['From'])
            #print "To = %s" % (emailTo,)
            #print "From = %s" % (emailFrom,)
            for emailHeader in email_message.items() :
                print "    %s" % (emailHeader,)

            if 0 :
                # note that if you want to get text content (body) and the email contains
                # multiple payloads (plaintext/ html), you must parse each message separately.
                # use something like the following: (taken from a stackoverflow post)
                def get_first_text_block(self, email_message_instance):
                    maintype = email_message_instance.get_content_maintype()
                    if maintype == 'multipart':
                        for part in email_message_instance.get_payload():
                            if part.get_content_maintype() == 'text':
                                return part.get_payload()
                    elif maintype == 'text':
                        return email_message_instance.get_payload()

            print
        print

def HandleInvalidArguments(cli) :
    """
    @return: final exit code
    @rtype:  int
    """
    cli.printUsage()
    return cli.MapNagiosReturnCode(nagios_stuff.NAGIOS_RC_UNKNOWN)


def HandleMissingArguments(cli) :
    """
    @return: final exit code
    @rtype:  int
    """
    cli.printUsage()
    return cli.MapNagiosReturnCode(nagios_stuff.NAGIOS_RC_WARNING)


def HandleCannotConnectError(cli, e) :
    """
    @return: final exit code
    @rtype:  int
    """
    HandleMeasureCommand(cli, MUNIN_VALUE_CANNOT_CONNECT)
    if 0  :
        host = cli.GetHostname()
        print "CRITICAL: Could not connect to %s: %s" % (host, e)
    return cli.MapNagiosReturnCode(nagios_stuff.NAGIOS_RC_CRITICAL)


def HandleCannotLoginError(cli, e) :
    """
    @return: final exit code
    @rtype:  int
    """
    HandleMeasureCommand(cli, MUNIN_VALUE_CANNOT_LOGIN)
    if 0  :
        print "CRITICAL: IMAP Login not Successful: %s" % e
    return cli.MapNagiosReturnCode(nagios_stuff.NAGIOS_RC_CRITICAL)


def HandleSuccessfulLogin(cli, conn, connectDelay, loginDelay) :
    """
    @param conn: the IMAP connection

    @param connectDelay, loginDelay: Timing
    @type  connectDelay, loginDelay: float

    @return: final exit code
    @rtype:  int
    """

    HandleMeasureCommand(cli, loginDelay)
    #HandleMeasureCommand(cli, connectDelayd)

    if 0 :
        printMailboxesWithItemCount(conn)

    if 0 :
        printMailboxesWithLatestMail(conn)

    conn.logout()
    return cli.MapNagiosReturnCode(nagios_stuff.NAGIOS_RC_OK)

def HandleMeasureCommand(cli, theValue) :
    """
    @return: final exit code
    @rtype:  int
    """
    variableName = MONITOR_MEASURED_VARIABLE
    print "%(variableName)s.value %(theValue).2f" % locals()


def HandleConfigCommand(cli) :
    """
    @return: final exit code
    @rtype:  int
    """
    graphTitle = MONITOR_GRAPH_TITLE
    graphLabel = MONITOR_GRAPH_LABEL
    variableName = MONITOR_MEASURED_VARIABLE
    lowerLimit = MUNIN_VALUE_MINIMUM

    print "graph_title %(graphTitle)s" % locals()
    print "graph_vlabel %(graphLabel)s" % locals()
    if 1 :
        print "graph_args --base 1000 --lower-limit %(lowerLimit)f" % locals()
        print "graph_scale no"

    if 0 :
        print "%(variableName)s.warning 10" % locals()
        print "%(variableName)s.critical 120" % locals()

    print "%(variableName)s.label %(graphLabel)s" % locals()
    return 0


def main():

    cli = CLI.GetInstance()
    try:
        cli.evaluate()
    except Exception :
        return HandleInvalidArguments(cli)

    if cli.IsConfigMode() :
        return HandleConfigCommand(cli)

    user = cli.GetUser()
    host = cli.GetHostname()
    password = cli.GetPassword()
    use_ssl = cli.ShouldUseSSL()

    if user == None or password == None or host == None:
        return HandleMissingArguments(cli)

    timepreconnect = time.time()

    try:
        import socket
        socket.setdefaulttimeout(SOCKET_TIMEOUT_SECONDS)
        if use_ssl:
            M = imaplib.IMAP4_SSL(host=host)
        else:
            M = imaplib.IMAP4(host)
    except Exception as e:
        return HandleCannotConnectError(cli, e)

    timeprelogin = time.time()

    try:
        M.login(user, password)
    except Exception as e:
        return HandleCannotLoginError(cli, e)

    timepostlogin = time.time()
    connectDelay = (timeprelogin - timepreconnect) * 1000
    loginDelay = (timepostlogin - timeprelogin) * 1000

    return HandleSuccessfulLogin(cli, M, connectDelay, loginDelay)

if __name__ == "__main__":
    retCode = main()
    sys.exit(retCode)
