QUERY_LENGTH = {
    "Entreprise": 100,
    "ChequeIn": 100,
    "ChequeOut": 100,
    "VirementReçu": 100,
    "VirementEmis": 100,
    "AvisIn": 100,
    "AvisOut": 100,
    "Transaction": 100,
    "TransactionIn": 100,
    "TransactionOut": 100,
    "EntrepriseAccount": 100,
}


def getLen(model):
    return QUERY_LENGTH.get(model, None)
