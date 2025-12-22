
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


class InventoryScanSyncInput(graphene.InputObjectType):
    """Input payload for syncing mobile scan records."""

    local_id = graphene.String(required=True)
    campagne = graphene.ID(required=True)
    groupe = graphene.ID(required=True)
    lieu = graphene.ID(required=True)
    code_article = graphene.String(required=True)
    capture_le = graphene.DateTime(required=False)
    source_scan = graphene.String(required=False)
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

    def mutate(self, info, input):
        if not input:
            return SyncInventoryScans(
                ok=True, message="Aucun scan a synchroniser.", results=[]
            )

        results = []
        success_count = 0

        for item in input:
            payload = dict(item)
            local_id = payload.pop("local_id", None)

            cleaned = {key: value for key, value in payload.items() if value is not None}
            capture_payload = self._parse_capture_payload(
                cleaned.get("donnees_capture")
            )
            if capture_payload is not None:
                cleaned["donnees_capture"] = capture_payload
                image_payload = capture_payload.get("image")
                image_file = self._build_image_file(image_payload)
                if image_file is not None:
                    cleaned["image"] = image_file

            serializer = EnregistrementInventaireSerializer(data=cleaned)
            if serializer.is_valid():
                with transaction.atomic():
                    instance = serializer.save()
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

            results.append(
                InventoryScanSyncResult(
                    local_id=local_id,
                    remote_id=None,
                    ok=False,
                    errors=self._normalize_errors(serializer.errors),
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
    sync_inventory_scans = SyncInventoryScans.Field()

