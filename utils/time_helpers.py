import datetime


def get_now() -> datetime.datetime:
    return datetime.datetime.now((datetime.timezone.utc))


def str_datetime_to_datetime_obj(str_datetime: str) -> datetime.datetime:
    datetime_obj = datetime.datetime.strptime(str_datetime, "%Y-%m-%d %H:%M:%S.%f%z")
    return datetime_obj
