"""SQLAlchemy and AST-based query validator implementation using sqlglot."""

from __future__ import annotations

import re
from typing import Any

import sqlglot
from sqlglot import exp

from app.application.interfaces.i_query_validator import IQueryValidator
from app.core.exceptions import InvalidQueryError
from app.domain.value_objects.query import QueryRequest

# Forbidden SQL statement AST node types
FORBIDDEN_AST_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.Command,
    exp.Merge,
    exp.Execute,
)

# Additional keyword patterns for safety checks
FORBIDDEN_KEYWORD_PATTERNS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|EXEC|EXECUTE|MERGE|GRANT|REVOKE|VACUUM|CALL)\b",
    re.IGNORECASE,
)


class SqlAlchemyQueryValidator(IQueryValidator):
    """AST-based query validator enforcing read-only SELECT constraints."""

    def validate(self, request: QueryRequest) -> None:
        """Validate query text against strict security and AST rules."""
        raw_sql = request.query.sql.strip()
        if not raw_sql:
            raise InvalidQueryError("Query SQL string must not be empty.")

        # 1. Reject multiple statements via trailing semicolons
        cleaned_sql = raw_sql.rstrip(";").strip()
        if ";" in cleaned_sql:
            raise InvalidQueryError("Multiple SQL statements are not permitted.")

        # 2. Parse AST via sqlglot
        try:
            parsed_statements = sqlglot.parse(cleaned_sql)
        except Exception as exc:
            raise InvalidQueryError(f"SQL syntax parse error: {exc}") from exc

        valid_statements = [s for s in parsed_statements if s is not None]
        if not valid_statements:
            raise InvalidQueryError("Empty query provided.")

        if len(valid_statements) > 1:
            raise InvalidQueryError("Multiple SQL statements are not permitted.")

        stmt = valid_statements[0]

        # 3. Root statement MUST be SELECT or UNION (including CTE WITH)
        if not isinstance(stmt, (exp.Select, exp.Union)):
            raise InvalidQueryError(
                f"Query statement type '{type(stmt).__name__}' is not allowed. "
                "Only SELECT queries are permitted."
            )

        # 4. AST Traversal: Check for forbidden operations inside subqueries/CTEs
        for node in stmt.walk():
            if isinstance(node, FORBIDDEN_AST_NODES):
                raise InvalidQueryError(
                    f"Forbidden SQL operation '{type(node).__name__}' detected. "
                    "Only SELECT queries are permitted."
                )

        # 5. Regex backup check for keywords
        sql_without_strings = re.sub(r"'[^']*'", "''", cleaned_sql)
        sql_without_strings = re.sub(r'"[^"]*"', '""', sql_without_strings)

        match = FORBIDDEN_KEYWORD_PATTERNS.search(sql_without_strings)
        if match:
            forbidden_kw = match.group(1).upper()
            raise InvalidQueryError(
                f"Forbidden SQL keyword '{forbidden_kw}' detected. "
                "Only SELECT queries are permitted."
            )

        # 6. Validate named parameters structure if parameters are supplied
        self._validate_parameters(request.parameters)

    def _validate_parameters(self, parameters: dict[str, Any]) -> None:
        """Ensure parameter keys are valid identifiers."""
        for key in parameters:
            if not isinstance(key, str) or not key.isidentifier():
                raise InvalidQueryError(
                    f"Invalid parameter name '{key}'. "
                    "Parameter names must be valid identifiers."
                )
