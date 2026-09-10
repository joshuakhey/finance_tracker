import os
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_sync_request import TransactionsSyncRequest

from ..models import db, Transaction, Account, AccountBalance
from .categorizer import categorize_transaction

def get_plaid_client():
    config = plaid.Configuration(
        host=plaid.Environment.Production,
        api_key={
            'clientId': os.environ['PLAID_CLIENT_ID'],
            'secret': os.environ['PLAID_SECRET'],
        }
    )
    return plaid_api.PlaidApi(plaid.ApiClient(config))

def transactions_sync():
    client = get_plaid_client()
    request = TransactionsSyncRequest(
            access_token=os.environ['PLAID_ACCESS_TOKEN'],
            cursor=None 
        )

    response = client.transactions_sync(request)   
    
    count = 0
    for plaid_txn in response.added:
        txn = Transaction.query.filter_by(external_id=plaid_txn.transaction_id).first()
        if txn is None:
            txn = Transaction(external_id=plaid_txn.transaction_id)
            db.session.add(txn)
        
        txn.amount = plaid_txn.amount
        txn.date = plaid_txn.date
        txn.merchant_name = plaid_txn.merchant_name
        txn.raw_name = plaid_txn.name
        txn.pending = plaid_txn.pending
        account = Account.query.filter_by(external_id=plaid_txn.account_id).first()
        if account is None:
            continue
        txn.account_id = account.id        
        categorize_transaction(txn, plaid_category=plaid_txn.category[0] if plaid_txn.category else None)

        count += 1
    
    db.session.commit()
    return {'transactions': count}
    