










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






class ArticleInventaireCustomMutation:
    nested = {
        #'campagne' : 'CampagneInventaire',
#'article' : 'Article',
#'lieu_initial' : 'Location',

    }








class PositionTypeCustomMutation:
    nested = {
        #'locations' : 'Position',

    }



class PositionCustomMutation:
    nested = {
        #'children' : 'Position',
#'articles_scannes' : 'ScannedArticle',
#'parent' : 'Position',
#'location_type' : 'PositionType',

    }



class ScannedArticleCustomMutation:
    nested = {
        #'campagne' : 'CampagneInventaire',
#'groupe' : 'GroupeComptage',
#'position' : 'Position',
#'article' : 'Article',

    }






class RapprochementInventaireCustomMutation:
    nested = {
        #'campagne' : 'CampagneInventaire',

    }






class RapprochementInventaireDetailCustomMutation:
    nested = {
        #'rapprochement' : 'RapprochementInventaire',
#'article' : 'Article',

    }


