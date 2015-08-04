# -*- coding: utf-8 -*-

#---
#--- Python
import optparse # von Python 2.3 bis Python 2.6 (usage 'argparse' from Python 2.7 on)
import os

#---
#--- Plugin
import nagios_stuff

#---
class BaseCLI(object) :

    _SINGLETON_INSTANCE = None #: Singleton Pattern

    def __init__(self, userVar, passwordVar, hostnameVar) :
	"""
	@param userVar, passwordVar, hostnameVar: Name of the
	    environment variables holding the user credentials and the
	    hostname of the service under test.
	@type  userVar, passwordVar, hostnameVar: str
	"""

	# Names of some environment variables
	self._ENV_NAME_USER = userVar
	self._ENV_NAME_PASS = passwordVar
	self._ENV_NAME_HOST = hostnameVar

        self._options = None
        self._args = None
        self.user = None
        self.host = None
        self.password = None
        self.use_ssl = None

        # take default values from environment variables
        self.defaultUsername = os.environ.get(self._ENV_NAME_USER, None)
        self.defaultPassword = os.environ.get(self._ENV_NAME_PASS, None)
        self.defaultHostname = os.environ.get(self._ENV_NAME_HOST, None)

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
                          help = "Login on HOST. If not specified content of environment variable '%s' will be used." % (self._ENV_NAME_HOST,),
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

        if 0 :
            print "'%s' with '%s' -> '%s'" % (self.user, self.password, self.host)


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
