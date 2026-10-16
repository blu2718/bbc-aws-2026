"""Campos de formulario compartidos."""
from django import forms
from django.core.exceptions import ValidationError

# Rango de un entero con signo de 64 bits: lo que acepta SQLite (y el BIGINT de PostgreSQL).
_ENTERO_MIN, _ENTERO_MAX = -(2**63), 2**63 - 1


class SeleccionMultiple(forms.ModelMultipleChoiceField):
    """ModelMultipleChoiceField que rechaza IDs fuera de rango antes de consultar la base.

    Django solo atrapa ValueError y TypeError al buscar los IDs enviados. Con SQLite, un ID
    mayor que un entero de 64 bits (por ejemplo "99999999999999999999") lanza OverflowError
    y la página responde 500. Aquí se responde como cualquier opción inválida (400).
    """

    def _check_values(self, value):
        if self.to_field_name is None:
            for valor in value:
                try:
                    entero = int(str(valor).strip())
                except (TypeError, ValueError):
                    continue  # Django ya informa estos casos como opción inválida
                if not _ENTERO_MIN <= entero <= _ENTERO_MAX:
                    raise ValidationError(
                        self.error_messages["invalid_pk_value"], code="invalid_pk_value", params={"pk": valor},
                    )
        return super()._check_values(value)
