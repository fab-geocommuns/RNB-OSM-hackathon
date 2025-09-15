from flask_crontab import Crontab

crontab = Crontab()


def init_crontab(app) -> None:
    crontab.init_app(app)


@crontab.job(day_of_week="2", hour="8", minute="0")
def cleanup_exports():
    for export in Export.query.filter(
        Export.created_at < datetime.now() - timedelta(days=7)
    ):
        export.cleanup()
    db.session.commit()
