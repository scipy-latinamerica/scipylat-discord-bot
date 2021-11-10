import sentry_sdk
from decouple import config

sentry_sdk.init(
    config("SENTRY_TOKEN"),

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)

division_by_zero = 1 / 0
