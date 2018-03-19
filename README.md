# multisig-helper

## Pre-requirements

- Python >= 3.6.0
- coind with legacy RPC methods
- Insight API

## Getting started

### 0. Install dependent libraries

```bash
pip install -r requirements.txt
```

### 1. Configure coind

- dstra.conf

```
# Don't use these value on production environment. After changing value, edit hard coded username and password in main.py.
server=1
rpcuser=a
rpcpassword=b
```

- main.py

```python
# Edit this line
# e.g.
# a: dstrarpc
# b: 8vwDMP7h9u2AWUsuwKgHnjvf8xrj95kFxTKQDXMmjRczHtECvZESwh4xU2gpRdzJ
RPC = Proxy("http://a:b@127.0.0.1:5170")
```

### 2. Create keypair

create_keypair

- John

```bash
John$ python main.py create_keypair
Account name: multisig-helper_keypair_2018-03-22T03:55:49.139309
P2PKH address: FH56xZJKuo1UigWspi6bcDc7raDpFgLgvX
Public key(hex): 037a5ccae392617092684a9933e38ce73167af71bc04415829b168271ab4135744
Private key: LWBgfyaQ72L1WnRHLdoegnzWY3YsPV5CncgfDDBKZNdKeJc472k5
```

- Yamada

```bash
Yamada$ python main.py create_keypair
Account name: multisig-helper_keypair_2018-03-22T03:55:49.667917
P2PKH address: FDnfBdWxnTpJykssd2p3offTSuU3Nwa8Fh
Public key(hex): 0221ea2712033b05149c71a4fa7a212f95c0d6ca4436370fc780b57c9bd42ff3d2
Private key: LQom16ekJvPxCatW2e29jgkDMVHk3EfbikUJLjuubxRs9wGd6H92
```

Share ``Public key(hex)`` on your team and backup ``Private key``.

### 3. Create multi-sig wallet

create_wallet REQUIRED_KEYS HEXADECIMAL_PUBLIC_KEYS...

- John or Yamada

```bash
Yamada$ python main.py create_wallet 2 037a5ccae392617092684a9933e38ce73167af71bc04415829b168271ab4135744 0221ea2712033b05149c71a4fa7a212f95c0d6ca4436370fc780b57c9bd42ff3d2
Account name: multisig-helper_wallet_2018-03-22T03:56:16.372161
P2SH address: fLF9S6ndvKstHgY6YTsqAqZstZXwWrAMdi
Redeem script: 5221037a5ccae392617092684a9933e38ce73167af71bc04415829b168271ab4135744210221ea2712033b05149c71a4fa7a212f95c0d6ca4436370fc780b57c9bd42ff3d252ae
Participant public keys: ['FH56xZJKuo1UigWspi6bcDc7raDpFgLgvX', 'FDnfBdWxnTpJykssd2p3offTSuU3Nwa8Fh']
No. of required signs: 2
```

Share ``P2SH address`` and ``Redeem script`` on your team.

### 4. Create transaction

create_tx P2SH_ADDRESS RECIPIENT_LIST_FILE HEXADECIMAL_TX_FILE

- John or Yamada

```csv
FBQi6PxL5ncU1HJMHJrB4BgwFFEX2Ym2pk,111.999
FEQjZND321GuHWKW4rHw1XC3RRyu4Eqefm,222.00000001
FJgjnvYJkob7db2YpmU5YikAkZA7wWXmZJ,333
```

```bash
John$ python main.py create_tx fLF9S6ndvKstHgY6YTsqAqZstZXwWrAMdi recipient.csv tx.txt
TX ID: b35bd37ff659437b0e4fcd4114a6c8724625b87120cfa7320a114bf64c898ccd
TX fee: 1.00000000
Created at: 2018-03-22 12:58:41
Inputs:  --------------------------------------------------------------------------------------------------
2fdbc83e3b53865305eb41017120f03465d72d2d6de4999c430b46fb1cbca552.vout[0] = 1000.0
Outputs: --------------------------------------------------------------------------------------------------
vout[0] = 111.999
FBQi6PxL5ncU1HJMHJrB4BgwFFEX2Ym2pk
vout[1] = 222.00000001
FEQjZND321GuHWKW4rHw1XC3RRyu4Eqefm
vout[2] = 333.0
FJgjnvYJkob7db2YpmU5YikAkZA7wWXmZJ
vout[3] = 332.00099999
fLF9S6ndvKstHgY6YTsqAqZstZXwWrAMdi
Unsigned transaction has been saved on tx.txt.
```

Share ``tx.txt`` to the first signer. **Signer order doesn't matter.**

### 5. Sign and broadcast transaction

sign_tx HEXADECIMAL_TX_FILE REDEEM_SCRIPT PRIVATE_KEY

- John

```bash
John$ python main.py sign_tx tx.txt 5221037a5ccae392617092684a9933e38ce73167af71bc04415829b168271ab4135744210221ea2712033b05149c71a4fa7a212f95c0d6ca4436370fc780b57c9bd42ff3d252ae LWBgfyaQ72L1WnRHLdoegnzWY3YsPV5CncgfDDBKZNdKeJc472k5
TX ID: b35bd37ff659437b0e4fcd4114a6c8724625b87120cfa7320a114bf64c898ccd
TX fee: 1.00000000
Created at: 2018-03-22 12:58:41
Inputs:  --------------------------------------------------------------------------------------------------
2fdbc83e3b53865305eb41017120f03465d72d2d6de4999c430b46fb1cbca552.vout[0] = 1000.0
Outputs: --------------------------------------------------------------------------------------------------
vout[0] = 111.999
FBQi6PxL5ncU1HJMHJrB4BgwFFEX2Ym2pk
vout[1] = 222.00000001
FEQjZND321GuHWKW4rHw1XC3RRyu4Eqefm
vout[2] = 333.0
FJgjnvYJkob7db2YpmU5YikAkZA7wWXmZJ
vout[3] = 332.00099999
fLF9S6ndvKstHgY6YTsqAqZstZXwWrAMdi
Do you want to sign this transaction? [y/N]: y
Signed transaction has been saved on tx.txt.
This TX needs more signs to broadcast.
01000000f129b35a0152a5bc1cfb460b439c99e46d2d2dd76534f020710141eb055386533b3ec8db2f000000009200483045022100b5fe491122cc3815ebc5ee9d07c07150e22e19d0de73bcaac6521de94e8bc11f022005d56bc946785c8c579b4b46d7fedbf586af3f2ed7b846295ad728a8fd17f9e101475221037a5ccae392617092684a9933e38ce73167af71bc04415829b168271ab4135744210221ea2712033b05149c71a4fa7a212f95c0d6ca4436370fc780b57c9bd42ff3d252aeffffffff0460e9909b020000001976a9143d33439d680c28830a9b7602a8d625da513463bd88ac011e392b050000001976a9145e1cdd48b5f1bb54e5b318fca66a4c6fd9272e7988ac00add5c0070000001976a9148d0437d15e5bc8b4779c6a25d558f309c4baa25388ac9f52e1ba0700000017a914434c7ae89bde8412dd7c4a3f16369a9a64d5f5a78700000000
```

Share ``tx.txt`` to the next signer.

- Yamada

```bash
$ python main.py sign_tx tx.txt 5221037a5ccae392617092684a9933e38ce73167af71bc04415829b168271ab4135744210221ea2712033b05149c71a4fa7a212f95c0d6ca4436370fc780b57c9bd42ff3d252ae LQom16ekJvPxCatW2e29jgkDMVHk3EfbikUJLjuubxRs9wGd6H92
TX ID: daedf490758e07c7632135e2d330e2cf469a1b00ed6eaadf7522b63f0654594e
TX fee: 1.00000000
Created at: 2018-03-22 12:58:41
Inputs:  --------------------------------------------------------------------------------------------------
2fdbc83e3b53865305eb41017120f03465d72d2d6de4999c430b46fb1cbca552.vout[0] = 1000.0
Outputs: --------------------------------------------------------------------------------------------------
vout[0] = 111.999
FBQi6PxL5ncU1HJMHJrB4BgwFFEX2Ym2pk
vout[1] = 222.00000001
FEQjZND321GuHWKW4rHw1XC3RRyu4Eqefm
vout[2] = 333.0
FJgjnvYJkob7db2YpmU5YikAkZA7wWXmZJ
vout[3] = 332.00099999
fLF9S6ndvKstHgY6YTsqAqZstZXwWrAMdi
Do you want to sign this transaction? [y/N]: y
Signed transaction has been saved on tx.txt.
Fulfilled the requirement signs.
TX ID: daedf490758e07c7632135e2d330e2cf469a1b00ed6eaadf7522b63f0654594e
TX fee: 1.00000000
Created at: 2018-03-22 12:58:41
Inputs:  --------------------------------------------------------------------------------------------------
2fdbc83e3b53865305eb41017120f03465d72d2d6de4999c430b46fb1cbca552.vout[0] = 1000.0
Outputs: --------------------------------------------------------------------------------------------------
vout[0] = 111.999
FBQi6PxL5ncU1HJMHJrB4BgwFFEX2Ym2pk
vout[1] = 222.00000001
FEQjZND321GuHWKW4rHw1XC3RRyu4Eqefm
vout[2] = 333.0
FJgjnvYJkob7db2YpmU5YikAkZA7wWXmZJ
vout[3] = 332.00099999
fLF9S6ndvKstHgY6YTsqAqZstZXwWrAMdi
Do you want to broadcast this transaction? [y/N]: y
TX ID: daedf490758e07c7632135e2d330e2cf469a1b00ed6eaadf7522b63f0654594e
```

DONE!

## License
