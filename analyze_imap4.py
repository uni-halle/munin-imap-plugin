#!/usr/bin/python
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
#

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
SOCKET_TIMEOUT_SECONDS = 5

#---
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

    def ShouldPrintCapabilities(self) :
        return True

    def ShouldPrintMailboxes(self) :
        return True

    def IsVerboseForHumans(self) :
        return True

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

def HandleInvalidArguments(cli) :
    """
    @return: final exit code
    @rtype:  int
    """
    cli.usage()
    return 0


def HandleMissingArguments(cli) :
    """
    @return: final exit code
    @rtype:  int
    """
    cli.usage()
    return 0


def HandleCannotConnectError(cli, e) :
    """
    @return: final exit code
    @rtype:  int
    """
    host = cli.GetHostname()
    print "CRITICAL: Could not connect to %s: %s" % (host, e)
    return 0


def HandleCannotLoginError(cli, e) :
    """
    @return: final exit code
    @rtype:  int
    """
    print "CRITICAL: IMAP Login not Successful: %s" % e
    return 0


def HandleSuccessfulLogin(cli, conn, connectDelay, loginDelay) :
    """
    @param conn: the IMAP connection

    @param connectDelay, loginDelay: Timing
    @type  connectDelay, loginDelay: float

    @return: final exit code
    @rtype:  int
    """
    capabilities = conn.capabilities

    print "OK IMAP Login Successful"
    print "  Connect:  %(connectDelay).2fms" % locals()
    print "  Login:    %(loginDelay).2fms" % locals()

    imap_helpers.printCapabilities(conn, capabilities)

    imap_helpers.printMailboxesWithItemCount(conn)

    conn.logout()
    return 0


def main():

    cli = CLI.GetInstance()
    try:
        cli.evaluate()
    except getopt.GetoptError:
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
            M = imaplib.IMAP4_SSL(host = host, port = 993)
        else:
            M = imaplib.IMAP4(host, port = 143)
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
    sys.exit(main())
