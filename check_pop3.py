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
import optparse # von Python 2.3 bis Python 2.6 (usage 'argparse' from Python 2.7 on)
import os
import socket
import sys
import time

#---
#--- Python (Mail)
import poplib

#---
#--- Nagios Constants (https://nagios-plugins.org/doc/guidelines.html)

#: The plugin was able to check the service and it appeared to be
#: functioning properly
NAGIOS_RC_OK = 0

#: The plugin was able to check the service, but it appeared to be above
#: some "warning" threshold or did not appear to be working properly
NAGIOS_RC_WARNING = 1

#: The plugin detected that either the service was not running or it was
#: above some "critical" threshold
NAGIOS_RC_CRITICAL = 2

#: Invalid command line arguments were supplied to the plugin or low-level
#: failures internal to the plugin (such as unable to fork, or open a tcp
#: socket) that prevent it from performing the specified operation.
#: Higher-level errors (such as name resolution errors, socket timeouts, etc)
#: are outside of the control of plugins and should generally NOT be reported
#: as UNKNOWN states.
NAGIOS_RC_UNKNOWN = 3

#---
#--- Munin Constants (http://munin-monitoring.org/wiki/HowToWritePlugins)

MONITOR_GRAPH_TITLE = "POP3 login time"
MONITOR_GRAPH_LABEL = "pop3_login_time"
MONITOR_MEASURED_VARIABLE = "pop3_login_time"

MUNIN_VALUE_CANNOT_LOGIN = -100.0
MUNIN_VALUE_CANNOT_CONNECT = -200.0
MUNIN_VALUE_MINIMUM = min(MUNIN_VALUE_CANNOT_LOGIN, MUNIN_VALUE_CANNOT_CONNECT)

SOCKET_TIMEOUT_SECONDS = 5

ENV_NAME_POP3_HOST = "POP3_HOST"
ENV_NAME_POP3_PASS = "POP3_PASSWORD"
ENV_NAME_POP3_USER = "POP3_USER"

#---
class CLI(object) :

    _SINGLETON_INSTANCE = None #: Singleton Pattern

    def __init__(self) :
        self._options = None
        self._args = None
        self.user = None
        self.host = None
        self.password = None
        self.use_ssl = None
        self._printCapabilities = False
        self._printMailboxes = False
        self._verboseForHumans = False
        self._mapNagiosReturnCodesToZero = True # FLAG_MAP_NAGIOS_RETURN_CODES_TO_ZERO

        # take default values from environment variables
        self.defaultUsername = os.environ.get(ENV_NAME_POP3_USER, None)
        self.defaultPassword = os.environ.get(ENV_NAME_POP3_PASS, None)
        self.defaultHostname = os.environ.get(ENV_NAME_POP3_HOST, None)

        self.parser = self.createParser()

    def IsConfigMode(self) :
        return 'config' in self._args

    def GetUser(self) :
        return self.user

    def GetHostname(self) :
        return self.host

    def GetPassword(self) :
        return self.password

    def ShouldUseSSL(self) :
        return self.use_ssl

    def ShouldPrintCapabilities(self) :
        return self._printCapabilities

    def ShouldPrintMailboxes(self) :
        return self._printMailboxes

    def IsVerboseForHumans(self) :
        return self._verboseForHumans

    def MapNagiosReturnCode(self, nagiosReturnCode) :
        """
        @param nagiosReturnCode: Following values are specified
            - 0 = OK
            - 1 = WARNING
            - 2 = CRITICAL
            - 3 = UNKNOWN
        @type  nagiosReturnCode: int
        """
        if self._mapNagiosReturnCodesToZero :
            return 0
        return nagiosReturnCode

    @classmethod
    def GetInstance(cls) :
        if cls._SINGLETON_INSTANCE is None :
            cls._SINGLETON_INSTANCE = cls()
        return cls._SINGLETON_INSTANCE

    def printUsage(self):
        self.parser.print_help()

    def createParser(self) :
        usage = "usage: %prog [options] [config]"
        parser = optparse.OptionParser(usage = usage)
        parser.add_option("-u", "--user",
                          dest = "user",
                          help = "Login as USER. If not specified content of environment variable '%s' will be used." % (ENV_NAME_POP3_USER,),
                          action = "store",
                          type = "string",
                          metavar = "USER",
                          default = self.defaultUsername,
        )

        parser.add_option("-p", "--passwd",
                          dest = "password",
                          help = "Login with PASSWORD. If not specified content of environment variable '%s' will be used." % (ENV_NAME_POP3_PASS,),
                          action = "store",
                          type = "string",
                          metavar = "PASSWORD",
                          default = self.defaultPassword,
        )

        parser.add_option("-H", "--host",
                          dest = "host",
                          help = "Login on HOST. If not specified content of environment variable '%s' will be used." % (ENV_NAME_POP3_HOST,),
                          action = "store",
                          type = "string",
                          metavar = "HOST",
                          default = self.defaultHostname,
        )

        parser.add_option("-s", "--secure",
                          dest = "use_ssl",
                          help = "secure connection with SSL/TLS",
                          action = "store_true",
                          default = True)
        return parser

    def evaluate(self) :
        (options, args) = self.parser.parse_args()

        self.user = options.user
        self.password = options.password
        self.host = options.host
        self.use_ssl = options.use_ssl

        self._args = args
        self._options = options


def HandleCannotConnectError(cli, e) :
    """
    @return: final exit code
    @rtype:  int
    """
    HandleMeasureCommand(cli, MUNIN_VALUE_CANNOT_CONNECT)
    if 0 :
        host = cli.GetHostname()
        print "CRITICAL: POP3 Connection not Successful: %s" % e
    return NAGIOS_RC_CRITICAL


def HandleCannotLoginError(cli, e) :
    """
    @return: final exit code
    @rtype:  int
    """
    HandleMeasureCommand(cli, MUNIN_VALUE_CANNOT_LOGIN)
    if 0  :
        print "CRITICAL: POP3 Login not Successful: %s" % e
    return NAGIOS_RC_CRITICAL


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
        M = conn
        try:
            numMessages = len(M.list()[1])
        except Exception as e:
            print "CRITICAL: POP3 Cannot retrieve stat: %s" % e
            return NAGIOS_RC_CRITICAL
        finally :
            M.quit

        print "OK POP3 Login Successful. N messages: ", numMessages
    return NAGIOS_RC_OK

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
            M = poplib.POP3_SSL(host=host) # default port is 995
        else:
    	    M = poplib.POP3(host) # default port is 110
    except Exception as e:
        return HandleCannotConnectError(cli, e)

    timeprelogin = time.time()

    try:
        M.user(user)
        M.pass_(password)
    except Exception as e:
        return HandleCannotLoginError(cli, e)

    timepostlogin = time.time()
    connectDelay = (timeprelogin - timepreconnect) * 1000
    loginDelay = (timepostlogin - timeprelogin) * 1000

    return HandleSuccessfulLogin(cli, M, connectDelay, loginDelay)

if __name__ == "__main__":
    retCode = main()
    sys.exit(retCode)
