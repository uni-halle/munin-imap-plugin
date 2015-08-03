# -*- coding: utf-8 -*-

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
