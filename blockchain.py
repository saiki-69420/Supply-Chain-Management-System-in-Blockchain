import hashlib
import json
from time import time, sleep
from uuid import uuid4
import threading
import qrcode
import random

class MerkleTree:
    def __init__(self, transactions):
        self.transactions = transactions
        self.tree = self.build_tree()

    def build_tree(self):
        if len(self.transactions) == 0:
            return None

        if len(self.transactions) % 2 != 0:
            self.transactions.append(self.transactions[-1])

        tree = [self.hash_transaction(tx) for tx in self.transactions]

        while len(tree) > 1:
            tree = [self.hash_transaction(tree[i] + tree[i+1]) for i in range(0, len(tree), 2)]

        return tree[0]

    @staticmethod
    def hash_transaction(transaction):
        return hashlib.sha256(transaction.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.pending_transactions = []
        self.clients = {}
        self.distributors = {}
        self.manufacturer_registered = False
        self.manufacturer_security_deposit = 0
        self.delivery_status = {}
        self.lock = threading.Lock()
        self.mine_flag = True

        #Creation of genesis block
        if len(self.chain) == 0:
            self.new_block(previous_hash='1', miner=None)

    def register_manufacturer(self, manufacturer_id, security_deposit):
        if not self.manufacturer_registered:
            self.manufacturer_registered = True
            self.manufacturer_security_deposit = security_deposit
            print(f"Manufacturer registered with ID: {manufacturer_id}, Security Deposit: {security_deposit}")
        else:
            print("Manufacturer is already registered.")

    def register_distributor(self, distributor_id, security_deposit):
        self.distributors[distributor_id] = {'security_deposit': security_deposit, 'transactions': []}
        print(f"Distributor {distributor_id} registered with security deposit: {security_deposit}")

    def register_client(self, client_id, security_deposit):
        self.clients[client_id] = {'security_deposit': security_deposit, 'transactions': []}
        print(f"Client {client_id} registered with security deposit: {security_deposit}")

    def new_block(self, previous_hash=None, miner=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': None,   # PoET-style mining, no proof needed 
            #(Since we are not using Proof of work we keep the proof section as None. We are using PoET consensus algorithm in this code.)
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'miner': miner  # Store miner's ID
        }

        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, product, price):
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'product': product,
            'price': price,
            'confirmed_by_distributor': False,
            'confirmed_by_consumer': False,
            'dispatched': False,
            'received': False,
        }

        self.pending_transactions.append(transaction)
        return len(self.pending_transactions)  # Return the number of pending transactions

    @staticmethod
    def hash(block):
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def stop_mining(self):
        self.mine_flag = False

    def mine_pending_transactions(self, node_identifier):
        last_block = self.last_block
        miner = node_identifier

        #PoET consesnus algorithm is being implemented here
        sleep_time = random.randint(1, 5)  # Simulate PoET-style random wait time
        sleep(sleep_time)

        previous_hash = self.hash(last_block)
        merkle_tree = MerkleTree([json.dumps(tx) for tx in self.pending_transactions])
        merkle_root = merkle_tree.tree

        block = self.new_block(previous_hash, miner)

        for transaction in self.pending_transactions:
            if (
                transaction['confirmed_by_distributor']
                and transaction['confirmed_by_consumer']
                and transaction['dispatched']
                and transaction['received']
            ):
                self.current_transactions.append(transaction)

        self.pending_transactions.clear()
        self.chain.append(block)

        # Print miner and transaction details
        print(f"Block mined by {miner}: {block}")
        for tx in block['transactions']:
            sender = tx['sender']
            recipient = tx['recipient']
            product = tx['product']
            print(f"Transaction: {sender} -> {recipient} (Product: {product})")

        # Update and print security deposit for each user
        if miner in self.clients:
            self.clients[miner]['security_deposit'] += 10  # Increment client's deposit by 10 after mining
            print(f"Security deposit left with Client {miner}: {self.clients[miner]['security_deposit']}")
        elif miner in self.distributors:
            self.distributors[miner]['security_deposit'] += 10  # Increment distributor's deposit by 10 after mining
            print(f"Security deposit left with Distributor {miner}: {self.distributors[miner]['security_deposit']}")
        elif miner == 'Manufacturer':
            self.manufacturer_security_deposit += 10  # Increment manufacturer's deposit by 10 after mining
            print(f"Security deposit left with Manufacturer: {self.manufacturer_security_deposit}")

        qr_code = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr_code.add_data(json.dumps(block))
        qr_code.make(fit=True)

        qr_code_image = qr_code.make_image(fill_color="black", back_color="white")
        qr_code_image.save(f'block_{block["index"]}.png')

        sleep(5)

    # Simulate distributor confirming product dispatch
    def distributor_confirm_dispatch(self, index):
        for transaction in self.pending_transactions:
            if not transaction['confirmed_by_distributor'] and not transaction['dispatched']:
                # Simulate a failed transaction with a 70% chance
                if random.random() < 0.7:
                    transaction['confirmed_by_distributor'] = True
                    transaction['dispatched'] = True
                    print(f"Successful dispatch confirmed for transaction: {index}")
                else:
                    transaction['confirmed_by_distributor'] = True
                    print(f"Transaction failed due to Distributor falsely confirms dispatch for transaction: {index}")
                    # Handle the failed transaction logic here if needed

    # Simulate consumer confirming product reception
    def consumer_confirm_reception(self, index):
        for transaction in self.pending_transactions:
            if not transaction['confirmed_by_consumer'] and transaction['dispatched'] and not transaction['received']:
                # Simulate a failed transaction with a 70% chance
                if random.random() < 0.7:
                    transaction['confirmed_by_consumer'] = True
                    transaction['received'] = True
                    print(f"Successful reception confirmed for transaction: {index}")
                else:
                    transaction['confirmed_by_consumer'] = True
                    print(f"Transaction failed due to Client denies receiving the product for transaction: {index}")
                    # Handle the failed transaction logic here if needed

    def resolve_delivery_issues(self):
        for transaction in self.current_transactions:
            sender = transaction['sender']
            recipient = transaction['recipient']
            product = transaction['product']
            distributor = sender if sender in self.distributors else recipient
            client = recipient if recipient in self.clients else sender

            # Scenario 1: Distributor dispatched, Client received, but Client is denying it
            if transaction['dispatched'] and transaction['received'] and not transaction['confirmed_by_consumer']:
                print(f"Delivery issue detected: Distributor ({distributor}) dispatched, "
                      f"Client ({client}) received, but Client is denying it for Product ({product}).")

                # Deduct security deposit from the lying party (client)
                self.clients[client]['security_deposit'] -= 50
                print(f"Deducted 50 units from Client {client}'s security deposit.")

            # Scenario 2: Distributor did not dispatch, Client did not receive, but Client is not lying
            elif not transaction['dispatched'] and not transaction['received'] and transaction['confirmed_by_consumer']:
                # Check if the distributor falsely confirmed dispatch
                if not transaction['confirmed_by_distributor']:
                    print(f"Transaction failed due to Distributor falsely confirms dispatch for transaction: {index}")
                    # Handle the failed transaction logic here if needed
                else:
                    print(f"Delivery issue detected: Distributor ({distributor}) did not dispatch, "
                          f"Client ({client}) did not receive, but Client is not lying for Product ({product}).")

                    # Deduct security deposit from the lying party (distributor)
                    self.distributors[distributor]['security_deposit'] -= 50
                    print(f"Deducted 50 units from Distributor {distributor}'s security deposit.")

blockchain = Blockchain()

# Register the Manufacturer
blockchain.register_manufacturer("Manufacturer1", 1000)

# Register Distributors
blockchain.register_distributor("Distributor1", 500)
blockchain.register_distributor("Distributor2", 500)
blockchain.register_distributor("Distributor3", 500)

# Register Clients
blockchain.register_client("Client1", 200)
blockchain.register_client("Client2", 200)
#blockchain.register_client("Client3", 200)

try:
    while True:
        # Simulate transactions between Manufacturer and Distributors
        sender = "Manufacturer1"
        distributor_recipient = random.choice(["Distributor1", "Distributor2", "Distributor3"])
        product = "Product A"
        price = random.randint(50, 200)
        index = blockchain.new_transaction(sender, distributor_recipient, product, price)
        print(f"New transaction created: {sender} -> {distributor_recipient} (Product: {product}), Index: {index}")

        # Check if there are at least 2 transactions to create a block
        if len(blockchain.pending_transactions) >= 2:
            # Simulate PoET-style mining
            node_identifier = str(uuid4()).replace('-', '')
            blockchain.mine_pending_transactions(node_identifier)

        blockchain.distributor_confirm_dispatch(index)
        sleep(2)  # Simulate some time passing

        # Simulate transactions between Distributors and Clients
        distributor_sender = random.choice(["Distributor1", "Distributor2", "Distributor3"])
        client_recipient = random.choice(["Client1", "Client2", "Client3"])
        product = "Product B"
        price = random.randint(50, 200)
        index = blockchain.new_transaction(distributor_sender, client_recipient, product, price)
        print(f"New transaction created: {distributor_sender} -> {client_recipient} (Product: {product}), Index: {index}")

        blockchain.distributor_confirm_dispatch(index)
        sleep(2)  # Simulate some time passing

        blockchain.consumer_confirm_reception(index)
        sleep(5)  # Simulate some time passing

        # Resolve delivery issues and deduct security deposit if necessary
        blockchain.resolve_delivery_issues()

        sleep(5)  # Simulate some time passing

except KeyboardInterrupt:
    print("Mining process termination requested.")
