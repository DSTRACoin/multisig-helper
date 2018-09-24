import csv
import datetime
from decimal import *

import click
import requests

from btcrpc import Proxy, RpcException


def get_account_name(identifier='keypair', dt=datetime.datetime.utcnow()):
    return f'multisig-helper_{identifier}_{dt.isoformat()}'


@click.group()
def keypair():
    pass


@keypair.command()
@click.pass_context
def create_keypair(ctx):
    """Create keypair"""
    account = get_account_name()
    r = RPC.getaccountaddress(account)
    print(f'Account name: {account}')
    ctx.invoke(export_keypair, address=r)


@keypair.command()
@click.argument('address')
def export_keypair(address):
    """
    Export keypair
    """
    # validate address
    r = RPC.validateaddress(address)
    if not r['isvalid']:
        click.echo(click.style(f'Invalid address: {address}', fg='red'))
        return
    if not r['ismine']:
        click.echo(click.style(f'Missing private key: {address}', fg='red'))
        return
    public_key_hex = r['pubkey']

    # retrieve private key
    private_key = RPC.dumpprivkey(address)

    print(f'P2PKH address: {address}\n'
          f'Public key(hex): {public_key_hex}\n'
          f'Private key: {private_key}')


@keypair.command()
@click.pass_context
@click.argument('private_key')
def import_keypair(ctx, private_key):
    """
    Import keypair
    """
    account = get_account_name()
    try:
        RPC.importprivkey(private_key, account)
    except RpcException as e:
        print(e)
        return
    print(f'Account name: {account}')
    r = RPC.getaddressesbyaccount(account)[0]
    ctx.invoke(export_keypair, public_key=r)


@click.group()
def wallet():
    pass


@wallet.command()
@click.pass_context
@click.argument('required_keys', type=click.IntRange(1))
@click.argument('hexadecimal_public_keys', nargs=-1, required=True)
def create_wallet(ctx, required_keys, hexadecimal_public_keys):
    """
    Create m-n multisig wallet
    """
    r = RPC.createmultisig(required_keys, [*hexadecimal_public_keys])

    print(f'P2SH address: {r["address"]}\n'
          f'Redeem script: {r["redeemScript"]}\n'
          f'Participant public keys: {",".join(hexadecimal_public_keys)}\n'
          f'No. of required signs: {required_keys}')

    click.echo(click.style(f'Multi-sig wallet was created successfully. Keep P2SH address and Redeem script in safe place.', fg='green'))

@wallet.command()
@click.argument('p2sh_address')
def dump_wallet(p2sh_address):
    """
    Dump multi-sig wallet
    """
    # validate script public key
    r = RPC.validateaddress(p2sh_address)
    if not r['isvalid']:
        click.echo(click.style(f'Invalid address: {p2sh_address}', fg='red'))
        return
    if not r['ismine']:  # TODO: not tested on this case
        click.echo(click.style(f'Missing redeem script?: {p2sh_address}', fg='red'))
        return
    if not r['script'] == 'multisig':  # TODO: not tested on this case
        click.echo(click.style(f'Not multisig wallet: {p2sh_address}', fg='red'))
        return

    print(f'P2SH address: {p2sh_address}\n'
          f'Redeem script: {r["hex"]}\n'
          f'Participant public keys: {r["addresses"]}\n'
          f'No. of required signs: {r["sigsrequired"]}')


@click.group()
def tx():
    pass


@tx.command()
@click.pass_context
@click.argument('p2sh_address')
@click.argument('recipient_list_file', type=click.File('r'))
@click.argument('hexadecimal_tx_file', type=click.File('w+'))
def create_tx(ctx, p2sh_address, recipient_list_file, hexadecimal_tx_file):
    """
    Create transaction
    """
    r = requests.get(f'{INSIGHT_URL}/addr/{p2sh_address}/utxo')
    uxtos = r.json()
    if r.status_code is not requests.codes.ok:
        print(uxtos)
        click.echo(click.style(f'Insight API returns the error.', fg='red'))
        return

    recipient_reader = csv.reader(recipient_list_file)
    recipients = {x[0]: Decimal(x[1]) for x in recipient_reader if len(x) == 2}

    fee = Decimal('0.1')  # TODO: implement fee estimator
    balance = Decimal(f"{sum(map(lambda x: x['amount'], uxtos)):.9f}")
    total_amount = sum(recipients.values())
    charge = balance - total_amount - fee

    if charge < 0:
        click.echo(click.style(f'Insufficient balance: {balance} < {total_amount} + {fee}', fg='red'))
        return

    recipients[p2sh_address] = float(charge)  # Send charge to the sender address

    vins = [{'txid': x['txid'], 'vout': x['vout']} for x in uxtos]  # TODO: implement UXTO selector

    norm_recipients = {k: float(v) for k, v in recipients.items()}

    hexadecimal_tx = RPC.createrawtransaction(vins, norm_recipients)
    hexadecimal_tx_file.write(hexadecimal_tx)

    ctx.invoke(dump_tx, hexadecimal_tx=hexadecimal_tx)

    print(f'Unsigned transaction has been saved on {hexadecimal_tx_file.name}.')


@tx.command()
@click.pass_context
@click.argument('hexadecimal_tx_file', type=click.File('r+'))
@click.argument('redeem_script')
@click.argument('private_key')
def sign_tx(ctx, hexadecimal_tx_file, redeem_script, private_key):
    """
    Sign transaction
    """
    hexadecimal_tx = hexadecimal_tx_file.read()

    ctx.invoke(dump_tx, hexadecimal_tx=hexadecimal_tx)
    click.confirm('Do you want to sign this transaction?', abort=True)

    tx = RPC.decoderawtransaction(hexadecimal_tx)

    def _(vin):
        def __(txid, index):
            r = RPC.getrawtransaction(txid, 1)
            scriptPubKey = [x['scriptPubKey'] for x in r['vout'] if x['n'] == index]
            assert len(scriptPubKey) == 1
            return scriptPubKey[0]['hex']

        return {
            'txid': vin['txid'],
            'vout': vin['vout'],
            'scriptPubKey': __(vin['txid'], vin['vout']),
            'redeemScript': redeem_script,
        }

    signed_tx = RPC.signrawtransaction(hexadecimal_tx, list(map(_, tx['vin'])), [private_key])

    hexadecimal_tx_file.seek(0)
    hexadecimal_tx_file.truncate()
    hexadecimal_tx_file.write(signed_tx['hex'])

    print(f'Signed transaction has been saved on {hexadecimal_tx_file.name}.')

    if not signed_tx['complete']:
        print(f'This TX needs more signs to broadcast.\n'
              f'{signed_tx["hex"]}')
    else:
        click.echo(click.style('Fulfilled the requirement signs.', fg='green'))
        ctx.invoke(broadcast_tx, hexadecimal_tx=signed_tx['hex'])


@tx.command()
@click.argument('hexadecimal_tx')
def dump_tx(hexadecimal_tx):
    """
    Dump transaction
    """
    r = RPC.decoderawtransaction(hexadecimal_tx)

    def _vin(txid, index):
        class _(object):
            def __init__(self, txid, index, value):
                self.txid = txid
                self.index = index
                self.value = value

            def __add__(self, other):
                return self.value + other

            def __radd__(self, other):
                return self.__add__(other)

            def __str__(self):
                return f'{self.txid}.vout[{self.index}] = {self.value}'

        r = RPC.getrawtransaction(txid, 1)
        value = [x['value'] for x in r['vout'] if x['n'] == index]
        assert len(value) == 1
        return _(txid, index, value[0])

    def _vout(index, addresses, value):
        class _(object):
            def __init__(self, index, addresses, value):
                self.index = index
                self.address = addresses
                self.value = value

            def __add__(self, other):
                return self.value + other

            def __radd__(self, other):
                return self.__add__(other)

            def __str__(self):
                return f'vout[{self.index}] = {self.value}\n' + '\n'.join(self.address)

        return _(index, addresses, value)

    txid = r['txid']
    vin = [_vin(x['txid'], x['vout']) for x in r['vin']]
    vout = [_vout(x['n'], x['scriptPubKey']['addresses'], x['value']) for x in r['vout']]
    fee = sum(vin) - sum(vout)

    print(f'TX ID: {txid}\n'
          f'TX fee: {fee:.8f}\n')

    print('Inputs:  --------------------------------------------------------------------------------------------------')
    print('\n'.join(map(str, vin)))

    print('Outputs: --------------------------------------------------------------------------------------------------')
    print('\n'.join(map(str, vout)))


@tx.command()
@click.pass_context
@click.argument('hexadecimal_tx')
def broadcast_tx(ctx, hexadecimal_tx):
    """
    Broadcast transaction
    """
    ctx.invoke(dump_tx, hexadecimal_tx=hexadecimal_tx)
    click.confirm('Do you want to broadcast this transaction?', abort=True)
    r = RPC.sendrawtransaction(hexadecimal_tx)
    print(f'TX ID: {r}')


INSIGHT_URL = 'https://blocks.dstra.io/api'

RPC = Proxy("http://a:b@127.0.0.1:5270")

CLI = click.CommandCollection(sources=[
    keypair,
    wallet,
    tx
])

if __name__ == '__main__':
    CLI()
