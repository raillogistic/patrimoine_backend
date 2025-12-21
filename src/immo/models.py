from django.db import models


def _join_desc_parts(*parts):
    return " - ".join(str(part) for part in parts if part not in (None, ""))


class Affectation(models.Model):
    number = models.TextField(verbose_name="numero")
    date_of_decision = models.DateField(
        verbose_name="date de decision", blank=True, null=True
    )
    createdat = models.DateTimeField(
        db_column="createdAt", verbose_name="date de creation"
    )  # Field name made lowercase.
    updatedat = models.DateTimeField(
        db_column="updatedAt", verbose_name="date de mise a jour"
    )  # Field name made lowercase.
    department = models.ForeignKey(
        "Department",
        models.DO_NOTHING,
        db_column="departmentId",
        blank=True,
        null=True,
        verbose_name="departement",
    )  # Field name made lowercase.
    employer = models.ForeignKey(
        "Employer",
        models.DO_NOTHING,
        db_column="employerId",
        blank=True,
        null=True,
        verbose_name="employeur",
    )  # Field name made lowercase.
    article = models.ForeignKey(
        "Article",
        models.DO_NOTHING,
        db_column="articleId",
        blank=True,
        null=True,
        verbose_name="article",
    )  # Field name made lowercase.
    location = models.ForeignKey(
        "Location",
        models.DO_NOTHING,
        db_column="locationId",
        blank=True,
        null=True,
        verbose_name="localisation",
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.
    health = models.TextField(verbose_name="etat")  # This field type is a guess.
    observation = models.CharField(
        verbose_name="observation", max_length=500, blank=True, null=True
    )
    transferexplanation = models.CharField(
        db_column="transferExplanation",
        max_length=500,
        blank=True,
        null=True,
        verbose_name="motif de transfert",
    )  # Field name made lowercase.
    enddate = models.DateField(
        db_column="endDate", blank=True, null=True, verbose_name="date de fin"
    )  # Field name made lowercase.
    block = models.IntegerField(
        db_column="blockId", blank=True, null=True, verbose_name="bloc"
    )  # Field name made lowercase.
    room = models.IntegerField(
        db_column="roomId", blank=True, null=True, verbose_name="salle"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(
            self.number, self.article, self.department, self.location, self.employer
        )

    class Meta:
        managed = False
        db_table = "Affectation"
        verbose_name = "affectation"
        verbose_name_plural = "affectations"


class Amortization(models.Model):
    year = models.IntegerField(verbose_name="annee")
    depreciationamount = models.DecimalField(
        db_column="depreciationAmount",
        max_digits=65,
        decimal_places=30,
        verbose_name="montant amortissement",
    )  # Field name made lowercase.
    remainingvalue = models.DecimalField(
        db_column="remainingValue",
        max_digits=65,
        decimal_places=30,
        verbose_name="valeur restante",
    )  # Field name made lowercase.
    article = models.ForeignKey(
        "Article", models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    createdat = models.DateTimeField(
        db_column="createdAt", verbose_name="date de creation"
    )  # Field name made lowercase.
    updatedat = models.DateTimeField(
        db_column="updatedAt", verbose_name="date de mise a jour"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.year, self.article, self.depreciationamount)

    class Meta:
        managed = False
        db_table = "Amortization"
        verbose_name = "amortissement"
        verbose_name_plural = "amortissements"


class Appliance(models.Model):
    article = models.OneToOneField(
        "Article", models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    brand = models.TextField(verbose_name="marque", blank=True, null=True)
    model = models.TextField(verbose_name="modele", blank=True, null=True)
    powerusage = models.TextField(
        db_column="powerUsage",
        blank=True,
        null=True,
        verbose_name="consommation electrique",
    )  # Field name made lowercase.
    dimensions = models.TextField(verbose_name="dimensions", blank=True, null=True)
    weight = models.FloatField(verbose_name="poids", blank=True, null=True)
    warranty = models.BooleanField(verbose_name="garantie", blank=True, null=True)
    energyrating = models.TextField(
        db_column="energyRating",
        blank=True,
        null=True,
        verbose_name="classe energetique",
    )  # Field name made lowercase.
    noiselevel = models.FloatField(
        db_column="noiseLevel", blank=True, null=True, verbose_name="niveau de bruit"
    )  # Field name made lowercase.
    capacity = models.TextField(verbose_name="capacite", blank=True, null=True)
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.brand, self.model, self.article)

    class Meta:
        managed = False
        db_table = "Appliance"
        verbose_name = "appareil"
        verbose_name_plural = "appareils"


class Article(models.Model):
    code = models.CharField(max_length=300, verbose_name="code")
    desc = models.CharField(
        max_length=500, verbose_name="description", db_column="description"
    )
    acquiringdate = models.DateField(
        verbose_name="date d acquisition", blank=True, null=True
    )
    beginningfiscalprice = models.DecimalField(
        max_digits=65, decimal_places=30, verbose_name="prix fiscal initial"
    )
    totalfiscalprice = models.DecimalField(
        max_digits=65, decimal_places=30, verbose_name="prix fiscal total"
    )
    quantity = models.IntegerField(verbose_name="quantite")
    createdat = models.DateTimeField(
        db_column="createdAt", verbose_name="date de creation"
    )  # Field name made lowercase.
    updatedat = models.DateTimeField(
        db_column="updatedAt", verbose_name="date de mise a jour"
    )  # Field name made lowercase.
    supplier = models.ForeignKey(
        "Supplier",
        models.DO_NOTHING,
        db_column="supplierId",
        blank=True,
        null=True,
        verbose_name="fournisseur",
    )  # Field name made lowercase.
    family = models.ForeignKey(
        "Family",
        models.DO_NOTHING,
        db_column="familyId",
        blank=True,
        null=True,
        verbose_name="famille",
    )  # Field name made lowercase.
    observation = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="observation"
    )
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.
    amortizationyears = models.IntegerField(
        db_column="amortizationYears",
        blank=True,
        null=True,
        verbose_name="duree d amortissement",
    )  # Field name made lowercase.
    deliverynote = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="bon de livraison"
    )
    financingmethod = models.CharField(
        max_length=300, blank=True, null=True, verbose_name="methode de financement"
    )
    invoice = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="facture"
    )
    type = models.BooleanField(verbose_name="type")
    references = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="references"
    )
    serialnumber = models.CharField(
        db_column="serialNumber",
        max_length=500,
        blank=True,
        null=True,
        verbose_name="numero de serie",
    )  # Field name made lowercase.
    exitedat = models.DateTimeField(
        db_column="exitedAt", blank=True, null=True, verbose_name="date de sortie"
    )  # Field name made lowercase.
    isexited = models.BooleanField(
        db_column="isExited", verbose_name="est sorti"
    )  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = "Article"
        verbose_name = "article"
        verbose_name_plural = "articles"


class Articleexitreason(models.Model):
    article = models.ForeignKey(
        Article, models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    exitreason = models.ForeignKey(
        "Exitreason",
        models.DO_NOTHING,
        db_column="exitReasonId",
        verbose_name="motif de sortie",
    )  # Field name made lowercase.
    createdat = models.DateTimeField(
        db_column="createdAt", verbose_name="date de creation"
    )  # Field name made lowercase.
    isreversed = models.BooleanField(
        db_column="isReversed", verbose_name="est annule"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.article, self.exitreason)

    class Meta:
        managed = False
        db_table = "ArticleExitReason"
        verbose_name = "motif de sortie d article"
        verbose_name_plural = "motifs de sortie d article"


class Block(models.Model):
    blockname = models.CharField(max_length=150, verbose_name="nom du bloc")
    designation = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="description",
        db_column="description",
    )
    location = models.IntegerField(
        db_column="locationId", verbose_name="localisation"
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.blockname, self.description)

    class Meta:
        managed = False
        db_table = "Block"
        verbose_name = "bloc"
        verbose_name_plural = "blocs"


class Construction(models.Model):
    article = models.OneToOneField(
        Article, models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    constructiontype = models.TextField(
        db_column="constructionType",
        blank=True,
        null=True,
        verbose_name="type de construction",
    )  # Field name made lowercase.
    constructionmaterial = models.TextField(
        db_column="constructionMaterial",
        blank=True,
        null=True,
        verbose_name="materiau de construction",
    )  # Field name made lowercase.
    constructiondate = models.DateTimeField(
        db_column="constructionDate",
        blank=True,
        null=True,
        verbose_name="date de construction",
    )  # Field name made lowercase.
    constructionlocation = models.TextField(
        db_column="constructionLocation",
        blank=True,
        null=True,
        verbose_name="lieu de construction",
    )  # Field name made lowercase.
    constructioncost = models.DecimalField(
        db_column="constructionCost",
        max_digits=65,
        decimal_places=30,
        blank=True,
        null=True,
        verbose_name="cout de construction",
    )  # Field name made lowercase.
    contractor = models.TextField(verbose_name="entrepreneur", blank=True, null=True)
    architect = models.TextField(verbose_name="architecte", blank=True, null=True)
    constructionnotes = models.TextField(
        db_column="constructionNotes",
        blank=True,
        null=True,
        verbose_name="notes de construction",
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(
            self.constructiontype,
            self.constructionmaterial,
            self.constructionlocation,
            self.article,
        )

    class Meta:
        managed = False
        db_table = "Construction"
        verbose_name = "construction"
        verbose_name_plural = "constructions"


class Department(models.Model):
    departmentname = models.CharField(
        unique=True, max_length=150, verbose_name="nom du departement"
    )
    designation = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="description",
        db_column="description",
    )
    createdat = models.DateTimeField(
        db_column="createdAt", verbose_name="date de creation"
    )  # Field name made lowercase.
    updatedat = models.DateTimeField(
        db_column="updatedAt", verbose_name="date de mise a jour"
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.departmentname, self.description)

    class Meta:
        managed = False
        db_table = "Department"
        verbose_name = "departement"
        verbose_name_plural = "departements"


class Departmenthistory(models.Model):
    department = models.ForeignKey(
        Department,
        models.DO_NOTHING,
        db_column="departmentId",
        verbose_name="departement",
    )  # Field name made lowercase.
    oldname = models.CharField(
        db_column="oldName", max_length=150, verbose_name="ancien nom"
    )  # Field name made lowercase.
    newname = models.CharField(
        db_column="newName", max_length=150, verbose_name="nouveau nom"
    )  # Field name made lowercase.
    changedat = models.DateTimeField(
        db_column="changedAt", verbose_name="date de modification"
    )  # Field name made lowercase.
    changedby = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="changedBy", verbose_name="modifie par"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.oldname, self.newname)

    class Meta:
        managed = False
        db_table = "DepartmentHistory"
        verbose_name = "historique de departement"
        verbose_name_plural = "historiques de departement"


class Electronics(models.Model):
    article = models.OneToOneField(
        Article, models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    brand = models.TextField(verbose_name="marque", blank=True, null=True)
    model = models.TextField(verbose_name="modele", blank=True, null=True)
    serialnumber = models.TextField(
        db_column="serialNumber",
        blank=True,
        null=True,
        verbose_name="numero de serie",
    )  # Field name made lowercase.
    warranty = models.BooleanField(verbose_name="garantie", blank=True, null=True)
    power = models.TextField(verbose_name="puissance", blank=True, null=True)
    voltage = models.TextField(verbose_name="tension", blank=True, null=True)
    dimensions = models.TextField(verbose_name="dimensions", blank=True, null=True)
    weight = models.FloatField(verbose_name="poids", blank=True, null=True)
    screensize = models.FloatField(
        db_column="screenSize",
        blank=True,
        null=True,
        verbose_name="taille ecran",
    )  # Field name made lowercase.
    batterylife = models.IntegerField(
        db_column="batteryLife",
        blank=True,
        null=True,
        verbose_name="autonomie batterie",
    )  # Field name made lowercase.
    connectivity = models.TextField(verbose_name="connectivite", blank=True, null=True)
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    # @property
    # def desc(self):
    #     return _join_desc_parts(self.brand, self.model, self.serialnumber, self.article)

    class Meta:
        managed = False
        db_table = "Electronics"
        verbose_name = "electronique"
        verbose_name_plural = "electroniques"


class Employer(models.Model):
    employername = models.TextField(verbose_name="nom de l employeur")
    industry = models.TextField(verbose_name="secteur", blank=True, null=True)
    location = models.TextField(verbose_name="localisation", blank=True, null=True)
    email = models.TextField(verbose_name="email", blank=True, null=True)
    phone = models.TextField(verbose_name="telephone", blank=True, null=True)
    website = models.TextField(verbose_name="site web", blank=True, null=True)
    createdat = models.DateTimeField(
        db_column="createdAt", verbose_name="date de creation"
    )  # Field name made lowercase.
    updatedat = models.DateTimeField(
        db_column="updatedAt", verbose_name="date de mise a jour"
    )  # Field name made lowercase.
    department = models.ForeignKey(
        Department,
        models.DO_NOTHING,
        db_column="departmentId",
        verbose_name="departement",
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.employername, self.department)

    class Meta:
        managed = False
        db_table = "Employer"
        verbose_name = "employeur"
        verbose_name_plural = "employeurs"


class Exitreason(models.Model):
    title = models.CharField(max_length=300, verbose_name="titre")
    designation = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="description",
        db_column="description",
    )
    date = models.DateTimeField(verbose_name="date")
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.title, self.description)

    class Meta:
        managed = False
        db_table = "ExitReason"
        verbose_name = "motif de sortie"
        verbose_name_plural = "motifs de sortie"


class Family(models.Model):
    code = models.CharField(max_length=300, verbose_name="code")
    familyname = models.TextField(verbose_name="nom de la famille")
    desc = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="description"
    )
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.
    amortissementduration = models.IntegerField(
        db_column="amortissementDuration",
        blank=True,
        null=True,
        verbose_name="duree d amortissement",
    )  # Field name made lowercase.
    category = models.TextField(
        verbose_name="categorie", blank=True, null=True
    )  # This field type is a guess.

    @property
    def desc(self):
        return _join_desc_parts(self.code, self.familyname)

    class Meta:
        managed = False
        db_table = "Family"
        verbose_name = "famille"
        verbose_name_plural = "familles"


class File(models.Model):
    filename = models.TextField(verbose_name="nom du fichier")
    mimetype = models.TextField(verbose_name="type mime")
    createdat = models.DateTimeField(
        db_column="createdAt", verbose_name="date de creation"
    )  # Field name made lowercase.
    updatedat = models.DateTimeField(
        db_column="updatedAt", verbose_name="date de mise a jour"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.filename)

    class Meta:
        managed = False
        db_table = "File"
        verbose_name = "fichier"
        verbose_name_plural = "fichiers"


class Financingmethod(models.Model):
    method = models.TextField(unique=True, verbose_name="methode")
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.method)

    class Meta:
        managed = False
        db_table = "Financingmethod"
        verbose_name = "methode de financement"
        verbose_name_plural = "methodes de financement"


class Fueltype(models.Model):
    gaztype = models.TextField(unique=True, verbose_name="type de gaz")
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.gaztype)

    class Meta:
        managed = False
        db_table = "FuelType"
        verbose_name = "type de carburant"
        verbose_name_plural = "types de carburant"


class Furniture(models.Model):
    article = models.OneToOneField(
        Article, models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    material = models.TextField(verbose_name="materiau", blank=True, null=True)
    dimensions = models.TextField(verbose_name="dimensions", blank=True, null=True)
    weight = models.FloatField(verbose_name="poids", blank=True, null=True)
    color = models.TextField(verbose_name="couleur", blank=True, null=True)
    brand = models.TextField(verbose_name="marque", blank=True, null=True)
    style = models.TextField(verbose_name="style", blank=True, null=True)
    room = models.TextField(verbose_name="piece", blank=True, null=True)
    assemblyrequired = models.BooleanField(
        db_column="assemblyRequired",
        blank=True,
        null=True,
        verbose_name="montage requis",
    )  # Field name made lowercase.
    warranty = models.BooleanField(verbose_name="garantie", blank=True, null=True)
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.brand, self.style, self.material, self.article)

    class Meta:
        managed = False
        db_table = "Furniture"
        verbose_name = "mobilier"
        verbose_name_plural = "mobiliers"


class Land(models.Model):
    article = models.OneToOneField(
        Article, models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    landtype = models.TextField(
        db_column="landType", blank=True, null=True, verbose_name="type de terrain"
    )  # Field name made lowercase.
    areasize = models.FloatField(
        db_column="areaSize", blank=True, null=True, verbose_name="surface"
    )  # Field name made lowercase.
    location = models.TextField(verbose_name="localisation", blank=True, null=True)
    zoningtype = models.TextField(
        db_column="zoningType", blank=True, null=True, verbose_name="type de zonage"
    )  # Field name made lowercase.
    soilquality = models.TextField(
        db_column="soilQuality", blank=True, null=True, verbose_name="qualite du sol"
    )  # Field name made lowercase.
    wateraccess = models.BooleanField(
        db_column="waterAccess", blank=True, null=True, verbose_name="acces a l eau"
    )  # Field name made lowercase.
    ownerhistory = models.TextField(
        db_column="ownerHistory",
        blank=True,
        null=True,
        verbose_name="historique proprietaire",
    )  # Field name made lowercase.
    currentuse = models.TextField(
        db_column="currentUse", blank=True, null=True, verbose_name="usage actuel"
    )  # Field name made lowercase.
    purchaseprice = models.DecimalField(
        db_column="purchasePrice",
        max_digits=65,
        decimal_places=30,
        blank=True,
        null=True,
        verbose_name="prix d achat",
    )  # Field name made lowercase.
    propertytax = models.DecimalField(
        db_column="propertyTax",
        max_digits=65,
        decimal_places=30,
        blank=True,
        null=True,
        verbose_name="taxe fonciere",
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.landtype, self.location, self.article)

    class Meta:
        managed = False
        db_table = "Land"
        verbose_name = "terrain"
        verbose_name_plural = "terrains"


class Location(models.Model):
    locationname = models.CharField(max_length=150, verbose_name="nom de localisation")
    desc = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="description"
    )
    createdat = models.DateTimeField(
        db_column="createdAt", verbose_name="date de creation"
    )  # Field name made lowercase.
    updatedat = models.DateTimeField(
        db_column="updatedAt", verbose_name="date de mise a jour"
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.
    parent = models.ForeignKey(
        "self",
        models.DO_NOTHING,
        db_column="parentId",
        blank=True,
        null=True,
        verbose_name="parent",
        related_name="children",
    )  # Field name made lowercase.
    type = models.TextField(verbose_name="type")  # This field type is a guess.
    barcode = models.CharField(
        unique=True, max_length=300, blank=True, null=True, verbose_name="code barre"
    )

    @property
    def desc(self):
        return _join_desc_parts(self.locationname, self.description)

    class Meta:
        managed = True
        db_table = "Location"
        verbose_name = "localisation"
        verbose_name_plural = "localisations"
        unique_together = (("parent", "locationname"),)


class Machinery(models.Model):
    article = models.OneToOneField(
        Article, models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    machinetype = models.TextField(
        db_column="machineType", blank=True, null=True, verbose_name="type de machine"
    )  # Field name made lowercase.
    manufacturer = models.TextField(verbose_name="fabricant", blank=True, null=True)
    model = models.TextField(verbose_name="modele", blank=True, null=True)
    power = models.TextField(verbose_name="puissance", blank=True, null=True)
    dimensions = models.TextField(verbose_name="dimensions", blank=True, null=True)
    weight = models.FloatField(verbose_name="poids", blank=True, null=True)
    capacity = models.TextField(verbose_name="capacite", blank=True, null=True)
    maintenanceschedule = models.TextField(
        db_column="maintenanceSchedule",
        blank=True,
        null=True,
        verbose_name="plan de maintenance",
    )  # Field name made lowercase.
    operatingmanual = models.TextField(
        db_column="operatingManual",
        blank=True,
        null=True,
        verbose_name="manuel d utilisation",
    )  # Field name made lowercase.
    warranty = models.BooleanField(verbose_name="garantie", blank=True, null=True)
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(
            self.machinetype, self.manufacturer, self.model, self.article
        )

    class Meta:
        managed = False
        db_table = "Machinery"
        verbose_name = "machine"
        verbose_name_plural = "machines"


class Medicalsupply(models.Model):
    article = models.OneToOneField(
        Article, models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    expirationdate = models.DateTimeField(
        db_column="expirationDate",
        blank=True,
        null=True,
        verbose_name="date d expiration",
    )  # Field name made lowercase.
    manufacturer = models.TextField(verbose_name="fabricant", blank=True, null=True)
    usage = models.TextField(verbose_name="usage", blank=True, null=True)
    storagerequirements = models.TextField(
        db_column="storageRequirements",
        blank=True,
        null=True,
        verbose_name="conditions de stockage",
    )  # Field name made lowercase.
    safetyinstructions = models.TextField(
        db_column="safetyInstructions",
        blank=True,
        null=True,
        verbose_name="consignes de securite",
    )  # Field name made lowercase.
    batchnumber = models.TextField(
        db_column="batchNumber",
        blank=True,
        null=True,
        verbose_name="numero de lot",
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(
            self.manufacturer, self.batchnumber, self.expirationdate, self.article
        )

    class Meta:
        managed = False
        db_table = "MedicalSupply"
        verbose_name = "fourniture medicale"
        verbose_name_plural = "fournitures medicales"


class Notification(models.Model):
    message = models.CharField(max_length=500, verbose_name="message")
    read = models.BooleanField(verbose_name="lu")
    createdat = models.DateTimeField(
        db_column="createdAt", verbose_name="date de creation"
    )  # Field name made lowercase.
    updatedat = models.DateTimeField(
        db_column="updatedAt", verbose_name="date de mise a jour"
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.
    article = models.ForeignKey(
        Article,
        models.DO_NOTHING,
        db_column="articleId",
        blank=True,
        null=True,
        verbose_name="article",
    )  # Field name made lowercase.
    affectation = models.ForeignKey(
        Affectation,
        models.DO_NOTHING,
        db_column="affectationId",
        blank=True,
        null=True,
        verbose_name="affectation",
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.message)

    class Meta:
        managed = False
        db_table = "Notification"
        verbose_name = "notification"
        verbose_name_plural = "notifications"


class Refreshtoken(models.Model):
    token = models.TextField(unique=True, verbose_name="jeton")
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.
    createdat = models.DateTimeField(
        db_column="createdAt", verbose_name="date de creation"
    )  # Field name made lowercase.
    updatedat = models.DateTimeField(
        db_column="updatedAt", verbose_name="date de mise a jour"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.token)

    class Meta:
        managed = False
        db_table = "RefreshToken"
        verbose_name = "jeton de rafraichissement"
        verbose_name_plural = "jetons de rafraichissement"


class Room(models.Model):
    roomname = models.CharField(max_length=150, verbose_name="nom de la salle")
    desc = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="description"
    )
    block = models.ForeignKey(
        Block, models.DO_NOTHING, db_column="blockId", verbose_name="bloc"
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.roomname, self.block)

    class Meta:
        managed = False
        db_table = "Room"
        verbose_name = "salle"
        verbose_name_plural = "salles"


class Software(models.Model):
    article = models.OneToOneField(
        Article, models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    licensekey = models.TextField(
        db_column="licenseKey",
        blank=True,
        null=True,
        verbose_name="cle de licence",
    )  # Field name made lowercase.
    version = models.TextField(verbose_name="version", blank=True, null=True)
    platform = models.TextField(verbose_name="plateforme", blank=True, null=True)
    developer = models.TextField(verbose_name="developpeur", blank=True, null=True)
    releasedate = models.DateTimeField(
        db_column="releaseDate",
        blank=True,
        null=True,
        verbose_name="date de sortie",
    )  # Field name made lowercase.
    supportedos = models.TextField(
        db_column="supportedOS", blank=True, null=True, verbose_name="os supporte"
    )  # Field name made lowercase.
    licensetype = models.TextField(
        db_column="licenseType", blank=True, null=True, verbose_name="type de licence"
    )  # Field name made lowercase.
    expirationdate = models.DateTimeField(
        db_column="expirationDate",
        blank=True,
        null=True,
        verbose_name="date d expiration",
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(
            self.licensekey, self.version, self.platform, self.article
        )

    class Meta:
        managed = False
        db_table = "Software"
        verbose_name = "logiciel"
        verbose_name_plural = "logiciels"


class Stationery(models.Model):
    article = models.OneToOneField(
        Article, models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    brand = models.TextField(verbose_name="marque", blank=True, null=True)
    type = models.TextField(verbose_name="type", blank=True, null=True)
    color = models.TextField(verbose_name="couleur", blank=True, null=True)
    material = models.TextField(verbose_name="materiau", blank=True, null=True)
    inktype = models.TextField(
        db_column="inkType", blank=True, null=True, verbose_name="type d encre"
    )  # Field name made lowercase.
    pointsize = models.FloatField(
        db_column="pointSize", blank=True, null=True, verbose_name="taille de pointe"
    )  # Field name made lowercase.
    packsize = models.IntegerField(
        db_column="packSize", blank=True, null=True, verbose_name="taille du lot"
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(
            self.brand, self.type, self.color, self.material, self.article
        )

    class Meta:
        managed = False
        db_table = "Stationery"
        verbose_name = "fourniture de bureau"
        verbose_name_plural = "fournitures de bureau"


class Subfamily(models.Model):
    code = models.CharField(max_length=150, verbose_name="code")
    subfamilyname = models.TextField(verbose_name="nom de la sous-famille")
    desc = models.CharField(
        max_length=500, blank=True, null=True, verbose_name="description"
    )
    family = models.ForeignKey(
        Family,
        models.DO_NOTHING,
        db_column="familyId",
        blank=True,
        null=True,
        verbose_name="famille",
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.code, self.subfamilyname, self.family)

    class Meta:
        managed = False
        db_table = "Subfamily"
        verbose_name = "sous-famille"
        verbose_name_plural = "sous-familles"


class Supplier(models.Model):
    socialreason = models.CharField(max_length=300, verbose_name="raison sociale")
    address = models.CharField(
        max_length=300, blank=True, null=True, verbose_name="adresse"
    )
    email = models.CharField(
        max_length=300, blank=True, null=True, verbose_name="email"
    )
    telephonenumber = models.CharField(
        max_length=300, blank=True, null=True, verbose_name="numero de telephone"
    )
    nif = models.TextField(verbose_name="nif", blank=True, null=True)
    nic = models.TextField(verbose_name="nic", blank=True, null=True)
    ai = models.TextField(verbose_name="ai", blank=True, null=True)
    rc = models.TextField(verbose_name="rc", blank=True, null=True)
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.socialreason)

    class Meta:
        managed = False
        db_table = "Supplier"
        verbose_name = "fournisseur"
        verbose_name_plural = "fournisseurs"


class Tool(models.Model):
    article = models.OneToOneField(
        Article, models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    tooltype = models.TextField(
        db_column="toolType", blank=True, null=True, verbose_name="type d outil"
    )  # Field name made lowercase.
    brand = models.TextField(verbose_name="marque", blank=True, null=True)
    powersource = models.TextField(
        db_column="powerSource",
        blank=True,
        null=True,
        verbose_name="source d energie",
    )  # Field name made lowercase.
    weight = models.FloatField(verbose_name="poids", blank=True, null=True)
    dimensions = models.TextField(verbose_name="dimensions", blank=True, null=True)
    warranty = models.BooleanField(verbose_name="garantie", blank=True, null=True)
    batterytype = models.TextField(
        db_column="batteryType", blank=True, null=True, verbose_name="type de batterie"
    )  # Field name made lowercase.
    maxpower = models.FloatField(
        db_column="maxPower", blank=True, null=True, verbose_name="puissance max"
    )  # Field name made lowercase.
    usageinstructions = models.TextField(
        db_column="usageInstructions",
        blank=True,
        null=True,
        verbose_name="instructions d utilisation",
    )  # Field name made lowercase.
    user = models.ForeignKey(
        "OldUser", models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(
            self.tooltype, self.brand, self.powersource, self.article
        )

    class Meta:
        managed = False
        db_table = "Tool"
        verbose_name = "outil"
        verbose_name_plural = "outils"


class OldUser(models.Model):
    name = models.TextField(verbose_name="nom")
    fullname = models.TextField(verbose_name="nom complet", blank=True, null=True)
    hashedpassword = models.TextField(
        db_column="hashedPassword", verbose_name="mot de passe chiffre"
    )  # Field name made lowercase.
    role = models.TextField(
        verbose_name="role", blank=True, null=True
    )  # This field type is a guess.
    isauthenticated = models.BooleanField(
        db_column="isAuthenticated", verbose_name="est authentifie"
    )  # Field name made lowercase.
    createdat = models.DateTimeField(
        db_column="createdAt", verbose_name="date de creation"
    )  # Field name made lowercase.
    updateat = models.DateTimeField(
        db_column="updateAt", verbose_name="date de mise a jour"
    )  # Field name made lowercase.
    email = models.TextField(verbose_name="email", blank=True, null=True)
    phonenumber = models.TextField(
        db_column="phoneNumber",
        blank=True,
        null=True,
        verbose_name="numero de telephone",
    )  # Field name made lowercase.
    bio = models.TextField(verbose_name="bio", blank=True, null=True)
    colorprimary = models.CharField(
        db_column="colorPrimary",
        max_length=10,
        blank=True,
        null=True,
        verbose_name="couleur principale",
    )  # Field name made lowercase.
    layout = models.TextField(
        verbose_name="mise en page"
    )  # This field type is a guess.
    sidermenutype = models.TextField(
        db_column="siderMenuType", verbose_name="type de menu lateral"
    )  # Field name made lowercase. This field type is a guess.
    photo = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="photo"
    )

    @property
    def desc(self):
        return _join_desc_parts(self.fullname, self.name, self.email)

    class Meta:
        managed = False
        db_table = "User"
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"


class Vehicle(models.Model):
    article = models.OneToOneField(
        Article, models.DO_NOTHING, db_column="articleId", verbose_name="article"
    )  # Field name made lowercase.
    vehiclemodel = models.ForeignKey(
        "Vehiclemodel",
        models.DO_NOTHING,
        db_column="VehicleModelId",
        blank=True,
        null=True,
        verbose_name="modele du vehicule",
    )  # Field name made lowercase.
    vehicletype = models.ForeignKey(
        "Vehicletype",
        models.DO_NOTHING,
        db_column="VehicleTypeId",
        blank=True,
        null=True,
        verbose_name="type de vehicule",
    )  # Field name made lowercase.
    licenseplate = models.TextField(
        db_column="licensePlate", verbose_name="plaque d immatriculation"
    )  # Field name made lowercase.
    manufacturer = models.TextField(verbose_name="fabricant", blank=True, null=True)
    year = models.IntegerField(verbose_name="annee", blank=True, null=True)
    color = models.TextField(verbose_name="couleur", blank=True, null=True)
    mileage = models.FloatField(verbose_name="kilometrage", blank=True, null=True)
    fueltype = models.TextField(
        db_column="fuelType", blank=True, null=True, verbose_name="type de carburant"
    )  # Field name made lowercase.
    enginesize = models.FloatField(
        db_column="engineSize", blank=True, null=True, verbose_name="cylindree"
    )  # Field name made lowercase.
    vin = models.TextField(verbose_name="numero de serie", blank=True, null=True)
    registrationdate = models.DateField(
        db_column="registrationDate",
        blank=True,
        null=True,
        verbose_name="date d immatriculation",
    )  # Field name made lowercase.
    servicehistory = models.TextField(
        db_column="serviceHistory",
        blank=True,
        null=True,
        verbose_name="historique d entretien",
    )  # Field name made lowercase.
    insurancepolicy = models.TextField(
        db_column="insurancePolicy",
        blank=True,
        null=True,
        verbose_name="police d assurance",
    )  # Field name made lowercase.
    user = models.ForeignKey(
        OldUser, models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.licenseplate, self.vehiclemodel, self.vehicletype)

    class Meta:
        managed = False
        db_table = "Vehicle"
        verbose_name = "vehicule"
        verbose_name_plural = "vehicules"


class Vehiclemodel(models.Model):
    model = models.CharField(unique=True, max_length=300, verbose_name="modele")
    user = models.ForeignKey(
        OldUser, models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.model)

    class Meta:
        managed = False
        db_table = "VehicleModel"
        verbose_name = "modele de vehicule"
        verbose_name_plural = "modeles de vehicule"


class Vehicletype(models.Model):
    type = models.CharField(unique=True, max_length=300, verbose_name="type")
    vehiclemodel = models.ForeignKey(
        Vehiclemodel,
        models.DO_NOTHING,
        db_column="vehiclemodelId",
        verbose_name="modele du vehicule",
    )  # Field name made lowercase.
    user = models.ForeignKey(
        OldUser, models.DO_NOTHING, db_column="userId", verbose_name="utilisateur"
    )  # Field name made lowercase.

    @property
    def desc(self):
        return _join_desc_parts(self.type, self.vehiclemodel)

    class Meta:
        managed = False
        db_table = "VehicleType"
        verbose_name = "type de vehicule"
        verbose_name_plural = "types de vehicule"
