import django
django.setup()
from celery import shared_task
from datetime import datetime, timezone

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='delivery:execute')
def execute(self, payload, **kwargs):
    data: dict = {}
    try:
        
        data.update(
            {
                'action': 'done',
                'time':  datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
                'result': 'success'
            }
        )
    
    except Exception as err:
        raise ValueError(f"Error saving delivery data into db: {err}")
    
    return data