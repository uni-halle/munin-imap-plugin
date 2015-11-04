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
import munin_helpers
import imap_helpers

#---
#--- Munin Constants (http://munin-monitoring.org/wiki/HowToWritePlugins)

MONITOR_GRAPH_TITLE = "IMAP login time"
MONITOR_GRAPH_LABEL = "imap_login_time"
MONITOR_MEASURED_VARIABLE = "imap%(ssl)s_login_time_%(user)s_at_%(host)s"

#---
SOCKET_TIMEOUT_SECONDS = 5

#---
ENV_NAME_IMAP_HOST = "IMAP_HOST"
ENV_NAME_POP3_HOST = "POP3_HOST"
ENV_NAME_IMAP_PASS = "RECEIVING_PASSWORD"
ENV_NAME_IMAP_USER = "RECEIVING_USERNAME"

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

    if cli.IsVerbose() :
        imap_helpers.printMailboxesWithItemCount(conn)

    if cli.IsVerbose() :
        imap_helpers.printMailboxesWithLatestMail(conn)

    conn.logout()
    return cli.MapNagiosReturnCode(nagios_stuff.NAGIOS_RC_OK)


#---
#--- Munin-Format
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
    lowerLimit = munin_helpers.MUNIN_VALUE_MINIMUM

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
    except Exception as E :
        return cli_helpers.HandleInvalidArguments(cli, E)

    if cli.IsConfigMode() :
        return HandleConfigCommand(cli)

    user = cli.GetUser()
    host = cli.GetHostname()
    password = cli.GetPassword()
    use_ssl = cli.ShouldUseSSL()

    if user == None or password == None or host == None:
        return cli_helpers.HandleMissingArguments(cli)

    timepreconnect = time.time()

    try:
        import socket
        socket.setdefaulttimeout(SOCKET_TIMEOUT_SECONDS)
        if use_ssl:
            M = imaplib.IMAP4_SSL(host = host)
        else:
            M = imaplib.IMAP4(host)
    except Exception as e:
        return cli_helpers.HandleCannotConnectError(cli,
                    HandleMeasureCommand,
                    "CRITICAL: Could not connect to %s: %s" % (host, e))

    timeprelogin = time.time()

    try:
        M.login(user, password)
    except Exception as e:
        return cli_helpers.HandleCannotLoginError(cli,
                    HandleMeasureCommand,
                    "CRITICAL: IMAP Login not Successful: %s" % e)

    timepostlogin = time.time()
    connectDelay = (timeprelogin - timepreconnect) * 1000
    loginDelay = (timepostlogin - timeprelogin) * 1000

    return HandleSuccessfulLogin(cli, M, connectDelay, loginDelay)

if __name__ == "__main__":
    retCode = main()
    sys.exit(retCode)
