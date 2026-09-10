from ..models import db, MerchantRule, Category

PLAID_CATEGORY_MAP = {
    'FOOD_AND_DRINK': 'Food & Drink',
    'GROCERIES': 'Groceries',
    'RESTAURANTS': 'Food & Drink',
    'COFFEE_SHOP': 'Coffee',
    'TRANSPORTATION': 'Transportation',
    'GAS_STATIONS': 'Gas & Fuel',
    'TRAVEL': 'Travel',
    'RENT_AND_UTILITIES': 'Utilities',
    'ENTERTAINMENT': 'Entertainment',
    'SHOPPING': 'Shopping',
    'PERSONAL_CARE': 'Personal Care',
    'HEALTH_AND_FITNESS': 'Health & Fitness',
    'EDUCATION': 'Education',
    'INCOME': 'Income',
    'TRANSFER_IN': 'Transfer',
    'TRANSFER_OUT': 'Transfer',
    'LOAN_PAYMENTS': 'Loan Payments',
    'BANK_FEES': 'Bank Fees',
    'SUBSCRIPTION': 'Subscriptions',
}

KEYWORD_MAP = {
    'tim hortons': 'Coffee',
    'starbucks': 'Coffee',
    'second cup': 'Coffee',
    'loblaws': 'Groceries',
    'metro': 'Groceries',
    'sobeys': 'Groceries',
    'no frills': 'Groceries',
    'freshco': 'Groceries',
    'costco': 'Groceries',
    'uber eats': 'Food & Drink',
    'doordash': 'Food & Drink',
    'skip the dishes': 'Food & Drink',
    'netflix': 'Subscriptions',
    'spotify': 'Subscriptions',
    'apple.com': 'Subscriptions',
    'presto': 'Transportation',
    'uber': 'Transportation',
    'esso': 'Gas & Fuel',
    'petro': 'Gas & Fuel',
    'shell': 'Gas & Fuel',
    'lcbo': 'Entertainment',
    'cineplex': 'Entertainment',
    'shoppers': 'Pharmacy',
    'rexall': 'Pharmacy',
    'rogers': 'Utilities',
    'bell': 'Utilities',
    'telus': 'Utilities',
    'hydro': 'Utilities',
    'enbridge': 'Utilities',
    'amazon': 'Shopping',
    'payroll': 'Income',
    'e-transfer': 'Transfer',
    'interac': 'Transfer',
}

def categorize_transaction(txn, plaid_category=None):
    search_str = (txn.merchant_name or txn.raw_name or '').lower().strip()

    rules = MerchantRule.query.all()
    for rule in rules:
        if rule.merchant_pattern in search_str:
            txn.category_id = rule.category_id
            txn.needs_categorization = False
            return True

    if plaid_category and plaid_category in PLAID_CATEGORY_MAP:
        category = Category.query.filter_by(name=PLAID_CATEGORY_MAP[plaid_category]).first()        
        if category:
            txn.category_id = category.id
            txn.needs_categorization = False
            return True

    for keyword, category_name in KEYWORD_MAP.items():
        if keyword in search_str:
            category = Category.query.filter_by(name=category_name).first()
            if category:
                txn.category_id = category.id
                txn.needs_categorization = False
                return True

    txn.needs_categorization = True
    return False