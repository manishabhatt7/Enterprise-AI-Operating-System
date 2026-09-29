import logging
import sys

import structlog

def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
        force=True,
    )

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.INFO
        ),
    )