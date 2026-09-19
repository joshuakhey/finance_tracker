import os
import hmac
import hashlib
import time
import json
import requests
from base64 import b64encode
from datetime import datetime
import sys

from ..models import db, Account, Holding

BASE_URL = 'https://api.snaptrade.com/api/v1'


def get_snaptrade_headers(path, body=None):
    client_id = os.environ['SNAPTRADE_CLIENT_ID']
    consumer_key = os.environ['SNAPTRADE_CONSUMER_KEY']
    timestamp = str(int(time.time()))

    query = f"clientId={client_id}&timestamp={timestamp}"

    sig_object = {
        "content": body,
        "path": path,
        "query": query,
    }

    sig_content = json.dumps(sig_object, separators=(',', ':'), sort_keys=True)
    sig_digest = hmac.new(
        consumer_key.encode(),
        sig_content.encode(),
        hashlib.sha256
    ).digest()
    signature = b64encode(sig_digest).decode()

    return {
        "Signature": signature,
        "Content-Type": "application/json",
    }, {"clientId": client_id, "timestamp": timestamp}


def accounts_sync():
    path = "/api/v1/accounts"
    headers, params = get_snaptrade_headers(path)
    response = requests.get(f"{BASE_URL}/accounts", params=params, headers=headers)
    
    if not response.ok:
        raise Exception(f"SnapTrade accounts fetch failed: {response.text}")

    for snaptrade_account in response.json():
        if snaptrade_account.get('status') == 'closed':
            continue

        account = Account.query.filter_by(
            external_id=snaptrade_account['id']
        ).first()
        if account is None:
            account = Account(external_id=snaptrade_account['id'])
            db.session.add(account)

        account.provider = 'snaptrade'
        account.institution = snaptrade_account['institution_name']
        account.account_name = snaptrade_account['name']
        account.account_type = snaptrade_account['meta']['type']
        account.currency = snaptrade_account['meta']['currency']
        account.is_investment = True
        account.account_category = 'investment'

    account.last_synced_at = datetime.utcnow()
    db.session.commit()

def holdings_sync():
    path = "/api/v1/accounts"
    headers, params = get_snaptrade_headers(path)

    response = requests.get(
        f"{BASE_URL}/accounts",
        params=params,
        headers=headers,
    )

    if not response.ok:
        raise Exception(f"SnapTrade accounts fetch failed: {response.text}")

    accounts = response.json()
    print(f"RAW ACCOUNTS RESPONSE: {response.status_code} - {str(accounts)[:200]}", flush=True, file=sys.stderr)
    count = 0

    for snaptrade_account in accounts:
        print(f"Processing: {snaptrade_account['id']} status: {snaptrade_account.get('status')}")
        if snaptrade_account.get('status') == 'closed':
            continue

        account = Account.query.filter_by(
            external_id=snaptrade_account['id']
        ).first()
        if account is None:
            continue

        holdings_path = f"/api/v1/accounts/{snaptrade_account['id']}/holdings"
        holdings_headers, holdings_params = get_snaptrade_headers(holdings_path)

        holdings_response = requests.get(
            f"{BASE_URL}/accounts/{snaptrade_account['id']}/positions",
            params=holdings_params,
            headers=holdings_headers,
        )

        print(f"Account: {snaptrade_account['id']}")
        print(f"Status: {holdings_response.status_code}")
        print(f"Response: {holdings_response.text[:500]}")

        if not holdings_response.ok:
            continue

        positions = holdings_response.json()
        for h in positions:
            symbol = h.get('symbol', {}).get('symbol')
            if not symbol:
                continue

            holding = Holding.query.filter_by(
                symbol=symbol,
                account_id=account.id
            ).first()
            if holding is None:
                holding = Holding(symbol=symbol, account_id=account.id)
                db.session.add(holding)

            holding.quantity = h.get('units', 0)
            holding.average_price = h.get('average_purchase_price', 0)
            holding.market_price = h.get('price', 0)
            holding.market_value = holding.quantity * holding.market_price
            count += 1

    db.session.commit()
    return {'holdings': count}