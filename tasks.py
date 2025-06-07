from celery import Celery

celery = Celery("tasks")


@celery.task
def prepare_export():
    pass
