#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# vi:si:et:sw=4:sts=4:ts=4
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
import datetime
import os
import socket
import sys
import time

#---
#--- Python (Mail)
from email.mime.text import MIMEText
import email.header
import imaplib
import poplib
import smtplib

#---
#--- Plugin Stuff
import cli_helpers
import imap_helpers
import mail_helpers
import munin_helpers
import nagios_stuff
import pop_helpers

#---
#--- Munin Constants (http://munin-monitoring.org/wiki/HowToWritePlugins)

MONITOR_GRAPH_TITLE = "IMAP-POP-OFFSET regarding latest mail"
MONITOR_GRAPH_LABEL = "imap_minus_pop"
MONITOR_MEASURED_VARIABLE = "imap%(ssl)s_minus_pop%(ssl)s_%(user)s_at_%(host)s"

#---
SOCKET_TIMEOUT_SECONDS = 5

#---
class CLI(cli_helpers.BaseCLI) :

    _SINGLETON_INSTANCE = None #: Singleton Pattern

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


def timedelta2seconds(td) :
    SECONDS_PER_DAY = 24 * 3600
    seconds = td.seconds + td.days * SECONDS_PER_DAY
    return seconds


def HandleSuccessfulLogin(cli, connImapTriple, connPopTriple) :
    """
    @param connImapTriple: (conn, connectDelay, loginDelay) the IMAP connection
    @type  connImapTriple: (???, float, float)

    @param connPopTriple:  (conn, connectDelay, loginDelay) the POP3 connection
    @type  connPopTriple: (???, float, float)

    @return: final exit code
    @rtype:  int
    """

    (iConn, iConnectDelay, iLoginDelay) = connImapTriple
    (pConn, pConnectDelay, pLoginDelay) = connPopTriple

    newestFirst = True

    now = datetime.datetime.now()
    latestSmtp = None

    # SMTP
    toAddress = os.environ.get('RECEIVING_ADDRESS', None)
    fromAddress = os.environ.get('SENDING_ADDRESS', None)
    smtpServer = os.environ.get('SMTP_HOST', None)
    smtpPort = os.environ.get('SMTP_PORT', 25)
    smtpUser = os.environ.get('SENDING_USERNAME', None)
    smtpPassword = os.environ.get('SENDING_PASSWORD', None)
    if None in [toAddress, fromAddress,
                smtpServer, smtpPort,
                smtpUser, smtpPassword] :
        # Testmail kann nicht versandt werden
        print >>sys.stderr, "SMTP credentials incomplete."
        sys.exit(1)
        return

    if 0 :
        sendTestMessageWithTimestamp(toAddress, fromAddress,
                                     smtpServer, smtpPort,
                                     smtpUser, smtpPassword, now)
        latestSmtp = now

    # IMAP
    if cli.IsVerbose() :
        imapValue = printImapMailboxContent(iConn)

    # POP
    if cli.IsVerbose() :
        popValue = printPopMailboxContent(pConn)

    mailDict = {}
    for (prot, newestMailObj) in zip(["imap", "pop"], [imapValue, popValue]) :
        dateString = newestMailObj["DATE"]
        dateValue = mail_helpers.parseMailDate(dateString)
        subjectString = newestMailObj["SUBJECT"]
        subjectEncoding = email.header.decode_header(subjectString)
        subject = subjectEncoding[0][0]
        fromField = newestMailObj["FROM"]
        fromAddress = mail_helpers.getFromAddress(fromField)

        try :
            timestamp = decomposeSubjectLine(subject)
        except Exception as E :
            print >>sys.stderr, "Exception while decomposing subject line: %s" % (E,)
            sys.exit(5)
            return

        mailDict[prot] = {
            "date" : dateValue.isoformat(),
            "subject" : subject,
            "from" : fromAddress,
            "timestamp" : timestamp,
        }

        if 0 :
            print prot
            print "  DATE    =", dateValue.isoformat()
            print "  SUBJECT =", subject
            print "  FROM    =", fromAddress

        if 0 :
            print "    multipart", newestMailObj.is_multipart()
            print "    unixfrom", newestMailObj.get_unixfrom()
            print "    charset", newestMailObj.get_charset()
            print "    contentType", newestMailObj.get_charset()
            print "    boundary =", newestMailObj.get_boundary()

        if 0 :
            for receivedValue in mail_helpers.iterReceivedHeadLines(newestMailObj) :
                receivedDict = mail_helpers.parseReceivedValue(receivedValue)
                print "from", receivedDict["from"].split(' ')[0]
                print "  at", receivedDict["at"]
                print

        print

    latestSmtp = now
    latestImap = mailDict["imap"]["timestamp"]
    latestPop = mailDict["pop"]["timestamp"]
    if None in [latestImap, latestPop] :
        impSeconds = 0
        print >>sys.stderr, "Missing either POP or IMAP value."
        sys.exit(4)
        return

    impTimeDelta = latestImap - latestPop
    impSeconds = timedelta2seconds(impTimeDelta)
    print "imapSeconds =", timedelta2seconds(latestImap - now)
    print "popSeconds =", timedelta2seconds(latestPop - now)

    if 0 :
        import pprint
        pprint.pprint(mailDict)

    # see the following website for Multigraph Plugins
    # http://guide.munin-monitoring.org/en/latest/plugin/multigraphing.html

    # theValue = iLoginDelay
    # theValue = iConnectDelayd
    theValue = impSeconds

    HandleMeasureCommand(cli, theValue)

    # logout
    iConn.logout()
    pConn.quit()

    return cli.MapNagiosReturnCode(nagios_stuff.NAGIOS_RC_OK)

#---
#--- Munin-Format
def getMuninVariableName(cli) :
    fullhost = cli.GetHostname()
    host = fullhost.split(".")[0]
    ssl = "s" if cli.ShouldUseSSL() else ""
    user = cli.GetUser()
    variableName = MONITOR_MEASURED_VARIABLE % locals()
    return variableName


#---
#--- Munin-Inhalt
def HandleMeasureCommand(cli, theValue) :
    """
    @return: final exit code
    @rtype:  int
    """
    variableName = getMuninVariableName(cli)
    print "%(variableName)s.value %(theValue).2f" % locals()


def HandleConfigCommand(cli) :
    """
    For development of a Multigraph Plugin see:

        - http://guide.munin-monitoring.org/en/latest/plugin/multigraphing.html#plugin-multigraphing

    @return: final exit code
    @rtype:  int
    """
    graphTitle = MONITOR_GRAPH_TITLE
    graphLabel = MONITOR_GRAPH_LABEL
    variableName = getMuninVariableName(cli)
    lowerLimit = munin_helpers.MUNIN_VALUE_MINIMUM

    if 0 : # single graph plugin
        print "graph_title %(graphTitle)s" % locals()
        print "graph_vlabel %(graphLabel)s" % locals()
        if 1 :
            print "graph_args --base 1000 --lower-limit %(lowerLimit)f" % locals()
            print "graph_scale no"

        if 0 :
            print "%(variableName)s.warning 10" % locals()
            print "%(variableName)s.critical 120" % locals()

        print "%(variableName)s.label %(graphLabel)s" % locals()

    else : # multigraph plugin
        print """multigraph if_bytes
graph_title $host interface traffic
graph_order recv send
graph_args --base 1000
graph_vlabel bits in (-) / out (+) per \${graph_period}
graph_category network
graph_info This graph shows the total traffic for $host

send.info Bits sent/received by $host
recv.label recv
recv.type DERIVE
recv.graph no
recv.cdef recv,8,*
recv.min 0
send.label bps
send.type DERIVE
send.negative recv
send.cdef send,8,*
send.min 0

multigraph if_errors
graph_title $host interface errors
graph_order recv send
graph_args --base 1000
graph_vlabel errors in (-) / out (+) per \${graph_period}
graph_category network
graph_info This graph shows the total errors for $host

send.info Errors in outgoing/incoming traffic on $host
recv.label recv
recv.type DERIVE
recv.graph no
recv.cdef recv,8,*
recv.min 0
send.label bps
send.type DERIVE
send.negative recv
send.cdef send,8,*
send.min 0
"""

    return 0

def GetImapConnection(cli, host, user, password, use_ssl) :
    DO_RAISE = True

    timepreconnect = time.time()

    try:
        import socket
        socket.setdefaulttimeout(SOCKET_TIMEOUT_SECONDS)
        if use_ssl:
            M = imaplib.IMAP4_SSL(host = host)
        else:
            M = imaplib.IMAP4(host)
    except Exception as e:
        if DO_RAISE :
            raise
        rc = cli_helpers.HandleCannotConnectError(cli,
                    HandleMeasureCommand,
                    "CRITICAL: Could not connect to %s: %s" % (host, e))
        return None

    timeprelogin = time.time()

    try:
        M.login(user, password)
    except Exception as e:
        if DO_RAISE :
            raise
        rc = cli_helpers.HandleCannotLoginError(cli,
                    HandleMeasureCommand,
                    "CRITICAL: IMAP Login not Successful: %s" % e)
        return None

    timepostlogin = time.time()
    connectDelay = (timeprelogin - timepreconnect) * 1000
    loginDelay = (timepostlogin - timeprelogin) * 1000

    return (M, connectDelay, loginDelay)


def GetPopConnection(cli, host, user, password, use_ssl) :
    DO_RAISE = True

    timepreconnect = time.time()

    try:
        import socket
        socket.setdefaulttimeout(SOCKET_TIMEOUT_SECONDS)
        if use_ssl:
            M = poplib.POP3_SSL(host = host) # default port is 995
        else:
    	    M = poplib.POP3(host) # default port is 110
    except Exception as e:
        if DO_RAISE :
            raise
        rc = cli_helpers.HandleCannotConnectError(cli,
                    HandleMeasureCommand,
                    "CRITICAL: Could not connect to %s: %s" % (host, e))
        return None

    timeprelogin = time.time()

    try:
        M.user(user)
        # '+OK password required for user "xyz"'
        M.pass_(password)
        # '+OK mailbox "xyz" has 5 messages (47919 octets) H migmx123'
    except Exception as e:
        return cli_helpers.HandleCannotLoginError(cli,
                    HandleMeasureCommand,
                    "CRITICAL: POP3 Login not Successful: %s" % e)

    timepostlogin = time.time()
    connectDelay = (timeprelogin - timepreconnect) * 1000
    loginDelay = (timepostlogin - timeprelogin) * 1000

    return (M, connectDelay, loginDelay)


def printImapMailboxContent(conn) :
    """
    Reads the latest mail via IMAP.
    """

    mailbox = 'INBOX'

    #imap_helpers.printMailboxesWithItemCount(iConn)
    #imap_helpers.printMailboxesWithLatestMail(iConn)
    #imap_helpers.printMailboxContent(iConn, mailbox, **kwargs)

    (okSelect, msgCountList) = conn.select(mailbox, readonly = True)
    mailboxPretty = imap_helpers.decodeMailboxName(mailbox)

    if 0 :
        print "%(mailboxPretty)s" % locals()
    prettyMailbox = imap_helpers.decodeMailboxName(mailbox)

    newestMailObj = None
    for id, emailObj in imap_helpers.iterMailboxContent(conn, mailbox,
                                                        uniqueIdentifier = True,
                                                        newestFirst = True) :
        if 0 :
            print "ID = %(id)s" % locals()
        newestMailObj = emailObj
        break

    if newestMailObj is None :
        print >>sys.stderr, "Could not access IMAP server."
        sys.exit(3)
        return None

    return newestMailObj




def printPopMailboxContent(conn) :
    """
    Reads the latest mail via POP.
    """
    msgList = pop_helpers.listMessages(conn)
    numMessages = len(msgList)
    if 0 :
        print "There are %i messages (via POP)." % (numMessages,)
    newestMailObj = None

    for (sid, emailObj) in pop_helpers.iterMessages(conn, msgList, newestFirst = True) :
        if 0 :
            print "ID = %r" % (sid,)
            for headerType, headerTrunc in mail_helpers.iterEmailHeaders(emailObj, truncateAt = 70) :
                if mail_helpers.IsBaseHeader(headerType) :
                    headerDisplay = mail_helpers.RemoveLineBreaks(headerTrunc)
                    print "    %-30s %s" % (headerType, headerDisplay,)
            print


        newestMailObj = emailObj
        break

    # show informations of the newest mail
    if newestMailObj is None :
        print >>sys.stderr, "Could not access POP server."
        sys.exit(2)
        return None

    # print all parts of a multipart mail
    if 0 :
        for (i, msg) in enumerate(newestMailObj.get_payload()) :
            print "PART", i
            print "  charset =", msg.get_charset()
            print "  contentType =", msg.get_content_type()
            print "  contentMainType =", msg.get_content_maintype()
            print "  contentSubType =", msg.get_content_subtype()
            print "  defaultType =", msg.get_default_type()
            print "  filename =", msg.get_filename()
            print "  boundary =", msg.get_boundary()
            print "  contentCharset =", msg.get_content_charset()
            print "  charsets =", msg.get_charsets()
            print
            print "  <CONTENT>"
            print msg.as_string()
            print "  </CONTENT>"
            print

        pass

    return newestMailObj

SUBJECT_PREFIX = "Testmessage "

def composeSubjectLine(now) :
    """
    @param now: the current timestamp
    @type  now: datetime.datetime
    """
    timestamp = now.isoformat()
    return "%s%s" % (SUBJECT_PREFIX, timestamp)


def decomposeSubjectLine(subjectLine) :
    """
    @param subject: content of the subject field
    @type  subject: str

    @raise ValueError: on bad formatted subject line

    @rtype: datetime.datetime
    """
    timestamp = subjectLine[len(SUBJECT_PREFIX):]
    formatString = "%Y-%m-%dT%H:%M:%S.%f"
    ts = datetime.datetime.strptime(timestamp, formatString)
    return ts


def sendTestMessageWithTimestamp(toAddress, fromAddress,
                                 smtpServer, smtpPort,
                                 smtpUser, smtpPassword,
                                 now) :
    """
    @param toAddress, fromAddress: sender and receiver
    @type  toAddress, fromAddress: str

    @param smtpServer: hostname of the SMTP server
    @type  smtpServer: str

    @param smtpPort: port of the SMTP server
    @type  smtpPort: int

    @param smtpUser, smtpPassword: user credential for authenticated sending
        (transmittet without SSL but with STARTTLS)
    @type  smtpUser, smtpPassword: str

    @param now: the current timestamp
    @type  now: datetime.datetime
    """
    msg = MIMEText("This is an automatic generated test message.\n\nPlease contact david-lukas.mueller@itz.uni-halle.de for details.")
    msg['Subject'] = composeSubjectLine(now)
    msg['From'] = fromAddress
    msg['To'] = toAddress

    s = smtplib.SMTP(smtpServer, smtpPort)
    s.starttls() # (220, 'OK')
    s.login(smtpUser, smtpPassword) # (235, 'Authentication succeeded')
    s.sendmail(fromAddress, [toAddress], msg.as_string())
    s.quit()
    return

def main():

    defaultHostname = os.environ.get('IMAP_HOST', None)

    cli = CLI.GetInstance(hostname = defaultHostname,
                          usernameVar = 'RECEIVING_USERNAME',
                          passwordVar = 'RECEIVING_PASSWORD')

    try:
        cli.evaluate()
    except Exception as E :
        return cli_helpers.HandleInvalidArguments(cli, E)

    if cli.IsConfigMode() :
        return HandleConfigCommand(cli)


    user = cli.GetUser()
    imaphost = os.environ.get('IMAP_HOST', None)
    pop3host = os.environ.get('POP3_HOST', None)
    password = cli.GetPassword()


    if None in [user, password, imaphost, pop3host] :
        return cli_helpers.HandleMissingArguments(cli)

    use_ssl = cli.ShouldUseSSL()

    connImapTriple = GetImapConnection(cli, imaphost, user, password, use_ssl)
    if connImapTriple is None :
        return None

    connPopTriple = GetPopConnection(cli, pop3host, user, password, use_ssl)
    if connPopTriple is None :
        return None

    return HandleSuccessfulLogin(cli, connImapTriple, connPopTriple)

if __name__ == "__main__":
    retCode = main()
    sys.exit(retCode)
