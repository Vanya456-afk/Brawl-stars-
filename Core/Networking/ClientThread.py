import time
import json
from threading import Thread
from Logic.Player import Player
from Logic.Device import Device
from Utils.Helpers import Helpers
from Protocol.LogicLaserMessageFactory import packets


def _(*args):
    print(*args)


class ClientThread(Thread):
    def __init__(self, client, address, db):
        super().__init__()
        self.client = client
        self.address = address
        self.db = db
        self.config = json.loads(open('config.json', 'r', encoding='utf-8').read())
        self.device = Device(self.client)
        self.player = Player(self.device)

    def recvall(self, length: int):
        data = b''
        while len(data) < length:
            chunk = self.client.recv(length - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def run(self):
        try:
            last_packet = time.time()
            while True:
                header = self.client.recv(7)
                if not header:
                    break

                last_packet = time.time()
                packet_id = int.from_bytes(header[:2], 'big')
                packet_length = int.from_bytes(header[2:5], 'big')
                packet_data = self.recvall(packet_length)

                if packet_id in packets:
                    message = packets[packet_id](self.client, self.player, packet_data)
                    message.decode()
                    message.process(self.db)
                else:
                    _('[CLIENT] Unhandled Packet!', packet_id, packet_length)

                if time.time() - last_packet > 10:
                    break
        except (ConnectionAbortedError, ConnectionResetError, TimeoutError, OSError):
            pass
        finally:
            try:
                self.client.close()
            except OSError:
                pass
            Helpers.connected_clients['ClientsCount'] = max(
                0, Helpers.connected_clients['ClientsCount'] - 1
            )
