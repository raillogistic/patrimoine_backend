
import base64
import binascii
import json
import uuid

import graphene
from django.core.files.base import ContentFile
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from inventory.models import EnregistrementInventaire


class ImmoCustomQueries(graphene.ObjectType):
    pass


############################
# Inventory scan image-only sync
############################


class InventoryScanImageSyncInput(graphene.InputObjectType):
    """Input payload for syncing images to an existing inventory scan."""

    local_id = graphene.String(required=True)
    remote_id = graphene.ID(required=True)
    donnees_capture = graphene.JSONString(required=True)


class InventoryScanImageSyncResult(graphene.ObjectType):
    """Result payload for a single scan image sync."""

    local_id = graphene.String()
    remote_id = graphene.ID()
    ok = graphene.Boolean()
    errors = graphene.List(graphene.String)


class SyncInventoryScanImages(graphene.Mutation):
    """Attach images to existing inventory scan records."""

    class Input:
        input = graphene.List(InventoryScanImageSyncInput, required=True)

    ok = graphene.Boolean()
    message = graphene.String()
    results = graphene.List(InventoryScanImageSyncResult)

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
            return SyncInventoryScanImages(
                ok=True, message="Aucune image a synchroniser.", results=[]
            )

        results = []
        success_count = 0

        with transaction.atomic():
            for item in input:
                local_id = None
                sid = transaction.savepoint()
                try:
                    payload = dict(item)
                    local_id = payload.pop("local_id", None)
                    remote_id = payload.pop("remote_id", None)
                    capture_payload = SyncInventoryScanImages._parse_capture_payload(
                        payload.get("donnees_capture")
                    )

                    if not remote_id:
                        raise ValueError("remote_id requis pour la synchronisation.")

                    if not isinstance(capture_payload, dict):
                        raise ValueError("donnees_capture invalide ou manquant.")

                    try:
                        instance = EnregistrementInventaire.objects.get(pk=remote_id)
                    except ObjectDoesNotExist:
                        raise ValueError("Enregistrement introuvable.")

                    image_payloads = []
                    if isinstance(capture_payload.get("images"), list):
                        image_payloads.extend(
                            [img for img in capture_payload.get("images") if img]
                        )
                    else:
                        image_payloads.extend(
                            [
                                capture_payload.get("image"),
                                capture_payload.get("image2"),
                                capture_payload.get("image3"),
                            ]
                        )

                    update_fields = []
                    for index, image_payload in enumerate(image_payloads[:3], start=1):
                        image_file = SyncInventoryScanImages._build_image_file(
                            image_payload
                        )
                        if image_file is None:
                            continue
                        field_name = "image" if index == 1 else f"image{index}"
                        setattr(instance, field_name, image_file)
                        update_fields.append(field_name)

                    if not update_fields:
                        raise ValueError("Aucune image valide a synchroniser.")

                    instance.donnees_capture = capture_payload
                    update_fields.append("donnees_capture")
                    update_fields.append("modifie_le")
                    instance.save(update_fields=update_fields)

                    transaction.savepoint_commit(sid)
                    results.append(
                        InventoryScanImageSyncResult(
                            local_id=local_id,
                            remote_id=instance.pk,
                            ok=True,
                            errors=[],
                        )
                    )
                    success_count += 1
                except Exception as exc:
                    transaction.savepoint_rollback(sid)
                    results.append(
                        InventoryScanImageSyncResult(
                            local_id=local_id,
                            remote_id=None,
                            ok=False,
                            errors=[f"{type(exc).__name__}: {exc}"],
                        )
                    )

        message = (
            f"{success_count}/{len(input)} images synchronisees."
            if len(input) > 0
            else "Aucune image a synchroniser."
        )
        return SyncInventoryScanImages(
            ok=success_count == len(input),
            message=message,
            results=results,
        )


############################


class ImmoCustomMutations(graphene.ObjectType):
    sync_inventory_scan_images = SyncInventoryScanImages.Field()

