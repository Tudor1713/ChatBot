"""One writer per data directory; repeated launches activate the existing window."""
import hashlib
from pathlib import Path

from PySide6.QtCore import QObject, QLockFile, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstance(QObject):
    activated = Signal()

    def __init__(self, directory):
        super().__init__()
        directory = Path(directory).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(str(directory).casefold().encode('utf-8')).hexdigest()[:32]
        self.name = 'ChatBot-' + digest
        self.lock = QLockFile(str(directory / '.chatbot.lock'))
        # A long-running application is not a stale lock. Dead owner PIDs still recover.
        self.lock.setStaleLockTime(0)
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self.server.newConnection.connect(self._activate)
        self.owner = False

    def acquire(self):
        if self.owner:
            return True
        if not self.lock.tryLock(0):
            if self.lock.error() != QLockFile.LockError.LockFailedError:
                raise RuntimeError('ChatBot 无法锁定数据目录，请检查目录写入权限。')
            client = QLocalSocket()
            client.connectToServer(self.name)
            if client.waitForConnected(1500):
                client.disconnectFromServer()
            return False
        # Only the lock owner can remove an abandoned local socket.
        QLocalServer.removeServer(self.name)
        if not self.server.listen(self.name):
            self.lock.unlock()
            raise RuntimeError('ChatBot 启动通信失败，请重试。')
        self.owner = True
        return True

    def _activate(self):
        while self.server.hasPendingConnections():
            client = self.server.nextPendingConnection()
            client.close()
            client.deleteLater()
            self.activated.emit()

    def close(self):
        if self.owner:
            self.server.close()
            self.lock.unlock()
            self.owner = False
