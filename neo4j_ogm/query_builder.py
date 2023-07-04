"""
COMPARISON OPERATORS
$eq
$ne
$gt
$gte
$lt
$lte
$in
$nin
$contains
$startsWith
$endsWith
$regex

LOGICAL OPERATORS
$and
$or
$xor
$not
$all

ELEMENT OPERATORS
$exists

ARRAY OPERATORS
$size
"""


from typing import Any


class QueryBuilder:
    __comparison_operants: list[str] = [
        "$eq",
        "$ne",
        "$gt",
        "$gte",
        "$lt",
        "$lte",
        "$in",
        "$nin",
        "$contains",
        "$startsWith",
        "$endsWith",
        "$regex",
    ]
    __logical_operants: list[str] = [
        "$and",
        "$or",
        "$xor",
        "$not",
        "$all",
    ]
    __element_operants: list[str] = ["$exists"]
    __list_operants: list[str] = ["$size"]
    _prefix: str | None = None
    ref: str = "n"
    property_name: str

    def _build_comparison_operant(self, operant: str, value: Any) -> tuple[str, dict[str, Any]]:
        parameters = {}
        query = ""
        parameter_name = self._build_parameter_name(operant=operant)

        match operant:
            case "$eq":
                query = f"{self.ref}.{self.property_name} = ${parameter_name}"
                parameters[parameter_name] = value

            case "$ne":
                query = f"NOT({self.ref}.{self.property_name} = ${parameter_name})"
                parameters[parameter_name] = value

            case "$gt":
                query = f"{self.ref}.{self.property_name} > ${parameter_name}"
                parameters[parameter_name] = value

            case "$gte":
                query = f"{self.ref}.{self.property_name} >= ${parameter_name}"
                parameters[parameter_name] = value

            case "$lt":
                query = f"{self.ref}.{self.property_name} < ${parameter_name}"
                parameters[parameter_name] = value

            case "$lte":
                query = f"{self.ref}.{self.property_name} <= ${parameter_name}"
                parameters[parameter_name] = value

            case "$in":
                query = f"{self.ref}.{self.property_name} IN ${parameter_name}"
                parameters[parameter_name] = value

            case "$nin":
                query = f"NOT({self.ref}.{self.property_name} IN ${parameter_name})"
                parameters[parameter_name] = value

            case "$contains":
                query = f"{self.ref}.{self.property_name} CONTAINS ${parameter_name}"
                parameters[parameter_name] = value

            case "$startsWith":
                query = f"{self.ref}.{self.property_name} STARTS WITH ${parameter_name}"
                parameters[parameter_name] = value

            case "$endsWith":
                query = f"{self.ref}.{self.property_name} ENDS WITH ${parameter_name}"
                parameters[parameter_name] = value

            case "$regex":
                query = f"{self.ref}.{self.property_name} =~ ${parameter_name}"
                parameters[parameter_name] = value

        return query, parameters

    def _build_parameter_name(self, operant) -> str:
        if self._prefix:
            return f"{self._prefix}_{operant[1:]}"

        return f"{self.ref}__{operant[1:]}"
