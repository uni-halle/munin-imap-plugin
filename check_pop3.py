#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# vi:si:et:sw=4:sts=4:ts=4
# -*- coding: UTF-8 -*-
# -*- Mode: Python -*-
#
# Copyright (C) 2012 dcodix
# Copyright (C) 2015 David Lukas Müller (david-lukas.mueller@itz.uni-halle.de)

# This file may be distributed and/or modified under the terms of
# the GNU General Public License version 2 as published by
# the Free Software Foundation.
# This file is distributed without any warranty; without even the implied
# warranty of merchantability or fitness for a particular purpose.
# See "LICENSE.GPL" in the source distribution for more information.

#---
#--- Python

import os
import socket
import sys
import time

#---
#--- Python (Mail)
import poplib

#---
#--- Plugin Stuff
import cli_helpers
import nagios_stuff
import munin_helpers
import pop_helpers
import mail_helpers

#---
#--- Munin Constants (http://munin-monitoring.org/wiki/HowToWritePlugins)

MONITOR_GRAPH_TITLE = "POP3 login time"
MONITOR_GRAPH_LABEL = "pop3_login_time"
MONITOR_MEASURED_VARIABLE = "pop%(ssl)s_login_time_%(user)s_at_%(host)s"

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


def printMailboxContent(conn) :
    msgList = pop_helpers.listMessages(conn)
    numMessages = len(msgList)
    print "There are %i messages." % (numMessages,)
    for (sid, emailObj) in pop_helpers.iterMessages(conn, msgList) :
        #emailObj = email.message_from_string(rawMail)
        for headerType, headerTrunc in mail_helpers.iterEmailHeaders(emailObj, truncateAt = 70) :
            if mail_helpers.IsBaseHeader(headerType) :
                headerDisplay = mail_helpers.RemoveLineBreaks(headerTrunc)
                print "    %-30s %s" % (headerType, headerDisplay,)
        print

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

    import email.header

    if cli.IsVerbose() :
        #try:
        printMailboxContent(conn)
        #except Exception as e:
        #    print "CRITICAL: POP3 Cannot retrieve stat: %s" % e
        #    return nagios_stuff.NAGIOS_RC_CRITICAL
        #finally :
        conn.quit
        #print "OK POP3 Login Successful. N messages: ", numMessages

    return nagios_stuff.NAGIOS_RC_OK


#---
#--- Munin Format
def getMuninVariableName(cli) :
    host = cli.GetHostname().split(".")[0]
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
    @return: final exit code
    @rtype:  int
    """
    graphTitle = MONITOR_GRAPH_TITLE
    graphLabel = MONITOR_GRAPH_LABEL
    variableName = getMuninVariableName(cli)
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

    defaultHostname = os.environ.get('IMAP_HOST', None)

    cli = CLI.GetInstance(hostname = defaultHostname,
                          usernameVar = 'RECEIVING_USERNAME',
                          passwordVar = 'RECEIVING_PASSWORD')

    try:
        cli.evaluate()
    except Exception as E:
        return cli_helpers.HandleInvalidArguments(cli, E)

    if cli.IsConfigMode() :
        return HandleConfigCommand(cli)

    user = cli.GetUser()
    host = cli.GetHostname()
    password = cli.GetPassword()
    use_ssl = cli.ShouldUseSSL()

    if None in [user, password, host] :
        return cli_helpers.HandleMissingArguments(cli)

    timepreconnect = time.time()

    try:
        import socket
        socket.setdefaulttimeout(SOCKET_TIMEOUT_SECONDS)
        if use_ssl:
            M = poplib.POP3_SSL(host=host) # default port is 995
        else:
    	    M = poplib.POP3(host) # default port is 110
    except Exception as e:
        return cli_helpers.HandleCannotConnectError(cli,
                    HandleMeasureCommand,
                    "CRITICAL: POP3 Connection not Successful: %s" % e)

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

    return HandleSuccessfulLogin(cli, M, connectDelay, loginDelay)

if __name__ == "__main__":
    retCode = main()
    sys.exit(retCode)
