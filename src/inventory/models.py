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
        CONTROLE = "CONTROLE", "Contrôle / Supervision"

    compare_to_group = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groupes_comparaison",
        verbose_name="Groupe de comparaison",
        help_text="Groupe avec lequel comparer les scans.",
    )

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
    lieux_autorises = models.ManyToManyField(
        "immo.Location",
        blank=True,
        related_name="groupes_autorises",
        verbose_name="Lieux autorises",
        help_text=(
            "Lieux sur lesquels le groupe est autorise a operer. "
            "Les sous-lieux des parents selectionnes sont aussi autorises."
        ),
    )

    @property
    def designation(self):
        return f"{self.nom} "

    designation.fget.short_description = "Designation"

    class Meta:
        verbose_name = "Groupe de comptage"
        verbose_name_plural = "Groupes de comptage"
        ordering = ("nom",)

    def __str__(self) -> str:
        return f"{self.nom} - {self.utilisateur_id}"

    def get_lieux_autorises(self):
        """Retourne les lieux autorises, en incluant les descendants."""
        from immo.models import Location

        racines = list(self.lieux_autorises.all())
        if not racines:
            return Location.objects.none()

        ids_autorises = {loc.id for loc in racines}
        a_parcourir = list(ids_autorises)

        while a_parcourir:
            enfants = list(
                Location.objects.filter(parent_id__in=a_parcourir).values_list(
                    "id", flat=True
                )
            )
            nouveaux = [loc_id for loc_id in enfants if loc_id not in ids_autorises]
            if not nouveaux:
                break
            ids_autorises.update(nouveaux)
            a_parcourir = nouveaux

        return Location.objects.filter(id__in=ids_autorises)

    def is_lieu_autorise(self, lieu):
        """Indique si un lieu est autorise pour ce groupe."""
        if not lieu:
            return False
        return self.get_lieux_autorises().filter(id=lieu.id).exists()


# -- Enregistrements de comptage -------------------------------------------
class EnregistrementInventaire(ModeleHorodatage):
    """Enregistre un scan d'article dans un lieu selectionne."""

    class EtatMateriel(models.TextChoices):
        bien = "BIEN", "Bien"
        moyenne = "MOYENNE", "Moyenne"
        hors_service = "HORS_SERVICE", "Hors service"

    is_extra = models.BooleanField(
        default=False, null=True, blank=True, verbose_name="Est extra?"
    )

    observation = models.TextField(null=True, blank=True, verbose_name="Observation")
    serial_number = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Numéro de série"
    )
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
    observation = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observation",
        help_text="Observation complementaire associee a l'enregistrement.",
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Numero de serie",
        help_text="Numero de serie associe a l'article scanne.",
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
    image = models.ImageField(
        upload_to="inventaire/images",
        blank=True,
        null=True,
        verbose_name="Image",
        help_text="Image associee a l'enregistrement.",
    )
    image2 = models.ImageField(
        upload_to="inventaire/images",
        blank=True,
        null=True,
        verbose_name="Image",
        help_text="Image associee a l'enregistrement.",
    )
    image3 = models.ImageField(
        upload_to="inventaire/images",
        blank=True,
        null=True,
        verbose_name="Image",
        help_text="Image associee a l'enregistrement.",
    )
    custom_desc = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description personnalisée",
        help_text="Description personnalisée associee a l'enregistrement.",
    )
    # localisation GPS
    latitude = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="Latitude",
        help_text="Latitude associee a l'enregistrement.",
    )
    longitude = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="Longitude",
        help_text="Longitude associee a l'enregistrement.",
    )

    class Meta:
        verbose_name = "Enregistrement d'inventaire"
        verbose_name_plural = "Enregistrements d'inventaire"
        ordering = ("-capture_le",)

    @classmethod
    def check_extra(cls, ids: [str]):
        EnregistrementInventaire.objects.filter(id__in=ids).update(is_extra=True)
        return True

    def chhange_extra(self):
        self.is_extra = not self.is_extra
        self.save()
        return

    def __str__(self) -> str:
        return f"{self.code_article} @ {self.lieu_id}"


# -- Types d'emplacement ----------------------------------------------------
class PositionType(ModeleHorodatage):
    """Type d'emplacement pour categoriser les positions."""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom du type",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="Slug",
    )
    desc = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        db_column="description",
    )

    class Meta:
        verbose_name = "Type d'emplacement"
        verbose_name_plural = "Types d'emplacement"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


from datetime import date

from immo.models import Article


class RapprochementInventaire(ModeleHorodatage):
    """Rapprochement d'inventaire."""

    campagne = models.OneToOneField(
        CampagneInventaire,
        on_delete=models.CASCADE,
        related_name="rapprochement",
        verbose_name="Campagne",
        null=True,
        blank=True,
    )
    date = models.DateField(null=True, blank=True, verbose_name="Date")
    created_at = models.DateTimeField(
        auto_now_add=True, null=True, blank=True, verbose_name="Date de création"
    )

    @classmethod
    def new_rapprochement(cls, test: str = ""):
        if RapprochementInventaire.objects.filter(id=1).exists():
            pass
        else:
            return RapprochementInventaire.objects.create(date=date.today(), id="1")
        r = RapprochementInventaire.objects.get(id=1)
        r.details.all().delete()
        for a in Article.objects.all():
            de = RapprochementInventaireDetail.objects.create(
                rapprochement=r, article=a
            )
            if EnregistrementInventaire.objects.filter(article=a).exists:
                de.quantite = (
                    EnregistrementInventaire.objects.filter(article=a).first().quantite
                )
                de.save()

        return r

    # def update(self):
    #     EnregistrementInventaire


class RapprochementInventaireDetail(ModeleHorodatage):
    """Detail du rapprochement d'inventaire."""

    class StatutRapprochement(models.TextChoices):
        MATCH = "MATCH", "Correspondance"
        MANQUANT = "MANQUANT", "Manquant (Ecart Négatif)"
        SURPLUS = "SURPLUS", "Surplus (Ecart Positif)"

    rapprochement = models.ForeignKey(
        RapprochementInventaire,
        on_delete=models.CASCADE,
        related_name="details",
        verbose_name="Rapprochement",
        help_text="Rapprochement rattache a ce detail.",
    )
    article = models.ForeignKey(
        "immo.Article",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="rapprochements_details",
        verbose_name="Article",
        help_text="Article reference si le code correspond au referentiel.",
    )
    code_article = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Code article",
        help_text="Code article (utile pour les surplus non references).",
    )
    statut = models.CharField(
        max_length=20,
        choices=StatutRapprochement.choices,
        default=StatutRapprochement.MATCH,
        verbose_name="Statut",
    )
    confirmed = models.BooleanField(
        default=False, null=True, blank=True, verbose_name="Confirmé?"
    )
    observation = models.TextField(null=True, blank=True, verbose_name="Observation")

    class Meta:
        verbose_name = "Détail du rapprochement"
        verbose_name_plural = "Détails du rapprochement"


# -- Emplacements -----------------------------------------------------------
class Position(ModeleHorodatage):
    """Emplacement hierarchique pour le comptage d'inventaire."""

    name = models.CharField(
        max_length=150,
        verbose_name="Nom",
    )
    desc = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        db_column="description",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Parent",
    )
    location_type = models.ForeignKey(
        PositionType,
        on_delete=models.PROTECT,
        related_name="locations",
        verbose_name="Type",
        null=True,
        blank=True,
    )
    barcode = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Code-barres",
        help_text="Code-barres unique pour identifier l'emplacement.",
    )

    class Meta:
        verbose_name = "Emplacement"
        verbose_name_plural = "Emplacements"
        unique_together = ("parent", "name")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    @property
    def full_path(self) -> str:
        """Retourne le chemin hierarchique complet depuis la racine.

        Exemple: "Rouiba - ADM 01 - Etage 01"
        """
        path_parts = [self.name]
        current = self.parent
        while current is not None:
            path_parts.insert(0, current.name)
            current = current.parent
        return " - ".join(path_parts)


# -- Articles scannes -------------------------------------------------------
class ScannedArticle(ModeleHorodatage):
    """Enregistre un article scanne lors d'une campagne d'inventaire."""

    class EtatMateriel(models.TextChoices):
        BIEN = "BIEN", "Bien"
        MOYENNE = "MOYENNE", "Moyenne"
        HORS_SERVICE = "HORS_SERVICE", "Hors service"

    campagne = models.ForeignKey(
        CampagneInventaire,
        on_delete=models.PROTECT,
        related_name="articles_scannes",
        verbose_name="Campagne",
        help_text="Campagne rattachee a cet enregistrement.",
    )
    groupe = models.ForeignKey(
        GroupeComptage,
        on_delete=models.PROTECT,
        related_name="articles_scannes",
        verbose_name="Groupe de comptage",
        help_text="Groupe ayant effectue le scan.",
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        related_name="articles_scannes",
        verbose_name="Emplacement",
        help_text="Emplacement ou l'article a ete scanne.",
    )
    article = models.ForeignKey(
        "immo.Article",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="scans_inventaire",
        verbose_name="Article",
        help_text="Article reference si le code correspond au referentiel.",
    )
    code_article = models.CharField(
        max_length=300,
        verbose_name="Code article",
        help_text="Code unique scanne sur l'article.",
    )
    etat = models.CharField(
        max_length=20,
        choices=EtatMateriel.choices,
        null=True,
        blank=True,
        verbose_name="Etat du materiel",
        help_text="Etat du materiel lors de l'enregistrement.",
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Numero de serie",
        help_text="Numero de serie associe a l'article scanne.",
    )
    observation = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observation",
        help_text="Observation complementaire associee a l'enregistrement.",
    )
    source_scan = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Source du scan",
        help_text="Origine du scan (integrated scanner, RFID, manuel...).",
    )
    capture_le = models.DateTimeField(
        default=timezone.now,
        verbose_name="Capture le",
        help_text="Date et heure de capture du scan.",
    )

    class Meta:
        verbose_name = "Article scanne"
        verbose_name_plural = "Articles scannes"
        ordering = ("-capture_le",)

    def __str__(self) -> str:
        return f"{self.code_article} @ {self.position_id}"
