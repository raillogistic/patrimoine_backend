
import base64
import binascii
import json
import uuid

import graphene
from django.core.files.base import ContentFile
from django.db import transaction

from libs.graphql.schema.serializers import EnregistrementInventaireSerializer


class InventoryCustomQueries(graphene.ObjectType):
    pass


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


class InventoryCustomMutations(graphene.ObjectType):
    # Old mutation (kept for backward compatibility)
    sync_inventory_scans = SyncInventoryScans.Field()

