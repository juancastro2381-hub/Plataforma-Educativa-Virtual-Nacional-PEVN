"""
PEVN Backend — MEN Open Data / DUE (Directorio Único de Establecimientos) Adapter

Decouples the PEvN Domain Model from changes in official government open-data schemas.
Supports ingestion from Socrata SODA JSON, CSV rows, and official MinEducación export structures.
"""

from __future__ import annotations

import re
from typing import Any

DANE_REGEX = re.compile(r"^\d{12}$")


class MenOpenDataAdapter:
    """
    Normalizes official Colombian Government Open Data (MEN DUE / SIMAT / DANE DIREDU)
    into standard PEvN domain format.
    """

    # Field aliases mapping for flexibility against government schema changes
    FIELD_ALIASES: dict[str, list[str]] = {
        "dane_code": [
            "dane_code",
            "codigo_dane",
            "codigodane",
            "cod_dane",
            "dane_ee",
            "dane_establecimiento",
            "codigo_establecimiento",
            "codigoestablecimiento",
            "codigoinstitucion",
            "codigo_institucion",
            "cod_inst",
            "dane",
        ],
        "name": [
            "name",
            "nombre_establecimiento",
            "nombreestablecimiento",
            "nombre_ee",
            "nombreee",
            "nombre",
            "razon_social",
            "establecimiento_educativo",
            "nombre_institucion",
            "nombreinstitucion",
            "institucion",
        ],
        "department_code": [
            "department_code",
            "cod_dane_departamento",
            "coddanedepartamento",
            "cod_dane_depto",
            "codigo_departamento",
            "codigodepartamento",
            "cod_depto",
            "cod_dep",
            "codigo_depto_dane",
            "depto_codigo",
        ],
        "department_name": [
            "department_name",
            "departamento",
            "nom_dep",
            "nombre_departamento",
            "nombredepartamento",
            "depto",
        ],
        "municipality_code": [
            "municipality_code",
            "cod_dane_municipio",
            "coddanemunicipio",
            "cod_dane_mpio",
            "codigo_municipio",
            "codigomunicipio",
            "cod_mun",
            "cod_municipio",
            "codigo_mpio",
            "codigompio",
            "mpio_codigo",
        ],
        "municipality_name": [
            "municipality_name",
            "municipio",
            "nom_mun",
            "nombre_municipio",
            "nombremunicipio",
            "mpio",
        ],
        "secretaria_code": [
            "secretaria_code",
            "codigo_secretaria",
            "cod_secretaria",
            "cod_sec",
            "codigo_etc",
        ],
        "secretaria_name": [
            "secretaria_name",
            "secretaria",
            "nombre_secretaria",
            "secretaria_educacion",
            "nom_sec",
            "etc",
        ],
        "sector": ["sector", "sector_educativo", "tipo_sector", "naturaleza"],
        "zone": ["zone", "zona", "zona_sede", "zona_ee"],
        "calendar": ["calendar", "calendario", "tipo_calendario"],
        "academic_character": [
            "academic_character",
            "caracter",
            "genero_caracter",
            "modalidad",
            "especialidad",
        ],
        "official_address": [
            "official_address",
            "direccion",
            "direccion_ee",
            "direccion_establecimiento",
            "dir_establecimiento",
        ],
        "official_phone": [
            "official_phone",
            "telefono",
            "telefono_ee",
            "tel_establecimiento",
            "telefonos",
        ],
        "official_email": [
            "official_email",
            "correo_electronico",
            "correo",
            "email",
            "email_ee",
            "correo_institucional",
        ],
        "educational_levels": [
            "educational_levels",
            "niveles",
            "niveles_educativos",
            "grados_ofrecidos",
        ],
        "status": ["status", "estado", "estado_ee", "estado_establecimiento"],
        # Campus specific aliases
        "dane_sede_code": [
            "dane_sede_code",
            "codigo_dane_sede",
            "codigodanesede",
            "cod_sede",
            "dane_sede",
            "codigo_sede",
            "codigosede",
        ],
        "campus_name": [
            "campus_name",
            "nombre_sede",
            "nombresede",
            "nombre_sede_educativa",
            "sede",
        ],
        "is_main": [
            "is_main",
            "es_principal",
            "principal",
            "es_sede_principal",
            "sede_principal",
        ],
        "campus_address": [
            "campus_address",
            "direccion_sede",
            "dir_sede",
        ],
        "campus_zone": [
            "campus_zone",
            "zona_sede",
        ],
        "campus_status": [
            "campus_status",
            "estado_sede",
        ],
    }

    @classmethod
    def _extract_field(cls, raw: dict[str, Any], field_key: str, default: Any = None) -> Any:
        """Find value by inspecting aliases in a case-insensitive, normalized way."""
        aliases = cls.FIELD_ALIASES.get(field_key, [field_key])
        raw_keys_lower = {str(k).strip().lower(): v for k, v in raw.items()}

        for alias in aliases:
            alias_lower = alias.lower()
            if alias_lower in raw_keys_lower and raw_keys_lower[alias_lower] is not None:
                val = raw_keys_lower[alias_lower]
                if isinstance(val, str):
                    val = val.strip()
                return val
        return default

    @classmethod
    def normalize_dane(cls, raw_dane: Any) -> str:
        """Ensures 12-digit format with preserved leading zeroes."""
        if raw_dane is None:
            raise ValueError("El código DANE no puede ser nulo.")
        clean = str(raw_dane).strip()
        # If integer conversion lost leading zero (e.g. 11-digit starting with 5 or 8), pad with 0
        if len(clean) == 11 and clean.isdigit():
            clean = "0" + clean
        if not (clean.isdigit() and len(clean) == 12):
            raise ValueError(f"Código DANE '{clean}' inválido: debe tener exactamente 12 dígitos numéricos.")
        return clean

    @classmethod
    def normalize_record(
        cls,
        raw_row: dict[str, Any],
        *,
        source_system: str = "MINISTERIO DE EDUCACION NACIONAL (DUE) / DANE",
        source_dataset: str = "datos.gov.co/c36d-tcj8",
    ) -> dict[str, Any]:
        """
        Transforms a single raw flat or nested government record into a standardized institution dictionary.
        """
        raw_dane = cls._extract_field(raw_row, "dane_code")
        dane_code = cls.normalize_dane(raw_dane)

        name = str(cls._extract_field(raw_row, "name", "ESTABLECIMIENTO EDUCATIVO SIN NOMBRE")).upper().strip()
        dept_code = str(cls._extract_field(raw_row, "department_code", dane_code[:2])).strip()
        # Pad department code to 2 digits if needed
        if len(dept_code) == 1 and dept_code.isdigit():
            dept_code = "0" + dept_code

        dept_name = str(cls._extract_field(raw_row, "department_name", "DEPARTAMENTO NO ESPECIFICADO")).upper().strip()
        muni_code = str(cls._extract_field(raw_row, "municipality_code", dane_code[:5])).strip()
        # Pad municipality code to 5 digits if needed
        if len(muni_code) == 4 and muni_code.isdigit():
            muni_code = "0" + muni_code

        muni_name = str(cls._extract_field(raw_row, "municipality_name", "MUNICIPIO NO ESPECIFICADO")).upper().strip()

        secretaria_code = cls._extract_field(raw_row, "secretaria_code")
        secretaria_name = cls._extract_field(raw_row, "secretaria_name")
        sector = str(cls._extract_field(raw_row, "sector", "OFICIAL")).upper().strip()
        zone = str(cls._extract_field(raw_row, "zone", "URBANA")).upper().strip()
        calendar = str(cls._extract_field(raw_row, "calendar", "A")).upper().strip()
        academic_character = str(cls._extract_field(raw_row, "academic_character", "ACADÉMICO")).upper().strip()
        official_address = cls._extract_field(raw_row, "official_address")
        official_phone = cls._extract_field(raw_row, "official_phone")
        official_email = cls._extract_field(raw_row, "official_email")
        educational_levels = cls._extract_field(raw_row, "educational_levels", "PREESCOLAR,PRIMARIA,SECUNDARIA,MEDIA")
        status = str(cls._extract_field(raw_row, "status", "ACTIVO")).upper().strip()
        is_active = status == "ACTIVO" or str(cls._extract_field(raw_row, "is_active", "true")).lower() in ["true", "1", "t"]

        # Parse Campuses if already nested
        campuses: list[dict[str, Any]] = []
        raw_campuses = raw_row.get("campuses")
        if isinstance(raw_campuses, list) and raw_campuses:
            for c_idx, c_raw in enumerate(raw_campuses):
                raw_c_dane = cls._extract_field(c_raw, "dane_sede_code", cls._extract_field(c_raw, "dane_code"))
                if not raw_c_dane:
                    continue
                c_dane = cls.normalize_dane(raw_c_dane)
                c_name = str(cls._extract_field(c_raw, "campus_name", cls._extract_field(c_raw, "name", f"SEDE {c_idx + 1}"))).upper().strip()
                c_is_main = bool(cls._extract_field(c_raw, "is_main", c_idx == 0 or c_dane == dane_code))
                c_zone = str(cls._extract_field(c_raw, "campus_zone", cls._extract_field(c_raw, "zone", zone))).upper().strip()
                c_address = cls._extract_field(c_raw, "campus_address", cls._extract_field(c_raw, "address", official_address))
                c_status = str(cls._extract_field(c_raw, "campus_status", cls._extract_field(c_raw, "status", "ACTIVA"))).upper().strip()
                c_active = c_status == "ACTIVA"

                campuses.append(
                    {
                        "dane_sede_code": c_dane,
                        "name": c_name,
                        "is_main": c_is_main,
                        "zone": c_zone,
                        "address": c_address,
                        "status": c_status,
                        "is_active": c_active,
                    }
                )
        else:
            # Check if row is a flat campus row
            raw_sede_dane = cls._extract_field(raw_row, "dane_sede_code")
            if raw_sede_dane:
                c_dane = cls.normalize_dane(raw_sede_dane)
                c_name = str(cls._extract_field(raw_row, "campus_name", name)).upper().strip()
                c_is_main = bool(cls._extract_field(raw_row, "is_main", c_dane == dane_code))
                campuses.append(
                    {
                        "dane_sede_code": c_dane,
                        "name": c_name,
                        "is_main": c_is_main,
                        "zone": zone,
                        "address": official_address,
                        "status": "ACTIVA",
                        "is_active": is_active,
                    }
                )
            else:
                # Default Sede Principal with establishment DANE
                campuses.append(
                    {
                        "dane_sede_code": dane_code,
                        "name": f"SEDE PRINCIPAL - {name}",
                        "is_main": True,
                        "zone": zone,
                        "address": official_address,
                        "status": "ACTIVA",
                        "is_active": is_active,
                    }
                )

        return {
            "dane_code": dane_code,
            "name": name,
            "department_code": dept_code,
            "department_name": dept_name,
            "municipality_code": muni_code,
            "municipality_name": muni_name,
            "secretaria_code": str(secretaria_code).strip() if secretaria_code else None,
            "secretaria_name": str(secretaria_name).strip() if secretaria_name else None,
            "sector": sector,
            "zone": zone,
            "calendar": calendar,
            "academic_character": academic_character,
            "official_address": str(official_address).strip() if official_address else None,
            "official_phone": str(official_phone).strip() if official_phone else None,
            "official_email": str(official_email).strip().lower() if official_email else None,
            "educational_levels": educational_levels,
            "status": status,
            "is_active": is_active,
            "source_system": source_system,
            "source_dataset": source_dataset,
            "source_record_id": raw_row.get("source_record_id") or raw_row.get("id"),
            "source_updated_at": raw_row.get("source_updated_at"),
            "campuses": campuses,
        }

    @classmethod
    def group_flat_rows_into_establishments(
        cls,
        flat_rows: list[dict[str, Any]],
        *,
        source_system: str = "MINISTERIO DE EDUCACION NACIONAL (DUE) / DANE",
        source_dataset: str = "datos.gov.co/c36d-tcj8",
    ) -> list[dict[str, Any]]:
        """
        Groups flat rows (e.g. from DUE Sedes export) where each row has establishment and campus fields,
        into structured establishment dictionaries with nested campuses.
        """
        grouped: dict[str, dict[str, Any]] = {}

        for row in flat_rows:
            try:
                norm = cls.normalize_record(
                    row,
                    source_system=source_system,
                    source_dataset=source_dataset,
                )
            except Exception:
                # Let sync service quality gate handle malformed items
                raw_dane = str(cls._extract_field(row, "dane_code", "UNKNOWN"))
                norm = {"dane_code": raw_dane, "name": "INVALID", "campuses": []}

            dane_code = norm["dane_code"]
            if dane_code not in grouped:
                grouped[dane_code] = norm
            else:
                # Merge campuses without duplicates
                existing_campuses = {c["dane_sede_code"]: c for c in grouped[dane_code]["campuses"]}
                for new_c in norm.get("campuses", []):
                    c_code = new_c["dane_sede_code"]
                    if c_code not in existing_campuses:
                        grouped[dane_code]["campuses"].append(new_c)
                        existing_campuses[c_code] = new_c

        return list(grouped.values())
