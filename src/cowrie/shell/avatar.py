# Copyright (c) 2009-2014 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

from __future__ import absolute_import, division

from twisted.conch import avatar
from twisted.conch.interfaces import IConchUser, ISFTPServer, ISession
from twisted.conch.ssh import filetransfer as conchfiletransfer
from twisted.python import components, log

from zope.interface import implementer

from cowrie.core.config import CONFIG
from cowrie.shell import filetransfer
from cowrie.shell import pwd
from cowrie.shell import session as shellsession
from cowrie.ssh import forwarding
from cowrie.ssh import session as sshsession


@implementer(IConchUser)
class CowrieUser(avatar.ConchUser):

    def __init__(self, username, server):
        avatar.ConchUser.__init__(self)
        self.username = username.decode('utf-8')
        self.server = server

        self.channelLookup[b'session'] = sshsession.HoneyPotSSHSession

        try:
            pwentry = pwd.Passwd().getpwnam(self.username)
            self.temporary = False
        except KeyError:
            pwentry = pwd.Passwd().setpwentry(self.username)
            self.temporary = True

        self.uid = pwentry['pw_uid']
        self.gid = pwentry['pw_gid']
        self.home = pwentry['pw_dir']

        # SFTP support enabled only when option is explicitly set
        if CONFIG.getboolean('ssh', 'sftp_enabled', fallback=False):
            self.subsystemLookup[b'sftp'] = conchfiletransfer.FileTransferServer

        # SSH forwarding disabled only when option is explicitly set
        if CONFIG.getboolean('ssh', 'forwarding', fallback=True):
            self.channelLookup[b'direct-tcpip'] = forwarding.cowrieOpenConnectForwardingClient

    def logout(self):
        log.msg("avatar {} logging out".format(self.username))


components.registerAdapter(filetransfer.SFTPServerForCowrieUser, CowrieUser, ISFTPServer)
components.registerAdapter(shellsession.SSHSessionForCowrieUser, CowrieUser, ISession)
