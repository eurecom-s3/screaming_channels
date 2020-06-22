#!/usr/bin/python3

# This script handles the interaction with Google Eddystone beacons
# On ones side, it communicate with the reproduce.py script to synchronize with
# traces collection, on the other side it connects via BLE to the beacon to
# trigger encryptions with known plaintext.

import gatt
from Crypto.Cipher import AES
import zmq
import os
import time

manager = gatt.DeviceManager(adapter_name='hci0')

class AnyDevice(gatt.Device):
    def connect_succeeded(self):
        super().connect_succeeded()
        # print("[%s] Connected" % (self.mac_address))

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        # print("[%s] Disconnected" % (self.mac_address))
        manager.stop()

    def connect_failed(self, error):
        super().connect_failed(error)
        # print("[%s] Connection failed: %s" % (self.mac_address, str(error)))

    def services_resolved(self):
        super().services_resolved()

        # print("[%s] Resolved services" % (self.mac_address))
        # for service in self.services:
            # print("[%s]  Service [%s]" % (self.mac_address, service.uuid))
            # for characteristic in service.characteristics:
                # print("[%s]    Characteristic [%s]" % (self.mac_address, characteristic.uuid))

        self.unlock_service = next(
            s for s in self.services
            if s.uuid == 'a3c87500-8ed3-4bdf-8a39-a01bebede295')

        self.unlock_characteristic = next(
            c for c in self.unlock_service.characteristics
            if c.uuid == 'a3c87507-8ed3-4bdf-8a39-a01bebede295')

        self.lock_state_characteristic = next(
            c for c in self.unlock_service.characteristics
            if c.uuid == 'a3c87506-8ed3-4bdf-8a39-a01bebede295')

        self.remain_connectable_characteristic = next(
            c for c in self.unlock_service.characteristics
            if c.uuid == 'a3c8750c-8ed3-4bdf-8a39-a01bebede295')

        # notify sc-exeriment collect that we are ready
        socket.send(b"ble dongle ready")
        # wait to start
        self.last_cmd = socket.recv()
        print(self.last_cmd)
        
        # Get the challenge
        self.collected_traces = 0
        self.num_traces = 1
        self.challenges = []
        # self.remain_connectable_characteristic.read_value()
        self.unlock_characteristic.read_value()

    # Callbacks
    def characteristic_enable_notification_succeeded(self, characteristic):
        print("Enable notification succeeded")

    def characteristic_enable_notification_failed(self, characteristic, error):
        print("Enable notification failed, error:", error)

    def characteristic_write_value_succeeded(self, characteristic):
        if characteristic == self.unlock_characteristic:
            print("Write to lock succeeded")
            if self.last_cmd == b'quit':
                new_key = b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
                # new_key = self.new_key
                _key = self.new_key
            else:
                new_key = self.new_key
                _key = b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
            cipher = AES.new(_key, AES.MODE_ECB)
            ct = cipher.encrypt(new_key)
            new_value = b'\x00'+ ct
            self.lock_state_characteristic.write_value(new_value)
        elif characteristic == self.lock_state_characteristic:
            if self.last_cmd == b'quit':
                print("Writen new key")
                socket.send(self.new_key)
                # print("bye bye")
                # self.disconnect()
                # manager.stop()
                self.lock_state_characteristic.read_value()
            elif self.last_cmd == b'set new key':
                print("Writen new key")
                socket.send(self.new_key)
                print("aaaaa",socket.recv())
                socket.send(b'ble dongle ready with new key')
                self.last_cmd = socket.recv()
                print(self.last_cmd)
                # self.remain_connectable_characteristic.read_value()
                self.unlock_characteristic.read_value()
        # self.lock_state_characteristic.read_value()
        # self.disconnect()
        

    def characteristic_write_value_failed(self, characteristic, error):
        print("Write failed, error:", error)

    def characteristic_value_updated(self, characteristic, value):
        
        if characteristic.uuid == 'a3c87506-8ed3-4bdf-8a39-a01bebede295':
            print("Lock State", value)
            print("bye bye")
            self.disconnect()
            manager.stop()
        elif characteristic == self.remain_connectable_characteristic:
            print("remain connectable")
            # self.remain_connectable_characteristic.read_value()
        else:
            print("Challenge: ", value)

            print("Last cmd:", self.last_cmd)
            if(self.last_cmd == b'set new key' or self.last_cmd == b'quit'):
                self.challenge = value
                if self.last_cmd == b'quit':
                    print("restore key")
                    _key = self.new_key
                else:
                    print("new key")
                    self.new_key = os.urandom(16)
                    # self.new_key = b'\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa\xaa'
                    # self.new_key = b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
                    _key = b'\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'
                    #_key = b'\xec\x74\xe6\x70\xf1\x16\x5d\x7b\xd6\x78\xe2\x50\x75\x43\x89\xd9'
                cipher = AES.new(_key, AES.MODE_ECB)
                ct = cipher.encrypt(self.challenge)
                print("Response", ct)
                self.unlock_characteristic.write_value(ct)
                return

            self.collected_traces += 1
            if self.collected_traces < self.num_traces:
                self.unlock_characteristic.read_value()
                return

            socket.send(value)
            
            cmd = socket.recv()
            print(cmd)
            if cmd == b'quit':
                print("trying to quit")
                self.last_cmd = b'quit'
                #self.lock_state_characteristic.read_value()
                self.unlock_characteristic.read_value()
            else:
                print("Hello")
                self.unlock_characteristic.read_value()

# ZMQ socket to interact with reproduce.py
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://127.0.0.1:7777")

# TODO: make the mac address configurable
device = AnyDevice(mac_address='d4:37:ce:01:da:52', manager=manager)
# device = AnyDevice(mac_address='DB:32:09:DE:F9:26', manager=manager)
# device = AnyDevice(mac_address='DF:14:A5:02:10:0A', manager=manager)
# device = AnyDevice(mac_address='E5:8F:A5:90:43:80', manager=manager)
# device = AnyDevice(mac_address='CC:35:30:09:B6:67', manager=manager)
device.connect()

manager.run()

