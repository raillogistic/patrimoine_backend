from django.db.models import Count, Q
from django.utils import timezone
from .models import (
    CampagneInventaire,
    EnregistrementInventaire,
    GroupeComptage,
    RapprochementInventaire,
    RapprochementInventaireDetail,
)
from immo.models import Article


class InventoryReconciliationService:
    """Service gérant la logique de réconciliation et de rapprochement d'inventaire."""

    def __init__(self, campagne: CampagneInventaire):
        self.campagne = campagne

    def get_scanned_items_status(self):
        """
        Analyse les scans pour déterminer les articles validés et les conflits.
        
        Règles:
        1. Validé si scanné par un groupe de type 'CONTROLE' (Groupe C).
        2. Validé si scanné par au moins 2 groupes de type 'COMPTAGE' (A et B).
        3. Sinon -> Conflit (à vérifier par le groupe C).
        """
        # Récupérer tous les scans de la campagne (hors "extra")
        scans = (
            EnregistrementInventaire.objects.filter(campagne=self.campagne)
            .exclude(is_extra=True)
            .select_related("groupe", "article")
            .values("code_article", "groupe__id", "groupe__role", "article__id")
        )

        item_status = {}
        # Structure: code_article -> { 'groups': set(), 'has_controle': False, 'article_id': id }

        for scan in scans:
            code = scan["code_article"]
            if code not in item_status:
                item_status[code] = {
                    "comptage_groups": set(),
                    "has_controle": False,
                    "article_id": scan["article__id"],
                }
            
            role = scan["groupe__role"]
            if role == GroupeComptage.RoleComptage.CONTROLE:
                item_status[code]["has_controle"] = True
            elif role == GroupeComptage.RoleComptage.COMPTAGE:
                item_status[code]["comptage_groups"].add(scan["groupe__id"])

        valid_codes = set()
        conflict_codes = set()
        
        # Classification
        for code, data in item_status.items():
            is_valid = False
            
            # Règle 1: Validé par Groupe C
            if data["has_controle"]:
                is_valid = True
            
            # Règle 2: Validé par consensus (au moins 2 groupes de comptage différents)
            elif len(data["comptage_groups"]) >= 2:
                is_valid = True
            
            if is_valid:
                valid_codes.add(code)
            else:
                conflict_codes.add(code)

        return {
            "valid_codes": valid_codes,
            "conflict_codes": conflict_codes,
            "item_data": item_status # Pour récupérer les article_id plus tard
        }

    def generate_rapprochement(self):
        """
        Génère ou met à jour le rapprochement d'inventaire.
        Compare l'inventaire validé (physique) avec le registre (théorique).
        """
        status_data = self.get_scanned_items_status()
        valid_codes = status_data["valid_codes"]
        item_data = status_data["item_data"]

        # 1. Inventaire Théorique (Registry)
        # On suppose que le registre est la source de vérité pour les articles "supposés être là"
        # Filtre: Articles non sortis (isexited=False)
        theoretical_articles = Article.objects.filter(isexited=False)
        theoretical_ids = set(theoretical_articles.values_list("id", flat=True))

        # 2. Création du Rapprochement
        rapprochement, created = RapprochementInventaire.objects.update_or_create(
            campagne=self.campagne,
            defaults={"date": timezone.now().date()}
        )
        
        # Si le rapprochement existait déjà, on nettoie les anciens détails
        if not created:
            rapprochement.details.all().delete()

        details_to_create = []
        processed_article_ids = set()

        # 3. Comparaison & Catégorisation

        # A. MATCH & SURPLUS (Basé sur ce qui a été trouvé physiquement)
        for code in valid_codes:
            article_id = item_data[code]["article_id"]
            
            if article_id:
                # Si l'article a déjà été traité via un autre code, on ignore (deduplication)
                if article_id in processed_article_ids:
                    continue
                
                processed_article_ids.add(article_id)

                if article_id in theoretical_ids:
                    # MATCH: Trouvé et est dans le registre actif
                    status = RapprochementInventaireDetail.StatutRapprochement.MATCH
                else:
                    # SURPLUS: Trouvé mais PAS dans le registre actif (ex: sorti ou autre)
                    status = RapprochementInventaireDetail.StatutRapprochement.SURPLUS
                
                details_to_create.append(
                    RapprochementInventaireDetail(
                        rapprochement=rapprochement,
                        article_id=article_id,
                        code_article=code,
                        statut=status,
                        confirmed=True
                    )
                )
            else:
                # SURPLUS: Code scanné mais non lié à un article (Inconnu)
                details_to_create.append(
                    RapprochementInventaireDetail(
                        rapprochement=rapprochement,
                        article_id=None,
                        code_article=code,
                        statut=RapprochementInventaireDetail.StatutRapprochement.SURPLUS,
                        confirmed=True
                    )
                )

        # B. MANQUANT (Ce qui est dans le registre mais PAS trouvé physiquement)
        # On compare les IDs théoriques avec ceux qu'on a traités
        missing_ids = theoretical_ids - processed_article_ids
        
        # Récupérer les objets Article manquants pour les lier
        missing_articles = Article.objects.filter(id__in=missing_ids)
        
        for article in missing_articles:
            details_to_create.append(
                RapprochementInventaireDetail(
                    rapprochement=rapprochement,
                    article=article,
                    code_article=article.code,
                    statut=RapprochementInventaireDetail.StatutRapprochement.MANQUANT,
                    confirmed=True 
                )
            )

        # Bulk create pour la performance
        RapprochementInventaireDetail.objects.bulk_create(details_to_create)

        return rapprochement

    def get_conflicts_for_review(self):
        """Retourne la liste des articles en conflit nécessitant l'intervention du Groupe C."""
        status_data = self.get_scanned_items_status()
        return list(status_data["conflict_codes"])
