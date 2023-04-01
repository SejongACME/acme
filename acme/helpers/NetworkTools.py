#
#	NetworkTools.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various helpers for working with strings and texts
#

""" Utility functions for network aspects.
"""

from typing import Optional
import ipaddress, re, socket, contextlib

def isValidateIpAddress(ip:str) -> bool:
	try:
		ipaddress.ip_address(ip)
	except Exception:
		return False
	return True

_allowedPart = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)

def isValidateHostname(hostname:str) -> bool:
	if len(hostname) > 255:
		return False
	if hostname[-1] == '.':
		hostname = hostname[:-1] # strip exactly one dot from the right, if present
	return all(_allowedPart.match(x) for x in hostname.split("."))


def isValidPort(port:str) -> bool:
	try:
		_port = int(port)
	except ValueError:
		return False
	return 0 < _port <= 65535


def isTCPPortAvailable(port:int) -> bool:
	try:
		with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
			s.bind(('', port))
	except OSError:
		return False
	return True

def getIPAddress(hostname:Optional[str] = None) -> str:
	"""	Lookup and return the IP address for a host name.
	
		Args:
			hostname: The host name to look-up. If none is given, the own host name is tried.
		Return:
			IP address, or 127.0.0.1 as a last resort. *None* is returned in case of an error.
	"""
	if not hostname:
		hostname = socket.gethostname()
	
	try:
		ip = socket.gethostbyname(hostname)

		#	Try to resolve a local address. For example, sometimes raspbian
		#	need to add a 'local' ir 'lan' postfix, depending on the local 
		#	device configuration
		if ip.startswith('127.'):	# All local host addresses
			for ext in ['.local', '.lan']:
				try:
					ip = socket.gethostbyname(hostname + ext)
				except:
					pass
		return ip
	except Exception:
		return ''
