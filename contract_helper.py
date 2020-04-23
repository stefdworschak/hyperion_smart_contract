import json
import os
import web3
from web3 import Web3, HTTPProvider, IPCProvider
from web3.middleware import geth_poa_middleware
from solc import compile_standard

import env_vars

NODE_ADDRESS = os.environ.get('IPCProvider', 'No Value Set')
ETH_PK_FILE = os.environ.get('ETH_PK_FILE', 'No Value Set')
CONTRACT_NAME = 'Validator'

class AbiBytecodeMissing(Exception):
    pass

class EthContract(self):
    def __init__(self, node_address, abi=None, bytecode=None, contract_address=None):
        self.abi = abi
        self.bytecode = bytecode
        self.w3 = Web3(IPCProvider(node_address))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        # Pre funded account 
        self.w3.eth.defaultAccount = self.w3.eth.accounts[0]
        self._contract = self.w3.eth.contract(address=contract_address, abi=abi)
        self._functions = self._contract.functions


    def send_transaction(self, function, content):
        _contract_function = getattr(self._functions, function)
        tx_hash = _contract_function(content).transact()
        #tx_hash = self._contract.functions.setMessage('Nihao').transact()
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        return tx_receipt


    def call_function(self, function):
        _contract_function = getattr(self._functions, function)
        #return self._contract.functions.getMessage().call()
        return _contract_function().call()


    def deploy_contract(self, abi=None, bytecode=None):
        if abi is None:
            abi = self.abi
        if bytecode is None:
            bytecode = self.bytecode
        if not abi and not bytecode:
            raise AbiBytecodeMissing("ABI or Bytecode missing")
        deployed_contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        tx_hash = deployed_contract.constructor().transact()
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        self._contract = self.w3.eth.contract(
            address=tx_receipt.contractAddress, abi=abi)
        return tx_receipt.contractAddress


def compile_contract(contract_name):
    with open(f"contracts/sol/{contract_name}.sol", 'r') as file:
        contract_name = file.name
        contract_content = file.read()
        file.close()
    
    options = {}
    options['language'] = 'Solidity'
    options['sources'] = {
        contract_name: {
            'content': contract_content,
        },
    }

    options['settings'] = {
        "outputSelection": {
            "*": {
                "*": [
                    "metadata", "evm.bytecode", 
                    "evm.bytecode.sourceMap"]
                }
            }
        }

    return compile_standard(options)


def to_json():
    compiled_contract = compile_contract(CONTRACT_NAME)
    with open(f'contracts/json/{CONTRACT_NAME}.json', 'w+') as contract:
        contract.write(json.dumps(compiled_contract))
        contract.close()


def from_json(contract_name):
    with open(f'contracts/json/{contract_name}.json', 'r') as file:
        contract_content = json.loads(file.read())
        file.close()
    return contract_content


def get_abi(contract):
    return json.loads(contract['contracts'][f'contracts/sol/{CONTRACT_NAME}.sol'][CONTRACT_NAME]['metadata'])['output']['abi']


def get_bytecode(contract):
    return contract['contracts'][f'contracts/sol/{CONTRACT_NAME}.sol'][CONTRACT_NAME]['evm']['bytecode']['object']


def get_abi_bytecode(contract):
    return [get_abi(contract), get_bytecode(contract)]
