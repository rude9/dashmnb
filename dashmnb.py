#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# mnb.py

# codes form code from https://github.com/dashpay/electrum-dash
# ref : https://github.com/dashpay/dash/blob/v0.12.1.x/dash-docs/protocol-documentation.md

import sys, os
sys.path.append( os.path.join( os.path.dirname(__file__), '.' ) )
sys.path.append( os.path.join( os.path.dirname(__file__), '.', 'dashlib' ) )

import argparse
import time

from config import *
from mnb_misc import *
from mnb_mnconf import *
from mnb_rpc import *
from mnb_start import *
from mnb_xfer import *

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException    

def main(args):

    #clear_screen()
    logo_show()

    serverURL = 'http://' + rpcuser + ':' + rpcpassword + '@' + rpcbindip + ':' + str(rpcport)
    access = AuthServiceProxy(serverURL) 

    if TYPE_HW_WALLET == 'keepkey':
        from keepkeylib.client import KeepKeyClient
        from keepkeylib.transport_hid import HidTransport
        
        devices = HidTransport.enumerate()
    
        if len(devices) == 0:
            print('===> No HW Wallet found')
            signing  = False
            
        else:
            transport = HidTransport(devices[0])
            client = KeepKeyClient(transport)
            signing  = True
    
    if len(mpath) == 0:
        sys.exit('please configure bip49 path')
    
    if len(xpub) == 0:
        sys.exit('please configure bip32 xpub')
    
    check_dashd_syncing(access)  

    if args.check or args.status or args.anounce or args.balance or args.maketx or args.xfer:
        mn_config, signing, mns, mna = checking_mn_config(access, signing)
        need_wallet_rescan = checking_wallet_rescan(mn_config, access)

    if args.status or args.anounce or args.balance or args.maketx or args.xfer:
        print_mnstatus(mn_config, mns, mna)

    if need_wallet_rescan:
        sys.exit('\n1) to spend mn payments in HW Wallet, restart Dash-QT or dashd with -rescan\n2) if did -rescan and still see this messge, check if 1K was spent\n')

    if args.anounce:
        mns_to_start = {}
        for x in sorted(list(mn_config.keys())):
            txidtxidn = mn_config.get(x).get('collateral_txidtxidn')
            if (mns.get(txidtxidn, None) != 'ENABLED' and mns.get(txidtxidn, None) != 'PRE_ENABLED'):
                mns_to_start[x] = mn_config[x]
    
        if len(mns_to_start) > 0 and signing:
            start_masternode(mns_to_start, access, client, args.anounce)

    # wallet rescan
    if args.balance or args.maketx or args.xfer:
        if need_wallet_rescan:
            sys.exit('to spend mn payments in HW Wallet, restart Dash-QT or dashd with -rescan')

        for m in sorted(list(mn_config.keys())):
            mn_config[m]["unspent"], mn_config[m]["txs"] = get_unspent_txs(mn_config.get(m), access)

        print_balance(mn_config)

    
    if args.maketx or args.xfer:    
        print('[making txs]')
        if signing:
            for x in sorted(list(mn_config.keys())):
                print('---> signing txs for mn %s: ' % mn_config[x].get('alias'))
                mn_config[x]["signedrawtx"] = make_txs_for_keepkey(mn_config[x], client)

    if args.xfer and signing:
        print('[broadcasting txs]')
        xfertxid = broadcast_signedrawtx(mn_config, access)

        print()
        for x in xfertxid:
            print('\t' + x)


def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument('-c','--check',
                        dest = 'check',
                        action = 'store_true',
                        help='check masternode config') 

    parser.add_argument('-s','--status',
                        dest = 'status',
                        action = 'store_true',
                        help='show masternode status') 

    parser.add_argument('-a','--anounce',
                        dest = 'anounce',
                        action = 'store_true',
                        help='anounce missing masternodes')                        

    parser.add_argument('-b','--balance',
                        dest = 'balance',
                        action = 'store_true',
                        help='show masternodes balance')   

    parser.add_argument('-m','--maketx',
                        dest = 'maketx',
                        action = 'store_true',
                        help='make signed raw tx')

    parser.add_argument('-x','--xfer',
                        dest = 'xfer',
                        action = 'store_true',
                        help='broadcast signed raw tx')


    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()


if __name__ == "__main__":

    if (sys.version_info < (3, 0)):
        sys.exit('need python3')

    args = parse_args()
    main(args)


# end
