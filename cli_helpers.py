# -*- coding: utf-8 -*-

from __future__ import print_function
from builtins import object

#---
#--- Python
import optparse # von Python 2.3 bis Python 2.6 (usage 'argparse' from Python 2.7 on)
import os

#---
#--- Plugin Stuff
import nagios_stuff
import munin_helpers

#---
class BaseCLI(object) :

    _SINGLETON_INSTANCE = None #: Singleton Pattern

    def __init__(self, **keywords) :
        """
        @keyword usernameVar, passwordVar: Name of the
            environment variables holding the user credentials and the
            hostname of the service under test.
        @type    usernameVar, passwordVar: str

        @keyword hostname: default value for server hostname
        @type    hostname: str
        """

        # Names of some environment variables
        self._ENV_NAME_USER = keywords.get('usernameVar', None)
        self._ENV_NAME_PASS = keywords.get('passwordVar', None)

        self._options = None
        self._args = None
        self.user = None
        self.host = None
        self.password = None
        self.use_ssl = None

        # take default values from environment variables
        self.defaultUsername = os.environ.get(self._ENV_NAME_USER, None)
        self.defaultPassword = os.environ.get(self._ENV_NAME_PASS, None)
        self.defaultHostname = keywords.get('hostname', None)

        self.parser = self.createParser()

    def IsConfigMode(self) :
        return 'config' in self._args

    def IsVerbose(self) :
        return self._options.verbose_output

    def GetUser(self) :
        return self.user

    def GetHostname(self) :
        return self.host

    def GetPassword(self) :
        return self.password

    def ShouldUseSSL(self) :
        return self.use_ssl

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

    @classmethod
    def GetInstance(cls, **keywords) :
        """
        @keyword usernameVar, passwordVar: Name of the
            environment variables holding the user credentials and the
            hostname of the service under test.
        @type    usernameVar, passwordVar: str

        @keyword hostname: default value for server hostname
        @type    hostname: str
        """
        if cls._SINGLETON_INSTANCE is None :
            cls._SINGLETON_INSTANCE = cls(**keywords)
        return cls._SINGLETON_INSTANCE

    def printUsage(self):
        self.parser.print_help()

    def getLoginString(self) :
        cli = self
        user = cli.GetUser()
        host = cli.GetHostname()
        password = cli.GetPassword()
        use_ssl = cli.ShouldUseSSL()
        return "'%(user)s' with '%(password)s' --> '%(host)s'" % locals()

    def createParser(self) :
        usage = "usage: %prog [options] [config]"
        parser = optparse.OptionParser(usage = usage)
        parser.add_option("-u", "--user",
                          dest = "user",
                          help = "Login as USER. If not specified content of environment variable '%s' will be used." % (self._ENV_NAME_USER,),
                          action = "store",
                          type = "string",
                          metavar = "USER",
                          default = self.defaultUsername,
        )

        parser.add_option("-p", "--passwd",
                          dest = "password",
                          help = "Login with PASSWORD. If not specified content of environment variable '%s' will be used." % (self._ENV_NAME_PASS,),
                          action = "store",
                          type = "string",
                          metavar = "PASSWORD",
                          default = self.defaultPassword,
        )

        parser.add_option("-H", "--host",
                          dest = "host",
                          help = "Login on HOST.",
                          action = "store",
                          type = "string",
                          metavar = "HOST",
                          default = self.defaultHostname,
        )

        parser.add_option("-s", "--secure",
                          dest = "use_ssl",
                          help = "secure connection with SSL/TLS",
                          action = "store_true",
                          default = True,
        )

        parser.add_option("-v", "--verbose",
                          dest = "verbose_output",
                          help = "When active addtional information for human that are not consumable by Munin will be printed",
                          action = "store_true",
        )

        return parser

    def evaluate(self) :
        (options, args) = self.parser.parse_args()

        self.user = options.user
        self.password = options.password
        self.host = options.host
        self.use_ssl = options.use_ssl

        self._args = args
        self._options = options

        if 0 :
            print("'%s' with '%s' -> '%s'" % (self.user, self.password, self.host))


def HandleInvalidArguments(cli, E) :
    """
    @param cli: Command Line Arguments
    @type  cli: L{BaseCLI}

    @param E: the raised Exception
    @type  E: Exception

    @return: final exit code
    @rtype:  int
    """
    if 1 :
        print(E)
    cli.printUsage()
    return cli.MapNagiosReturnCode(nagios_stuff.NAGIOS_RC_UNKNOWN)


def HandleMissingArguments(cli) :
    """
    @return: final exit code
    @rtype:  int
    """
    cli.printUsage()
    return cli.MapNagiosReturnCode(nagios_stuff.NAGIOS_RC_WARNING)


def HandleCannotConnectError(cli, handleMeasureCommand, explanation) :
    """
    @return: final exit code
    @rtype:  int
    """
    handleMeasureCommand(cli, munin_helpers.MUNIN_VALUE_CANNOT_CONNECT)
    if 0 :
        host = cli.GetHostname()
        print(explanation)
    return nagios_stuff.NAGIOS_RC_CRITICAL


def HandleCannotLoginError(cli, handleMeasureCommand, explanation) :
    """
    @return: final exit code
    @rtype:  int
    """
    if 1 :
        print(cli.getLoginString())
    handleMeasureCommand(cli, munin_helpers.MUNIN_VALUE_CANNOT_LOGIN)
    if 0  :
        print(explanation)
    return nagios_stuff.NAGIOS_RC_CRITICAL
