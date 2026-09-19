import os
import sys
import hmac
import hashlib
import time
import json
import requests
from base64 import b64encode
from datetime import datetime

from ..models import db, Account, Holding

BASE_URL = 'https://api.snaptrade.com'


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
    path = "/accounts"
    headers, params = get_snaptrade_headers(path)

    response = requests.get(
        f"{BASE_URL}/accounts",
        params=params,
        headers=headers,
    )

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
    path = "/accounts"
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
        print(f"Processing: {snaptrade_account['id']} status: {snaptrade_account.get('status')}", flush=True, file=sys.stderr)
        if snaptrade_account.get('status') == 'closed':
            continue

        account = Account.query.filter_by(
            external_id=snaptrade_account['id']
        ).first()
        if account is None:
            continue

        # Use the canonical path without /api/v1 prefix
        positions_path = f"/accounts/{snaptrade_account['id']}/positions"
        positions_headers, positions_params = get_snaptrade_headers(positions_path)

        positions_response = requests.get(
            f"{BASE_URL}/accounts/{snaptrade_account['id']}/positions",
            params=positions_params,
            headers=positions_headers,
        )

        print(f"Account: {snaptrade_account['id']}", flush=True, file=sys.stderr)
        print(f"Status: {positions_response.status_code}", flush=True, file=sys.stderr)
        print(f"Response: {positions_response.text[:500]}", flush=True, file=sys.stderr)

        if not positions_response.ok:
            continue

        positions = positions_response.json()

        for h in positions:
            symbol_data = h.get('symbol', {})
            symbol = symbol_data.get('symbol') or symbol_data.get('ticker')
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
            holding.market_value = float(holding.quantity or 0) * float(holding.market_price or 0)
            holding.currency = h.get('currency', {}).get('code', 'CAD') if isinstance(h.get('currency'), dict) else h.get('currency', 'CAD')
            account.last_synced_at = datetime.utcnow()
            count += 1

    db.session.commit()
    return {'holdings': count}