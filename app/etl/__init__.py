"""ETL package: validación, deduplicación, estimación y pipeline de ingesta."""

from .source_priority import SOURCE_PRIORITY, priority_of  # noqa: F401
from .validators import (  # noqa: F401
    is_valid_cif_format,
    is_fake_cif,
    validate_facturacion,
    validate_empleados,
    validate_record,
)
from .publicidad_estimator import (  # noqa: F401
    SECTOR_AD_INTENSITY,
    DEFAULT_INTENSITY,
    estimate_record,
    estimate_all_missing,
)
