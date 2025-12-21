"""Modeles metiers pour un inventaire simplifie base sur des scans.

Ce module gere :
- Les campagnes d'inventaire (cadre temporel des comptages).
- Les groupes de comptage (un utilisateur, un appareil, un role unique, un PIN).
- Les enregistrements de scans (article, lieu, horodatage).

Notes:
- Pas de validation/verification ni de quantites.
- Chaque scan enregistre la presence d'un article par son code unique.
"""

from django.db import models
from django.utils import timezone


# -- Mixins -----------------------------------------------------------------
class ModeleHorodatage(models.Model):
    """Fournit un suivi temporel uniforme a l'ensemble des entites metier."""

    cree_le = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Cree le",
        help_text="Date et heure de creation de l'enregistrement.",
    )
    modifie_le = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifie le",
        help_text="Date et heure de derniere modification.",
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"{self.__class__.__name__} #{self.pk}"


# -- Campagnes ---------------------------------------------------------------
class CampagneInventaire(ModeleHorodatage):
    """Structure une periode de comptage pour regrouper les scans."""

    class StatutCampagne(models.TextChoices):
        BROUILLON = "BROUILLON", "Brouillon"
        EN_COURS = "EN_COURS", "En cours"
        CLOTUREE = "CLOTUREE", "Cloturee"
        ANNULEE = "ANNULEE", "Annulee"

    code_campagne = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Code de campagne",
        help_text="Identifiant fonctionnel unique de la campagne.",
    )
    nom = models.CharField(
        max_length=150,
        verbose_name="Nom de campagne",
        help_text="Libelle utilise pour identifier la campagne.",
    )

    date_debut = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de debut",
        help_text="Date effective de lancement.",
    )
    date_fin = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de fin",
        help_text="Date de cloture ou fin prevue.",
    )

    class Meta:
        verbose_name = "Campagne d'inventaire"
        verbose_name_plural = "Campagnes d'inventaire"
        ordering = ("-cree_le", "nom")

    def __str__(self) -> str:
        return f"{self.code_campagne} - {self.nom}"


from django.contrib.auth.models import User


# -- Groupes de comptage ----------------------------------------------------
class GroupeComptage(ModeleHorodatage):
    """Regroupe un utilisateur et son appareil pour les operations de comptage."""

    class RoleComptage(models.TextChoices):
        COMPTAGE = "COMPTAGE", "Comptage"

    campagne = models.ForeignKey(
        CampagneInventaire,
        on_delete=models.PROTECT,
        related_name="groupes",
        verbose_name="Campagne",
        help_text="Campagne a laquelle le groupe est rattache.",
    )
    nom = models.CharField(
        max_length=150,
        verbose_name="Nom du groupe",
        help_text="Identifiant court pour reconnaitre l'equipe de comptage.",
    )
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="groupes_comptage",
        verbose_name="Utilisateur",
        help_text="Utilisateur rattache au groupe de comptage.",
    )
    appareil_identifiant = models.CharField(
        max_length=120,
        unique=True,
        verbose_name="Identifiant de l'appareil",
        help_text="Identifiant unique de l'appareil utilise pour scanner.",
    )
    pin_code = models.CharField(
        max_length=12,
        default="0000",
        verbose_name="Code PIN",
        help_text="Code PIN requis pour valider la selection du groupe.",
    )
    role = models.CharField(
        max_length=20,
        choices=RoleComptage.choices,
        default=RoleComptage.COMPTAGE,
        verbose_name="Role",
        help_text="Role unique de l'equipe (comptage).",
    )
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire",
        help_text="Notes ou informations internes sur le groupe.",
    )

    class Meta:
        verbose_name = "Groupe de comptage"
        verbose_name_plural = "Groupes de comptage"
        ordering = ("nom",)

    def __str__(self) -> str:
        return f"{self.nom} - {self.utilisateur_id}"


# -- Enregistrements de comptage -------------------------------------------
class EnregistrementInventaire(ModeleHorodatage):
    """Enregistre un scan d'article dans un lieu selectionne."""

    class EtatMateriel(models.TextChoices):
        bien = "BIEN", "Bien"
        moyenne = "MOYENNE", "Moyenne"
        hors_service = "HORS_SERVICE", "Hors service"

    campagne = models.ForeignKey(
        CampagneInventaire,
        on_delete=models.PROTECT,
        related_name="enregistrements",
        verbose_name="Campagne",
        help_text="Campagne rattachee a cet enregistrement.",
    )
    groupe = models.ForeignKey(
        GroupeComptage,
        on_delete=models.PROTECT,
        related_name="enregistrements",
        verbose_name="Groupe de comptage",
        help_text="Groupe ayant effectue le scan.",
    )
    lieu = models.ForeignKey(
        "immo.Location",
        on_delete=models.PROTECT,
        related_name="enregistrements_inventaire",
        verbose_name="Lieu",
        help_text="Lieu selectionne pour le comptage (direction, location, ...).",
    )
    departement = models.ForeignKey(
        "immo.Department",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="enregistrements_inventaire",
        verbose_name="Departement",
        help_text="Direction ou departement selectionne pour le comptage.",
    )
    article = models.ForeignKey(
        "immo.Article",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="enregistrements_inventaire",
        verbose_name="Article",
        help_text="Article reference si le code correspond au referentiel.",
    )
    code_article = models.CharField(
        max_length=300,
        verbose_name="Code article",
        help_text="Code unique scanne sur l'article (peut etre repete).",
    )
    capture_le = models.DateTimeField(
        default=timezone.now,
        verbose_name="Capture le",
        help_text="Date et heure de capture du scan.",
    )
    source_scan = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Source du scan",
        help_text="Origine du scan (camera, RFID, manuel...).",
    )
    donnees_capture = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Donnees de capture",
        help_text="Donnees supplementaires liees a l'enregistrement.",
    )
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire",
        help_text="Notes complementaires associees a l'enregistrement.",
    )
    # etat du materiel
    etat = models.CharField(
        max_length=20,
        choices=EtatMateriel.choices,
        null=True,
        blank=True,
        verbose_name="Etat du materiel",
        help_text="Etat du materiel lors de l'enregistrement.",
    )

    class Meta:
        verbose_name = "Enregistrement d'inventaire"
        verbose_name_plural = "Enregistrements d'inventaire"
        ordering = ("-capture_le",)

    def __str__(self) -> str:
        return f"{self.code_article} @ {self.lieu_id}"
