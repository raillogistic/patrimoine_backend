






class CampagneInventaireCustomMutation:
    nested = {
        #'groupes' : 'GroupeComptage',
#'enregistrements' : 'EnregistrementInventaire',

    }



class GroupeComptageCustomMutation:
    nested = {
        #'enregistrements' : 'EnregistrementInventaire',
#'campagne' : 'CampagneInventaire',
#'utilisateur' : 'User',

    }



class EnregistrementInventaireCustomMutation:
    nested = {
        #'campagne' : 'CampagneInventaire',
#'groupe' : 'GroupeComptage',
#'lieu' : 'Location',
#'departement' : 'Department',
#'article' : 'Article',

    }


