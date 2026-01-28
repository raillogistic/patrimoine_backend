








from libs.graphql.serializers import CustomSerializer
from immo.models import Article





#######  CampagneInventaire  #########

class CampagneInventaireCustomSerializer(CustomSerializer):
    pass

#######  GroupeComptage  #########

class GroupeComptageCustomSerializer(CustomSerializer):
    pass

#######  EnregistrementInventaire  #########

class EnregistrementInventaireCustomSerializer(CustomSerializer):
    """Applique la resolution automatique de l'article via le code scanne."""

    def validate(self, data):
        data = super().validate(data)
        code_article = data.get("code_article")
        article = data.get("article")

        if code_article and not article:
            normalized = code_article.strip()
            if normalized:
                data["article"] = Article.objects.filter(code__iexact=normalized).first()

        return data
        



#######  ArticleInventaire  #########

class ArticleInventaireCustomSerializer(CustomSerializer):
    pass
        





#######  PositionType  #########

class PositionTypeCustomSerializer(CustomSerializer):
    pass

#######  Position  #########

class PositionCustomSerializer(CustomSerializer):
    pass

#######  ScannedArticle  #########

class ScannedArticleCustomSerializer(CustomSerializer):
    pass
        



#######  RapprochementInventaire  #########

class RapprochementInventaireCustomSerializer(CustomSerializer):
    pass
        



#######  RapprochementInventaireDetail  #########

class RapprochementInventaireDetailCustomSerializer(CustomSerializer):
    pass
        
