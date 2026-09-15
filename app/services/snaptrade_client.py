import os
import requests

from ..models import db, Account, Holding

def get_snaptrade_client():
    return {
        'userId': os.environ['SNAPTRADE_USER_ID'],
        'userSecret': os.environ['SNAPTRADE_USER_SECRET'],
        'clientId': os.environ['SNAPTRADE_CLIENT_ID'],
    }

def holdings_sync():

    credentials = get_snaptrade_client()
    BASE_URL = 'https://api.snaptrade.com/api/v1'

    response = requests.get(
        f'{BASE_URL}/accounts',
        params=credentials
    )
    accounts = response.json()
    
    count = 0
    for snaptrade_account in accounts:
        account = Account.query.filter_by(
            external_id=snaptrade_account['id']
        ).first()
        if account is None:
            continue

        holdings_response = requests.get(
            f'{BASE_URL}/accounts/{snaptrade_account["id"]}/holdings',
            params=credentials
        )
    
        for h in holdings_response.json():
            # upsert by symbol + account.id
            holding = Holding.query.filter_by(
                symbol=h['symbol'],
                account_id=account.id
            ).first()
            if holding is None:
                holding = Holding(symbol=h['symbol']['symbol'], account_id=account.id)
                db.session.add(holding)

            # set fields matching your model
            holding.quantity = h['units']
            holding.average_price = h['average_purchase_price']
            holding.market_price = h['price']
            holding.market_value = holding.quantity * holding.market_price
            count += 1

    db.session.commit()
    return {'holdings': count}
    