import django
django.setup()
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from datetime import datetime, timezone
from acceptance_control.models import VideoArchive, VideoArchiveMedia
from tenants.models import SensorBox, Camera, Tenant, PlantEntity
from acceptance_control.models import Media

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='video_archive:execute')
def execute(self, payload, **kwargs):
    """
    Celery task to process video archive entries, ensuring data integrity and optimized queries.
    """

    try:
        payload_dict = dict(payload)
        tenant_domain = payload_dict.get("tenant_domain")
        location = payload_dict.get("location")
        sensor_box_location = payload_dict.get("sensor_box_location")
        camera_id = payload_dict.get("camera_id")
        video_id = payload_dict.get("video_id")
        media_id = payload_dict.get("media_id")
        media_name = payload_dict.get("media_name")
        media_url = payload_dict.get("media_url")
        media_type = payload_dict.get("media_type")
        start_time = payload_dict.get("start_time", None)
        end_time = payload_dict.get("end_time", None)

        if not tenant_domain or not location or not camera_id or not video_id:
            raise ValueError("Missing required payload fields.")

        try:
            tenant = Tenant.objects.get(domain=tenant_domain)
        except Tenant.DoesNotExist:
            raise ObjectDoesNotExist(f"❌ Tenant {tenant_domain} does not exist.")

        try:
            entity = PlantEntity.objects.select_related("entity_type").get(
                entity_uid=location, entity_type__tenant=tenant
            )
        except PlantEntity.DoesNotExist:
            raise ObjectDoesNotExist(f"❌ Entity {location} for {tenant.domain} does not exist.")

        sensor_box = SensorBox.objects.filter(
            plant_entity=entity, sensor_box_location=sensor_box_location
        ).first()

        if not sensor_box:
            raise ObjectDoesNotExist(f"❌ SensorBox {sensor_box_location} for {entity} does not exist.")

        try:
            camera = Camera.objects.get(camera_id=camera_id, sensor_box=sensor_box)
        except Camera.DoesNotExist:
            raise ObjectDoesNotExist(f"❌ Camera {camera_id} for {entity} does not exist.")

        video_archive, created = VideoArchive.objects.get_or_create(
            video_id=video_id,
            defaults={
                "tenant": tenant,
                "entity": entity,
                "camera": camera,
                "start_time": start_time.replace(tzinfo=timezone.utc) if start_time else None,
                "end_time": end_time.replace(tzinfo=timezone.utc) if end_time else None,
            },
        )

        media, media_created = Media.objects.get_or_create(
            media_id=media_id,
            defaults={
                "media_name": media_name,
                "media_url": media_url,
                "media_type": media_type,
                "sensor_box": sensor_box,
            },
        )

        _, link_created = VideoArchiveMedia.objects.get_or_create(
            video_archive=video_archive,
            media=media
        )

        return {
            "action": "done",
            "time": datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
            "result": "success",
            "video_archive_created": created,
            "media_created": media_created,
            "link_created": link_created,
        }

    except (Tenant.DoesNotExist, PlantEntity.DoesNotExist, Camera.DoesNotExist, ObjectDoesNotExist) as err:
        raise ValueError(f"❌ Database Integrity Error: {err}")

    except IntegrityError as err:
        raise ValueError(f"❌ Integrity Error: {err}")

    except Exception as err:
        raise ValueError(f"❌ Unexpected Error: {err}")
