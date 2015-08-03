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
        mbName = mbNameWithQuotes[1:-1]
        yield mbName, markers
        continue

def printCapabilities(conn, capabilities) :
    """
    What capabilities does the IMAP server support?
    On http://www.iana.org/assignments/imap-capabilities/imap-capabilities.xhtml
    the following capabilities are listed::

        ACL                     [RFC4314]
        ANNOTATE-EXPERIMENT-1   [RFC5257]
        AUTH=                   [RFC3501]
        BINARY                  [RFC3516]
        CATENATE                [RFC4469]
        CHILDREN                [RFC3348]
        COMPRESS=DEFLATE        [RFC4978]
        CONDSTORE               [RFC7162]
        CONTEXT=SEARCH          [RFC5267]
        CONTEXT=SORT            [RFC5267]
        CONVERT                 [RFC5259]
        CREATE-SPECIAL-USE      [RFC6154]
        ENABLE                  [RFC5161]
        ESEARCH                 [RFC4731]
        ESORT                   [RFC5267]
        FILTERS                 [RFC5466]
        I18NLEVEL=1             [RFC5255]
        I18NLEVEL=2             [RFC5255]
        ID                      [RFC2971]
        IDLE                    [RFC2177]
        IMAPSIEVE=              [RFC6785]
        LANGUAGE                [RFC5255]
        LIST-EXTENDED           [RFC5258]
        LIST-STATUS             [RFC5819]
        LITERAL+                [RFC2088]
        LOGIN-REFERRALS         [RFC2221]
        LOGINDISABLED           [RFC2595][RFC3501]
        MAILBOX-REFERRALS       [RFC2193]
        METADATA                [RFC5464]
        METADATA-SERVER         [RFC5464]
        MOVE                    [RFC6851]
        MULTIAPPEND             [RFC3502]
        MULTISEARCH             [RFC7377]
        NAMESPACE               [RFC2342]
        NOTIFY                  [RFC5465]
        QRESYNC                 [RFC7162]
        QUOTA                   [RFC2087]
        RIGHTS=                 [RFC4314]
        SASL-IR                 [RFC4959]
        SEARCH=FUZZY            [RFC6203]
        SEARCHRES               [RFC5182]
        SORT                    [RFC5256]
        SORT=DISPLAY            [RFC5957]
        SPECIAL-USE             [RFC6154]
        STARTTLS                [RFC2595][RFC3501]
        THREAD                  [RFC5256]
        UIDPLUS                 [RFC4315]
        UNSELECT                [RFC3691]
        URLFETCH=BINARY         [RFC5524]
        URL-PARTIAL             [RFC5550]
        URLAUTH                 [RFC4467]
        UTF8=ACCEPT             [RFC6855]
        UTF8=ALL     (OBSOLETE) [RFC5738][RFC6855]
        UTF8=APPEND  (OBSOLETE) [RFC5738][RFC6855]
        UTF8=ONLY               [RFC6855]
        UTF8=USER    (OBSOLETE) [RFC5738][RFC6855]
        WITHIN                  [RFC5032]

    Other important RFCs are::

        RFC2060  INTERNET MESSAGE ACCESS PROTOCOL - VERSION 4rev1
            obsoletes RFC1730

        RFC3501  INTERNET MESSAGE ACCESS PROTOCOL - VERSION 4rev1
            obsoletes RFC2060
            updated by RFC4466 Collected Extensions to IMAP4 ABNF
            updated by RFC4469 Internet Message Access Protocol (IMAP) CATENATE Extension
            updated by RFC4551 IMAP Extension for Conditional STORE Operation
                               or Quick Flag Changes Resynchronization
            updated by RFC5032 WITHIN Search Extension to the IMAP Protocol
            updated by RFC5182 IMAP Extension for Referencing the Last SEARCH Result
            updated by RFC5738 IMAP Support for UTF-8
            updated by RFC6186 Use of SRV Records for Locating Email Submission/Access Services
            updated by RFC6858 Simplified POP and IMAP Downgrading for Internationalized Email

        RFC2222 Simple Authentication and Security Layer (SASL)



    @param capabilites: contains the CAPABILITIES of the IMAP server
    @type  capabilites: tuple of str
    """

    #print "  namespace: %r" % M.namespace()

    # Some methods from the Python library 'imaplib' will only work
    # if the server does support the specific capabilities.
    capabilitiesOfInterest = set(capabilities)
    capabilitiesOfInterest.add('ACL') # e.g. Cyrus Server
    capabilitiesOfInterest.add('ANNOTATIONS') # non-standard, but supported by Cyrus Server
    capabilitiesOfInterest.add('CHILDREN') # /Noinferiors
    capabilitiesOfInterest.add('QUOTA')
    capabilitiesOfInterest.add('AUTH=CRAM-MD5')
    capabilitiesOfInterest.add('NAMESPACE')

    # Novel Groupwiese
    # https://www.novell.com/documentation/groupwise_sdk/gwsdk_gwimap/data/al7te9j.html
    capabilitiesOfInterest.add('XGWEXTENSIONS')

    print
    print "  %-20s | supported " % ("Capabilities",)
    print "  %s-+-----------" % ("-"*20,)

    for capName in sorted(capabilitiesOfInterest) :
        supported = capName in capabilities
        print "  %-20s | %s" % (capName, "%s" % ('SUPPORTED' if supported else 'NO'))

#    for xcapName in sorted(capabilitiesOfInterest) :
#        if xcapName.startswith('X') :
#            print
#            print xcapName
#            print conn.xatom(xcapName)


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
        #acl = M.myrights(mailbox) # works only with ACL
        #quotaRoots = M.getquotaroot(mailbox) # works only with QUOTA
        (okCheck, checkResultList) = conn.check()
        checkResult = checkResultList[0]
        print "  %(mailbox)-20s | %(msgCount)5s  | %(markerString)6s | %(attributeString)s " % locals()


def HandleInvalidArguments(cli) :
    """
    @return: final exit code
    @rtype:  int
    """
    cli.printUsage()
    return cli.MapNagiosReturnCode(plugin_helpers.NAGIOS_RC_UNKNOWN)


def HandleMissingArguments(cli) :
    """
    @return: final exit code
    @rtype:  int
    """
    cli.printUsage()
    return cli.MapNagiosReturnCode(plugin_helpers.NAGIOS_RC_WARNING)


def HandleCannotConnectError(cli, e) :
    """
    @return: final exit code
    @rtype:  int
    """
    HandleMeasureCommand(cli, MUNIN_VALUE_CANNOT_CONNECT)
    if 0  :
        host = cli.GetHostname()
        print "CRITICAL: Could not connect to %s: %s" % (host, e)
    return cli.MapNagiosReturnCode(plugin_helpers.NAGIOS_RC_CRITICAL)


def HandleCannotLoginError(cli, e) :
    """
    @return: final exit code
    @rtype:  int
    """
    HandleMeasureCommand(cli, MUNIN_VALUE_CANNOT_LOGIN)
    if 0  :
        print "CRITICAL: IMAP Login not Successful: %s" % e
    return cli.MapNagiosReturnCode(plugin_helpers.NAGIOS_RC_CRITICAL)


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
