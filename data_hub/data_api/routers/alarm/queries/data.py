import os
import json
import time
import math
import django
import pytz
import logging
from django.db import connection
from django.db.models import Q
from django.db import models
from fastapi import status
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from datetime import time as dtime
from typing import Callable
from fastapi import Request
from fastapi import Response
from fastapi import APIRouter
from fastapi import HTTPException, Query, Body, Form
from fastapi.routing import APIRoute
from typing import Dict, List, Optional
from django.db.models import Prefetch
from pydantic import BaseModel, Field, create_model, ValidationError
from common_utils.timezone_utils.timeloc import (
    convert_to_local_time,
)
from common_utils.filters.utils import (
    map_value_range,
    map_value,
    map_entity_type_to_table_type,
)

logger = logging.getLogger(__name__)

django.setup()
from django.core.exceptions import ObjectDoesNotExist
from tenants.models import (
    Tenant,
    EntityType,
    PlantEntity,
    TenantStorageSettings,
)

from acceptance_control.models import (
    Alarm,
    AlarmTag,
    AlarmMedia,
    Media,
    Severity,
    FlagType,
    FlagTypeLocalization,
)

from metadata.models import (
    TableType,
    TenantTable,
    Language,
    TenantTableFilter,
    PlantEntityLocalization,
)


def filter_mapping(key, value, tenant):
    try:
        if value is None:
            return None

        if not len(value):
            return None

        if value == "all":
            return None

        if key == "severity_level":
            return (
                "severity__level__gte",
                value,
            )  # Severity.objects.filter(level=value).first())
        if key == "location":
            return (
                "entity",
                PlantEntity.objects.get(entity_uid=value, entity_type__tenant=tenant),
            )
        if key == "flag_type":
            return ("flag_type", FlagType.objects.get(name=value))
        if key == "value":
            return map_value_range(value)
        if key == "entity_type":
            return ("entity__entity_type", EntityType.objects.get(entity_type=value))
    except Exception as err:
        raise ValueError(f"Failed to map filter value {value} filter {key}: {err}")


class TimedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            before = time.time()
            response: Response = await original_route_handler(request)
            duration = time.time() - before
            response.headers["X-Response-Time"] = str(duration)
            print(f"route duration: {duration}")
            print(f"route response: {response}")
            print(f"route response headers: {response.headers}")
            return response

        return custom_route_handler


router = APIRouter(
    route_class=TimedRoute,
)


def create_filter_model(fields: Dict[str, Optional[str]]):
    """
    This function creates a dynamic Pydantic model based on the fields provided,
    without setting default values.
    """
    return create_model(
        "DynamicFilterModel", **{k: (Optional[str], v) for k, v in fields.items()}
    )


description = """
    URL Path: /alarm

    TO DO

"""


@router.api_route(
    "/alarm",
    methods=["GET"],
    tags=["Alarm"],
    description=description,
)
def get_alarm_data(
    response: Response,
    tenant_domain: str,
    user_filters: Optional[str] = Query(None),
    from_date: datetime = None,
    to_date: datetime = None,
    items_per_page: int = 15,
    page: int = 1,
    language: str = None,
    entity_type: str = f"gate",
):
    results = {}
    try:

        filters_dict = {}
        if user_filters:
            try:
                filters_dict = json.loads(user_filters)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="Invalid JSON format for user_filters"
                )

        if not Tenant.objects.filter(domain=tenant_domain).exists():
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Tenant {tenant_domain} not found",
                    "detail": f"Tenant {Tenant} not found ! Existing options: {[tenant.domain for tenant in Tenant.objects.all()]}",
                }
            }

            response.status_code = status.HTTP_404_NOT_FOUND
            return results

        alarm_type = map_entity_type_to_table_type(entity_type)
        if not TableType.objects.filter(name=alarm_type).exists():
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Table Type alarm not found",
                    "detail": f"Table Type alarm not found ! Existing options: {[table_type.name for table_type in TableType.objects.all()]}",
                }
            }

            response.status_code = status.HTTP_404_NOT_FOUND
            return results

        # language = Language.objects.get(code=language)
        table_type = TableType.objects.get(name=alarm_type)
        tenant = Tenant.objects.get(domain=tenant_domain)
        timezone_str = tenant.timezone
        entity_type = EntityType.objects.filter(
            entity_type=entity_type, tenant=tenant
        ).first()

        msg = f"using given language {language}"
        if not language:
            lang_code = tenant.default_language
            if lang_code:
                language = lang_code
                msg = f"using default language: {language}"
            else:
                language = "de"
                msg = f"using german language"
        if not Language.objects.filter(code=language).exists():
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Given Language {language} not supported",
                    "detail": f"Given Language {language} not supported! Supported Language: {[lang.name for lang in Language.objects.all()]}",
                }
            }

            response.status_code = status.HTTP_404_NOT_FOUND
            return results

        language = Language.objects.get(code=language)
        AzAccoutKey = TenantStorageSettings.objects.get(tenant=tenant).account_key

        if not TenantTable.objects.filter(tenant=tenant, table_type=table_type):
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Table Type alarm not defined for tenant {tenant_domain}",
                    "detail": f"Table Type alarm not found for {tenant_domain}!"
                    f"Existing options: {[tenant_table.table_type.name for tenant_table in TenantTable.objects.filter(tenant=tenant)]}",
                }
            }

            response.status_code = status.HTTP_404_NOT_FOUND
            return results

        today = datetime.today()
        if from_date is None:
            from_date = datetime(today.year, today.month, today.day)

        if to_date is None:
            to_date = from_date

        local_tz = pytz.timezone(timezone_str)
        from_date = local_tz.localize(datetime.combine(from_date, dtime.min))
        to_date = local_tz.localize(datetime.combine(to_date, dtime.max))

        if page < 1:
            page = 1

        if items_per_page <= 0:
            results["error"] = {
                "status_code": 400,
                "status_description": f"Bad Request, items_per_pages should not be 0",
                "detail": "division by zero.",
            }

            response.status_code = status.HTTP_400_BAD_REQUEST
            return results

        tenant_table = TenantTable.objects.get(tenant=tenant, table_type=table_type)

        tenant_table_filter = TenantTableFilter.objects.filter(
            tenant_table=tenant_table, is_active=True
        )

        filter_fields = {
            fil.table_filter.filter_name: fil.default for fil in tenant_table_filter
        }

        DynamicFilterModel = create_filter_model(filter_fields)
        try:
            validated_filters = DynamicFilterModel(**filters_dict)
        except ValidationError as e:
            results["error"] = {"status_code": 422, "detail": f"{e.errors()}"}

            response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            return results

        lookup_filters = Q()
        lookup_filters &= Q(tenant=tenant)
        lookup_filters &= Q(exclude_from_dashboard=False)
        lookup_filters &= Q(created_at__range=(from_date, to_date))

        if entity_type:
            lookup_filters &= Q(entity__entity_type=entity_type)

        for key, value in validated_filters:
            filter_map = filter_mapping(key, value, tenant)
            if filter_map:
                if isinstance(filter_map, list):
                    for field, val in filter_map:
                        lookup_filters &= Q(**{field: val})
                else:
                    field, val = filter_map
                    lookup_filters &= Q(**{field: val})

        alarms_with_images = (
            Alarm.objects.filter(lookup_filters)
            .filter(
                models.Exists(
                    AlarmMedia.objects.filter(
                        alarm=models.OuterRef("pk"), media__media_type=Media.IMAGE
                    )
                )
            )
            .select_related(
                "flag_type", "severity", "entity", "entity__entity_type", "tenant"
            )
            .prefetch_related(
                Prefetch("alarm_tags", queryset=AlarmTag.objects.select_related("tag")),
                Prefetch(
                    "alarmmedia_set",
                    queryset=AlarmMedia.objects.select_related("media")
                    .filter(media__media_type=Media.IMAGE)
                    .order_by("id")[:1],
                    to_attr="first_image_media",
                ),
            )
            .distinct()
            .order_by("-created_at")
        )

        total_count = alarms_with_images.count()

        # Apply pagination
        start = (page - 1) * items_per_page
        end = start + items_per_page
        paginated_alarms = alarms_with_images[start:end]

        rows = []
        for alarm in paginated_alarms:

            flag_type = alarm.flag_type
            plant_entity = PlantEntity.objects.get(
                entity_uid=alarm.entity.entity_uid, entity_type__tenant=tenant
            )

            if not PlantEntityLocalization.objects.filter(
                plant_entity=plant_entity,
                language=language,
            ).exists():
                results["error"] = {
                    "status_code": "non-matching-query",
                    "status_description": f"localization {language.name} not found for {plant_entity.entity_uid}",
                    "detail": f"localization {language.name} not found for {plant_entity.entity_uid}",
                }

                response.status_code = status.HTTP_404_NOT_FOUND
                return results

            if not FlagTypeLocalization.objects.filter(
                flag_type=flag_type, language=language
            ).exists():
                results["error"] = {
                    "status_code": "non-matching-query",
                    "status_description": f"localization {language.name} not found for {flag_type.name}",
                    "detail": f"localization {language.name} not found for {flag_type.name}",
                }

                response.status_code = status.HTTP_404_NOT_FOUND
                return results

            plant_entity_localization = PlantEntityLocalization.objects.get(
                plant_entity=PlantEntity.objects.get(
                    entity_uid=alarm.entity.entity_uid, entity_type__tenant=tenant
                ),
                language=language,
            )

            flag_type_localization = FlagTypeLocalization.objects.get(
                flag_type=flag_type,
                language=language,
            )

            # media = AlarmMedia.objects.filter(
            #     alarm=alarm, media__media_type="image"
            # ).first()

            if alarm.first_image_media:  # check if not empty
                media = alarm.first_image_media[0].media  # AlarmMedia → media FK

            logger.info(f"================= {media} {alarm.event_uid}")

            row = {
                "id": alarm.id,
                "event_uid": alarm.event_uid,
                "event_date": convert_to_local_time(alarm.created_at, timezone_str=timezone_str).strftime("%Y-%m-%d"),
                "start_time": convert_to_local_time(alarm.timestamp, timezone_str=timezone_str).strftime("%H:%M:%S"),
                "end_time": convert_to_local_time(alarm.timestamp, timezone_str=timezone_str).strftime("%H:%M:%S"),
                "timestamp": convert_to_local_time(alarm.created_at, timezone_str=timezone_str).strftime("%H:%M:%S"),
                "location": plant_entity_localization.title,
                "event_name": flag_type_localization.title,
                "media_type": media.media_type,
                "severity_level": alarm.severity.unicode_char,
                "value": map_value(alarm.value, flag_type=flag_type.name),
                "preview": f"{media.media_url}?{AzAccoutKey}",
                "ack_status": "✅" if alarm.ack_status else "⬛",
                "severity_level_numerical": int(alarm.severity.level),
                "feedback_provided": "✅" if alarm.feedback_provided else "⬛",
                "tags": [alarm_tag.tag.name for alarm_tag in alarm.alarm_tags.all()],
            }

            rows.append(row)

        total_record = total_count

        results["data"] = {
            "language": language.name,
            "tenant": tenant.tenant_name,
            "type": "collection",
            "total_record": total_record,
            "user_filters": lookup_filters.children,
            "validated_filters": validated_filters,
            "pages": math.ceil(total_record / items_per_page),
            "items": rows,
        }
        results["status_code"] = "ok"
        results["detail"] = "data retrieved successfully"
        results["status_description"] = "OK"

    except ObjectDoesNotExist as e:
        results["error"] = {
            "status_code": "non-matching-query",
            "status_description": f"Matching query was not found",
            "detail": f"matching query does not exist. {e}",
        }

        response.status_code = status.HTTP_404_NOT_FOUND

    except HTTPException as e:
        results["error"] = {
            "status_code": f"{e.status_code}",
            "status_description": f"{e.detail}",
            "detail": f"{e.detail}",
        }

        response.status_code = e.status_code

    except Exception as e:
        results["error"] = {
            "status_code": "server-error",
            "status_description": "Internal Server Error",
            "detail": str(e),
        }

        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return results
