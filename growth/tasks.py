"""
Celery 排程任務：每週日 20:00 產生每週回顧。
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_weekly_review(self):
    """
    對每位本週有活動的使用者，彙整誇誇數、任務完成數，
    建立 WeeklyReview 記錄（供前端成長視覺化用）。
    """
    from django.contrib.auth import get_user_model
    from growth.models import DailyTaskLog, KudosNote, WeeklyReview

    User = get_user_model()
    today = timezone.localdate()
    # 本週的週一 ~ 週日
    end_date = today
    start_date = today - timedelta(days=today.weekday())  # 本週一

    # 找出本週有互動的使用者
    active_user_ids = set(
        DailyTaskLog.objects.filter(
            date__range=(start_date, end_date)
        ).values_list("user_id", flat=True)
    ) | set(
        KudosNote.objects.filter(
            created_at__date__range=(start_date, end_date)
        ).values_list("user_id", flat=True)
    )

    created_count = 0
    for user_id in active_user_ids:
        try:
            kudos_count = KudosNote.objects.filter(
                user_id=user_id,
                created_at__date__range=(start_date, end_date),
            ).count()

            task_count = DailyTaskLog.objects.filter(
                user_id=user_id,
                date__range=(start_date, end_date),
            ).count()

            summary_data = {
                "kudos_count": kudos_count,
                "task_count": task_count,
                "tree_points": kudos_count + task_count,
                "start_date": str(start_date),
                "end_date": str(end_date),
            }

            WeeklyReview.objects.update_or_create(
                user_id=user_id,
                start_date=start_date,
                defaults={"end_date": end_date, "summary_data": summary_data},
            )
            created_count += 1

        except Exception as exc:
            logger.exception("產生週回顧失敗（user_id=%s）", user_id)
            raise self.retry(exc=exc, countdown=60)

    logger.info("weekly_review: 為 %d 位使用者建立回顧（%s ~ %s）", created_count, start_date, end_date)
    return created_count
