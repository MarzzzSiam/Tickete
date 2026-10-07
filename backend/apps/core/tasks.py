from celery import shared_task


@shared_task(ignore_result=False)
def worker_ping():
    return {"status": "ok", "service": "tickete-worker"}
