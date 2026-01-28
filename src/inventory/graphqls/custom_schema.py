import base64
import binascii
import json
import uuid
import datetime

import graphene
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Count, Sum, Q, F, Func, Value, CharField, Avg
from django.db.models.functions import TruncDay, ExtractHour, ExtractYear, Cast, ExtractWeekDay, ExtractMonth
from django.utils import timezone

from libs.graphql.schema.serializers import EnregistrementInventaireSerializer
from inventory.models import EnregistrementInventaire, CampagneInventaire
from inventory.services import InventoryReconciliationService
from immo.models import Article

class StatItem(graphene.ObjectType):
    label = graphene.String()
    value = graphene.Float()
    extra = graphene.String(required=False)

class StatTimeSeries(graphene.ObjectType):
    date = graphene.String()
    value = graphene.Float()

class TopArticleItem(graphene.ObjectType):
    code = graphene.String()
    designation = graphene.String()
    count = graphene.Int()

class StatsContext:
    def __init__(self, group_id=None):
        self.group_id = group_id
        self.queryset = EnregistrementInventaire.objects.all()
        if group_id:
            self.queryset = self.queryset.filter(groupe_id=group_id)

    def total_scans(self):
        return self.queryset.count()

    def scans_by_etat(self):
        qs = self.queryset.values('etat').annotate(c=Count('id')).order_by('-c')
        etat_map = {
            'BIEN': 'Bon état',
            'MOYENNE': 'État moyen',
            'HORS_SERVICE': 'Hors service',
            'EN_PANNE': 'En panne',
            'REFORME': 'Réformé'
        }
        return [StatItem(label=etat_map.get(x['etat'], x['etat'] or 'Non défini'), value=x['c']) for x in qs]

    def scans_by_location(self):
        qs = self.queryset.values('lieu__locationname').annotate(c=Count('id')).order_by('-c')[:20]
        return [StatItem(label=x['lieu__locationname'] or 'Inconnu', value=x['c']) for x in qs]

    def scans_by_group(self):
        qs = self.queryset.values('groupe__nom', 'groupe__id').annotate(c=Count('id')).order_by('-c')
        return [StatItem(label=x['groupe__nom'], value=x['c'], extra=str(x['groupe__id'])) for x in qs]

    def scans_by_campaign(self):
        qs = self.queryset.values('campagne__nom').annotate(c=Count('id')).order_by('-c')
        return [StatItem(label=x['campagne__nom'], value=x['c']) for x in qs]

    def scans_by_date(self):
        qs = self.queryset.annotate(day=TruncDay('capture_le')).values('day').annotate(c=Count('id')).order_by('day')
        return [StatTimeSeries(date=x['day'].isoformat() if x['day'] else None, value=x['c']) for x in qs]

    def scans_by_source(self):
        qs = self.queryset.values('source_scan').annotate(c=Count('id')).order_by('-c')
        return [StatItem(label=x['source_scan'] or 'Inconnu', value=x['c']) for x in qs]

    def scans_with_observation(self):
        return self.queryset.exclude(observation__exact='').exclude(observation__isnull=True).count()

    def scans_with_serial_number(self):
        return self.queryset.exclude(serial_number__exact='').exclude(serial_number__isnull=True).count()

    def scans_by_article_family(self):
        qs = self.queryset.filter(article__isnull=False).values('article__family__familyname').annotate(c=Count('id')).order_by('-c')
        return [StatItem(label=x['article__family__familyname'] or 'Sans famille', value=x['c']) for x in qs]

    def scans_by_article_supplier(self):
        qs = self.queryset.filter(article__isnull=False).values('article__supplier__socialreason').annotate(c=Count('id')).order_by('-c')
        return [StatItem(label=x['article__supplier__socialreason'] or 'Sans fournisseur', value=x['c']) for x in qs]

    def total_value_by_etat(self):
        qs = self.queryset.filter(article__isnull=False).values('etat').annotate(v=Sum('article__totalfiscalprice')).order_by('-v')
        return [StatItem(label=x['etat'] or 'Non défini', value=x['v']) for x in qs]

    def total_value_by_location(self):
        qs = self.queryset.filter(article__isnull=False).values('lieu__locationname').annotate(v=Sum('article__totalfiscalprice')).order_by('-v')[:20]
        return [StatItem(label=x['lieu__locationname'] or 'Inconnu', value=x['v']) for x in qs]

    def scans_without_article_link(self):
        return self.queryset.filter(article__isnull=True).count()

    def scans_by_hour(self):
        qs = self.queryset.annotate(hour=ExtractHour('capture_le')).values('hour').annotate(c=Count('id')).order_by('hour')
        return [StatItem(label=f"{x['hour']}h", value=x['c']) for x in qs]

    def scans_by_department(self):
        qs = self.queryset.values('departement__departmentname').annotate(c=Count('id')).order_by('-c')
        return [StatItem(label=x['departement__departmentname'] or 'Non assigné', value=x['c']) for x in qs]

    def top_scanned_articles(self):
        qs = self.queryset.values('code_article', 'article__desc').annotate(c=Count('id')).order_by('-c')[:10]
        return [TopArticleItem(code=x['code_article'], designation=x['article__desc'] or x['code_article'], count=x['c']) for x in qs]

    def scans_by_user(self):
        qs = self.queryset.values('groupe__utilisateur__username').annotate(c=Count('id')).order_by('-c')
        return [StatItem(label=x['groupe__utilisateur__username'] or 'Inconnu', value=x['c']) for x in qs]

    def scans_by_device(self):
        qs = self.queryset.values('groupe__appareil_identifiant').annotate(c=Count('id')).order_by('-c')
        return [StatItem(label=x['groupe__appareil_identifiant'] or 'Inconnu', value=x['c']) for x in qs]

    def scans_last_24_hours(self):
        last_24h = timezone.now() - datetime.timedelta(hours=24)
        return self.queryset.filter(capture_le__gte=last_24h).count()

    def scans_this_week(self):
        now = timezone.now()
        start_week = now - datetime.timedelta(days=now.weekday())
        return self.queryset.filter(capture_le__gte=start_week).count()

    def scans_this_month(self):
        now = timezone.now()
        return self.queryset.filter(capture_le__month=now.month, capture_le__year=now.year).count()

    def average_scans_per_day(self):
        total = self.queryset.count()
        days = self.queryset.annotate(day=TruncDay('capture_le')).values('day').distinct().count()
        if days == 0: return 0.0
        return float(total / days)

    def location_coverage(self):
        return self.queryset.values('lieu').distinct().count()

    def article_coverage(self):
        scanned = self.queryset.filter(article__isnull=False).values('article').distinct().count()
        total = Article.objects.count()
        if total == 0: return 0.0
        return float((scanned / total) * 100)

    def value_scanned_percentage(self):
        scanned_ids = self.queryset.filter(article__isnull=False).values_list('article', flat=True).distinct()
        scanned_val = Article.objects.filter(id__in=scanned_ids).aggregate(s=Sum('totalfiscalprice'))['s'] or 0
        total_val = Article.objects.aggregate(s=Sum('totalfiscalprice'))['s'] or 0
        try:
            if hasattr(total_val, 'is_nan') and total_val.is_nan(): return 0.0
            if total_val == 0: return 0.0
            if hasattr(scanned_val, 'is_nan') and scanned_val.is_nan(): scanned_val = 0
            return float((float(scanned_val) / float(total_val)) * 100)
        except Exception:
            return 0.0

    def scans_by_acquisition_year(self):
        qs = self.queryset.filter(article__isnull=False, article__acquiringdate__isnull=False).annotate(year=ExtractYear('article__acquiringdate')).values('year').annotate(c=Count('id')).order_by('year')
        return [StatItem(label=str(x['year']), value=x['c']) for x in qs]

    def scans_geo_distribution(self):
        qs = self.queryset.exclude(latitude__isnull=True).exclude(latitude='').values('latitude', 'longitude').annotate(c=Count('id'))
        return [StatItem(label=str(x['latitude']), extra=str(x['longitude']), value=x['c']) for x in qs]

    def scans_with_image(self):
         return self.queryset.filter(Q(image__isnull=False) & ~Q(image='')).count()

    def scans_progression(self):
         qs = self.queryset.annotate(day=TruncDay('capture_le')).values('day').annotate(c=Count('id')).order_by('day')
         result = []
         total = 0
         for x in qs:
             total += x['c']
             result.append(StatTimeSeries(date=x['day'].isoformat() if x['day'] else None, value=total))
         return result

    def scans_with_multiple_images(self):
        return self.queryset.filter(Q(image2__isnull=False) | Q(image3__isnull=False)).count()

    def scans_by_day_of_week(self):
        qs = self.queryset.annotate(day=ExtractWeekDay('capture_le')).values('day').annotate(c=Count('id')).order_by('day')
        days = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
        return [StatItem(label=days[x['day'] % 7], value=x['c']) for x in qs]

    def scans_by_month_of_year(self):
        qs = self.queryset.annotate(month=ExtractMonth('capture_le')).values('month').annotate(c=Count('id')).order_by('month')
        months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
        return [StatItem(label=months[x['month']-1], value=x['c']) for x in qs if 0 < x['month'] <= 12]

    def scans_with_custom_desc(self):
        return self.queryset.exclude(custom_desc__exact='').exclude(custom_desc__isnull=True).count()

    def scans_with_comment(self):
        return self.queryset.exclude(commentaire__exact='').exclude(commentaire__isnull=True).count()

    def scans_by_financing_method(self):
        qs = self.queryset.filter(article__isnull=False).values('article__financingmethod').annotate(c=Count('id')).order_by('-c')
        finance_map = {'1': 'Fonds Propres', '2': 'Crédit Bail', '3': 'Subvention', '4': 'Don', '5': 'Autre'}
        return [StatItem(label=finance_map.get(str(x['article__financingmethod']), x['article__financingmethod'] or 'Non spécifié'), value=x['c']) for x in qs]

    def scans_by_article_type(self):
        qs = self.queryset.filter(article__isnull=False).values('article__type').annotate(c=Count('id'))
        return [StatItem(label=str(x['article__type']), value=x['c']) for x in qs]

    def total_scanned_value(self):
        scanned_ids = self.queryset.filter(article__isnull=False).values_list('article', flat=True).distinct()
        val = Article.objects.filter(id__in=scanned_ids).aggregate(s=Sum('totalfiscalprice'))['s']
        return float(val) if val else 0.0

    def average_scanned_value(self):
        scanned_ids = self.queryset.filter(article__isnull=False).values_list('article', flat=True).distinct()
        val = Article.objects.filter(id__in=scanned_ids).aggregate(a=Avg('totalfiscalprice'))['a']
        return float(val) if val else 0.0

    def scans_on_weekend(self):
        return self.queryset.annotate(day=ExtractWeekDay('capture_le')).filter(day__in=[1, 7]).count()

    def scans_off_hours(self):
        return self.queryset.annotate(h=ExtractHour('capture_le')).filter(Q(h__lt=8) | Q(h__gt=18)).count()

    def scans_with_gps(self):
        return self.queryset.exclude(latitude__isnull=True).exclude(latitude__exact='').count()

    def scans_without_gps(self):
        return self.queryset.filter(Q(latitude__isnull=True) | Q(latitude__exact='')).count()

    def scans_edited(self):
        return self.queryset.filter(modifie_le__gt=F('cree_le') + datetime.timedelta(seconds=5)).count()

    def scans_duplicate_codes(self):
        qs = self.queryset.values('code_article').annotate(c=Count('id')).filter(c__gt=1)
        return qs.count()

    def scans_with_duplicate_articles(self):
        qs = self.queryset.filter(article__isnull=False).values('article').annotate(c=Count('id')).filter(c__gt=1)
        return qs.count()

    def avg_scans_per_active_user(self):
        total_scans = self.queryset.count()
        active_users = self.queryset.values('groupe__utilisateur').distinct().count()
        if active_users == 0: return 0.0
        return float(total_scans / active_users)

    def scans_last_hour(self):
        last_hour = timezone.now() - datetime.timedelta(hours=1)
        return self.queryset.filter(capture_le__gte=last_hour).count()

    def articles_age_distribution(self):
        current_year = timezone.now().year
        scanned_ids = self.queryset.filter(article__isnull=False).values_list('article', flat=True).distinct()
        qs = Article.objects.filter(id__in=scanned_ids, acquiringdate__isnull=False).annotate(acq_year=ExtractYear('acquiringdate'))
        bins = {'0-5 ans': 0, '5-10 ans': 0, '10-15 ans': 0, '15+ ans': 0}
        for item in qs.values('acq_year'):
            age = current_year - item['acq_year']
            if age < 5: bins['0-5 ans'] += 1
            elif age < 10: bins['5-10 ans'] += 1
            elif age < 15: bins['10-15 ans'] += 1
            else: bins['15+ ans'] += 1
        return [StatItem(label=k, value=v) for k, v in bins.items()]

    def unique_scanned_articles_count(self):
        return self.queryset.filter(article__isnull=False).values('article').distinct().count()

    def most_scanned_family(self):
        qs = self.queryset.filter(article__isnull=False).values('article__family__familyname').annotate(c=Count('id')).order_by('-c')
        if not qs: return None
        top = qs[0]
        return StatItem(label=top['article__family__familyname'] or 'Sans famille', value=top['c'])

    def most_scanned_location(self):
        qs = self.queryset.values('lieu__locationname').annotate(c=Count('id')).order_by('-c')
        if not qs: return None
        top = qs[0]
        return StatItem(label=top['lieu__locationname'] or 'Inconnu', value=top['c'])

class InventoryStats(graphene.ObjectType):
    total_scans = graphene.Int()
    scans_by_etat = graphene.List(StatItem)
    scans_by_location = graphene.List(StatItem)
    scans_by_group = graphene.List(StatItem)
    scans_by_campaign = graphene.List(StatItem)
    scans_by_date = graphene.List(StatTimeSeries)
    scans_by_source = graphene.List(StatItem)
    scans_with_observation = graphene.Int()
    scans_with_serial_number = graphene.Int()
    scans_by_article_family = graphene.List(StatItem)
    scans_by_article_supplier = graphene.List(StatItem)
    total_value_by_etat = graphene.List(StatItem)
    total_value_by_location = graphene.List(StatItem)
    scans_without_article_link = graphene.Int()
    scans_by_hour = graphene.List(StatItem)
    scans_by_department = graphene.List(StatItem)
    top_scanned_articles = graphene.List(TopArticleItem)
    scans_by_user = graphene.List(StatItem)
    scans_by_device = graphene.List(StatItem)
    scans_last_24_hours = graphene.Int()
    scans_this_week = graphene.Int()
    scans_this_month = graphene.Int()
    average_scans_per_day = graphene.Float()
    location_coverage = graphene.Int()
    article_coverage = graphene.Float()
    value_scanned_percentage = graphene.Float()
    scans_by_acquisition_year = graphene.List(StatItem)
    scans_geo_distribution = graphene.List(StatItem)
    scans_with_image = graphene.Int()
    scans_progression = graphene.List(StatTimeSeries)
    # New queries
    scans_with_multiple_images = graphene.Int()
    scans_by_day_of_week = graphene.List(StatItem)
    scans_by_month_of_year = graphene.List(StatItem)
    scans_with_custom_desc = graphene.Int()
    scans_with_comment = graphene.Int()
    scans_by_financing_method = graphene.List(StatItem)
    scans_by_article_type = graphene.List(StatItem)
    total_scanned_value = graphene.Float()
    average_scanned_value = graphene.Float()
    scans_on_weekend = graphene.Int()
    scans_off_hours = graphene.Int()
    scans_with_gps = graphene.Int()
    scans_without_gps = graphene.Int()
    scans_edited = graphene.Int()
    scans_duplicate_codes = graphene.Int()
    scans_with_duplicate_articles = graphene.Int()
    avg_scans_per_active_user = graphene.Float()
    scans_last_hour = graphene.Int()
    articles_age_distribution = graphene.List(StatItem)
    unique_scanned_articles_count = graphene.Int()
    most_scanned_family = graphene.Field(StatItem)
    most_scanned_location = graphene.Field(StatItem)

    def resolve_total_scans(root, info): return root.total_scans()
    def resolve_scans_by_etat(root, info): return root.scans_by_etat()
    def resolve_scans_by_location(root, info): return root.scans_by_location()
    def resolve_scans_by_group(root, info): return root.scans_by_group()
    def resolve_scans_by_campaign(root, info): return root.scans_by_campaign()
    def resolve_scans_by_date(root, info): return root.scans_by_date()
    def resolve_scans_by_source(root, info): return root.scans_by_source()
    def resolve_scans_with_observation(root, info): return root.scans_with_observation()
    def resolve_scans_with_serial_number(root, info): return root.scans_with_serial_number()
    def resolve_scans_by_article_family(root, info): return root.scans_by_article_family()
    def resolve_scans_by_article_supplier(root, info): return root.scans_by_article_supplier()
    def resolve_total_value_by_etat(root, info): return root.total_value_by_etat()
    def resolve_total_value_by_location(root, info): return root.total_value_by_location()
    def resolve_scans_without_article_link(root, info): return root.scans_without_article_link()
    def resolve_scans_by_hour(root, info): return root.scans_by_hour()
    def resolve_scans_by_department(root, info): return root.scans_by_department()
    def resolve_top_scanned_articles(root, info): return root.top_scanned_articles()
    def resolve_scans_by_user(root, info): return root.scans_by_user()
    def resolve_scans_by_device(root, info): return root.scans_by_device()
    def resolve_scans_last_24_hours(root, info): return root.scans_last_24_hours()
    def resolve_scans_this_week(root, info): return root.scans_this_week()
    def resolve_scans_this_month(root, info): return root.scans_this_month()
    def resolve_average_scans_per_day(root, info): return root.average_scans_per_day()
    def resolve_location_coverage(root, info): return root.location_coverage()
    def resolve_article_coverage(root, info): return root.article_coverage()
    def resolve_value_scanned_percentage(root, info): return root.value_scanned_percentage()
    def resolve_scans_by_acquisition_year(root, info): return root.scans_by_acquisition_year()
    def resolve_scans_geo_distribution(root, info): return root.scans_geo_distribution()
    def resolve_scans_with_image(root, info): return root.scans_with_image()
    def resolve_scans_progression(root, info): return root.scans_progression()
    def resolve_scans_with_multiple_images(root, info): return root.scans_with_multiple_images()
    def resolve_scans_by_day_of_week(root, info): return root.scans_by_day_of_week()
    def resolve_scans_by_month_of_year(root, info): return root.scans_by_month_of_year()
    def resolve_scans_with_custom_desc(root, info): return root.scans_with_custom_desc()
    def resolve_scans_with_comment(root, info): return root.scans_with_comment()
    def resolve_scans_by_financing_method(root, info): return root.scans_by_financing_method()
    def resolve_scans_by_article_type(root, info): return root.scans_by_article_type()
    def resolve_total_scanned_value(root, info): return root.total_scanned_value()
    def resolve_average_scanned_value(root, info): return root.average_scanned_value()
    def resolve_scans_on_weekend(root, info): return root.scans_on_weekend()
    def resolve_scans_off_hours(root, info): return root.scans_off_hours()
    def resolve_scans_with_gps(root, info): return root.scans_with_gps()
    def resolve_scans_without_gps(root, info): return root.scans_without_gps()
    def resolve_scans_edited(root, info): return root.scans_edited()
    def resolve_scans_duplicate_codes(root, info): return root.scans_duplicate_codes()
    def resolve_scans_with_duplicate_articles(root, info): return root.scans_with_duplicate_articles()
    def resolve_avg_scans_per_active_user(root, info): return root.avg_scans_per_active_user()
    def resolve_scans_last_hour(root, info): return root.scans_last_hour()
    def resolve_articles_age_distribution(root, info): return root.articles_age_distribution()
    def resolve_unique_scanned_articles_count(root, info): return root.unique_scanned_articles_count()
    def resolve_most_scanned_family(root, info): return root.most_scanned_family()
    def resolve_most_scanned_location(root, info): return root.most_scanned_location()

class InventoryReconciliationStatus(graphene.ObjectType):
    valid_codes = graphene.List(graphene.String)
    conflict_codes = graphene.List(graphene.String)
    total_valid = graphene.Int()
    total_conflicts = graphene.Int()

    def resolve_total_valid(root, info):
        return len(root.valid_codes)

    def resolve_total_conflicts(root, info):
        return len(root.conflict_codes)


class InventoryCustomQueries(graphene.ObjectType):
    inventory_stats = graphene.Field(InventoryStats, group_id=graphene.ID(required=False))
    inventory_reconciliation_status = graphene.Field(
        InventoryReconciliationStatus, campagne_id=graphene.ID(required=True)
    )
    inventory_conflicts = graphene.List(
        graphene.String, campagne_id=graphene.ID(required=True)
    )

    def resolve_inventory_stats(self, info, group_id=None):
        return StatsContext(group_id)

    def resolve_inventory_reconciliation_status(self, info, campagne_id):
        try:
            campagne = CampagneInventaire.objects.get(pk=campagne_id)
            service = InventoryReconciliationService(campagne)
            data = service.get_scanned_items_status()
            return InventoryReconciliationStatus(
                valid_codes=list(data["valid_codes"]),
                conflict_codes=list(data["conflict_codes"]),
            )
        except CampagneInventaire.DoesNotExist:
            return None

    def resolve_inventory_conflicts(self, info, campagne_id):
        try:
            campagne = CampagneInventaire.objects.get(pk=campagne_id)
            service = InventoryReconciliationService(campagne)
            return service.get_conflicts_for_review()
        except CampagneInventaire.DoesNotExist:
            return []


############################
# OLD: EnregistrementInventaire sync (kept for backward compatibility)
############################


class InventoryScanSyncInput(graphene.InputObjectType):
    """Input payload for syncing mobile scan records."""

    local_id = graphene.String(required=True)
    campagne = graphene.ID(required=True)
    groupe = graphene.ID(required=True)
    lieu = graphene.ID(required=True)
    code_article = graphene.String(required=True)
    capture_le = graphene.DateTime(required=False)
    source_scan = graphene.String(required=False)
    latitude = graphene.String(required=False)
    longitude = graphene.String(required=False)
    donnees_capture = graphene.JSONString(required=False)
    observation = graphene.String(required=False)
    serial_number = graphene.String(required=False)
    etat = graphene.String(required=False)
    article = graphene.ID(required=False)
    commentaire = graphene.String(required=False)
    custom_desc = graphene.String(required=False)


class InventoryScanSyncResult(graphene.ObjectType):
    """Result payload for a single mobile scan sync."""

    local_id = graphene.String()
    remote_id = graphene.ID()
    ok = graphene.Boolean()
    errors = graphene.List(graphene.String)


class SyncInventoryScans(graphene.Mutation):
    """Create inventory scan records from mobile offline data."""

    class Input:
        input = graphene.List(InventoryScanSyncInput, required=True)

    ok = graphene.Boolean()
    message = graphene.String()
    results = graphene.List(InventoryScanSyncResult)

    @staticmethod
    def _normalize_errors(errors):
        messages = []
        for field, details in errors.items():
            if isinstance(details, (list, tuple)):
                for detail in details:
                    messages.append(f"{field}: {detail}")
            else:
                messages.append(f"{field}: {details}")
        return messages

    @staticmethod
    def _parse_capture_payload(payload):
        if not payload:
            return None
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def _build_image_file(payload):
        if not isinstance(payload, dict):
            return None

        data = payload.get("data_base64") or payload.get("data")
        if not data:
            return None

        if isinstance(data, str) and "," in data:
            data = data.split(",", 1)[1]

        filename = payload.get("filename") or f"scan-{uuid.uuid4().hex}.jpg"
        try:
            decoded = base64.b64decode(data)
        except (binascii.Error, TypeError, ValueError):
            return None

        return ContentFile(decoded, name=filename)

    @staticmethod
    def mutate(root, info, input):
        if not input:
            return SyncInventoryScans(
                ok=True, message="Aucun scan a synchroniser.", results=[]
            )

        # Optimization: Pre-fetch articles to avoid N+1 queries
        codes = set()
        for item in input:
            # Safely access input attributes
            c = getattr(item, "code_article", None)
            if c:
                codes.add(c.strip().upper())

        prefetched_articles = {}
        if codes:
            from django.db.models.functions import Upper
            from immo.models import Article

            # Use Upper to match behavior of 'iexact' lookup in a bulk query
            qs = Article.objects.annotate(ucode=Upper("code")).filter(ucode__in=codes).order_by("pk")
            for art in qs:
                # Store first match (lowest PK)
                if art.ucode not in prefetched_articles:
                    prefetched_articles[art.ucode] = art

        results = []
        success_count = 0

        # Optimization: Single transaction for potentially large batch
        with transaction.atomic():
            for item in input:
                local_id = None
                sid = transaction.savepoint()
                try:
                    payload = dict(item)
                    local_id = payload.pop("local_id", None)

                    cleaned = {
                        key: value for key, value in payload.items() if value is not None
                    }

                    # Optimization: Inject pre-fetched article to skip N+1 DB lookup
                    c_art = cleaned.get("code_article")
                    if c_art and not cleaned.get("article"):
                        norm_code = c_art.strip().upper()
                        if norm_code in prefetched_articles:
                            cleaned["article"] = prefetched_articles[norm_code].pk

                    capture_payload = SyncInventoryScans._parse_capture_payload(
                        cleaned.get("donnees_capture")
                    )
                    if isinstance(capture_payload, dict):
                        cleaned["donnees_capture"] = capture_payload
                        image_payloads = []
                        if isinstance(capture_payload.get("images"), list):
                            image_payloads.extend(
                                [item for item in capture_payload.get("images") if item]
                            )
                        else:
                            image_payloads.extend(
                                [
                                    capture_payload.get("image"),
                                    capture_payload.get("image2"),
                                    capture_payload.get("image3"),
                                ]
                            )

                        for index, image_payload in enumerate(image_payloads[:3], start=1):
                            image_file = SyncInventoryScans._build_image_file(
                                image_payload
                            )
                            if image_file is None:
                                continue
                            field_name = "image" if index == 1 else f"image{index}"
                            cleaned[field_name] = image_file

                    serializer = EnregistrementInventaireSerializer(data=cleaned)
                    if serializer.is_valid():
                        # Save without creating a NEW atomic block, relying on the outer one
                        instance = serializer.save()
                        
                        # Release savepoint (success)
                        transaction.savepoint_commit(sid)

                        results.append(
                            InventoryScanSyncResult(
                                local_id=local_id,
                                remote_id=instance.pk,
                                ok=True,
                                errors=[],
                            )
                        )
                        success_count += 1
                        continue

                    # Validation failed - rollback this item
                    transaction.savepoint_rollback(sid)
                    results.append(
                        InventoryScanSyncResult(
                            local_id=local_id,
                            remote_id=None,
                            ok=False,
                            errors=SyncInventoryScans._normalize_errors(serializer.errors),
                        )
                    )
                except Exception as exc:
                    # Unexpected error - rollback this item
                    transaction.savepoint_rollback(sid)
                    results.append(
                        InventoryScanSyncResult(
                            local_id=local_id,
                            remote_id=None,
                            ok=False,
                            errors=[f"{type(exc).__name__}: {exc}"],
                        )
                    )

        message = (
            f"{success_count}/{len(input)} scans synchronises."
            if len(input) > 0
            else "Aucun scan a synchroniser."
        )
        return SyncInventoryScans(
            ok=success_count == len(input),
            message=message,
            results=results,
        )


class GenerateRapprochement(graphene.Mutation):
    """Génère le rapprochement d'inventaire pour une campagne donnée."""

    class Arguments:
        campagne_id = graphene.ID(required=True)

    ok = graphene.Boolean()
    message = graphene.String()
    rapprochement_id = graphene.ID()

    @staticmethod
    def mutate(root, info, campagne_id):
        try:
            campagne = CampagneInventaire.objects.get(pk=campagne_id)
            service = InventoryReconciliationService(campagne)
            rapprochement = service.generate_rapprochement()
            return GenerateRapprochement(
                ok=True,
                message="Rapprochement généré avec succès.",
                rapprochement_id=rapprochement.pk,
            )
        except CampagneInventaire.DoesNotExist:
            return GenerateRapprochement(ok=False, message="Campagne introuvable.")
        except Exception as e:
            return GenerateRapprochement(ok=False, message=str(e))


class GetInventoryConflicts(graphene.Mutation):
    """Retourne la liste des codes articles en conflit (nécessitant vérification Groupe C)."""

    class Arguments:
        campagne_id = graphene.ID(required=True)

    ok = graphene.Boolean()
    conflicts = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, campagne_id):
        try:
            campagne = CampagneInventaire.objects.get(pk=campagne_id)
            service = InventoryReconciliationService(campagne)
            conflicts = service.get_conflicts_for_review()
            return GetInventoryConflicts(ok=True, conflicts=conflicts)
        except CampagneInventaire.DoesNotExist:
            return GetInventoryConflicts(ok=False, conflicts=[])
        except Exception:
            return GetInventoryConflicts(ok=False, conflicts=[])


class InventoryCustomMutations(graphene.ObjectType):
    # Old mutation (kept for backward compatibility)
    sync_inventory_scans = SyncInventoryScans.Field()
    generate_rapprochement = GenerateRapprochement.Field()
    get_inventory_conflicts = GetInventoryConflicts.Field()
        