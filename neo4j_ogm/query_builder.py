from copy import deepcopy
from typing import Any

from neo4j_ogm.exceptions import InvalidOperator


class QueryBuilder:
    """
    Builder class for generating queries from expressions.
    """

    __comparison_operator: dict[str, str] = {
        "$eq": "{property_name} = {value}",
        "$ne": "NOT({property_name} = {value})",
        "$gt": "{property_name} > {value}",
        "$gte": "{property_name} >= {value}",
        "$lt": "{property_name} < {value}",
        "$lte": "{property_name} <= {value}",
        "$in": "{value} IN {property_name}",
        "$nin": "NOT({value} IN {property_name})",
        "$contains": "{property_name} CONTAINS {value}",
        "$startsWith": "{property_name} STARTS WITH {value}",
        "$endsWith": "{property_name} ENDS WITH {value}",
        "$regex": "{property_name} =~ {value}",
    }
    __logical_operator: dict[str, str] = {"$and": "AND", "$or": "OR", "$xor": "XOR"}
    __neo4j_operator: dict[str, str] = {"$elementId": "elementId({ref}) = {value}", "$id": "ID({ref}) = {value}"}
    _variable_name_overwrite: str | None = None
    _parameter_count: int = 0
    property_name: str
    ref: str

    def build_property_expression(self, expressions: dict[str, Any], ref: str = "n") -> tuple[str, dict[str, Any]]:
        """
        Builds a query for filtering properties with the given operators.

        Args:
            expressions (dict[str, Any]): The expressions defining the operators.
            ref (str, optional): The variable to use inside the generated query. Defaults to "n".

        Returns:
            tuple[str, dict[str, Any]]: The generated query and parameters.
        """
        normalized_expressions = self._normalize_expressions(expressions=expressions)
        self.ref = ref

        return self._build_nested_expressions(normalized_expressions)

    def _build_nested_expressions(self, expressions: dict[str, Any], level: int = 0) -> tuple[str, dict[str, Any]]:
        """
        Builds nested operators defined in provided expressions.

        Args:
            expressions (dict[str, Any]): The expressions to build the query from.
            level (int, optional): The recursion depth level. Should not be modified outside the function itself.
                Defaults to 0.

        Raises:
            InvalidOperator: If the `expressions` parameter is not a valid dict.

        Returns:
            tuple[str, dict[str, Any]]: The generated query and parameters.
        """
        complete_parameters: dict[str, Any] = {}
        partial_queries: list[str] = []

        if not isinstance(expressions, dict):
            raise InvalidOperator(f"Expressions must be instance of dict, got {type(expressions)}")

        for property_or_operator, expression_or_value in expressions.items():
            parameters = {}
            query = ""

            if not property_or_operator.startswith("$"):
                # Update current property name if the key is not a operator
                self.property_name = property_or_operator

            if level == 0 and property_or_operator.startswith("$"):
                query, parameters = self._build_neo4j_operator(property_or_operator, expression_or_value)
            elif property_or_operator == "$not":
                query, parameters = self._build_not_operator(expression=expression_or_value)
            elif property_or_operator == "$size":
                query, parameters = self._build_size_operator(expression=expression_or_value)
            elif property_or_operator == "$where":
                query, parameters = self._build_where_operator(expression=expression_or_value)
            elif property_or_operator == "$all":
                query, parameters = self._build_all_operator(expressions=expression_or_value)
            elif property_or_operator == "$exists":
                query = self._build_exists_operator(exists=expression_or_value)
            elif property_or_operator in self.__comparison_operator:
                query, parameters = self._build_comparison_operator(
                    operator=property_or_operator, value=expression_or_value
                )
            elif property_or_operator in self.__logical_operator:
                query, parameters = self._build_logical_operator(
                    operator=property_or_operator, expressions=expression_or_value
                )
            elif not property_or_operator.startswith("$"):
                query, parameters = self._build_nested_expressions(expressions=expression_or_value, level=level + 1)

            partial_queries.append(query)
            complete_parameters = {**complete_parameters, **parameters}

        complete_query = " AND ".join(partial_queries)
        return complete_query, complete_parameters

    def _build_comparison_operator(self, operator: str, value: Any) -> tuple[str, dict[str, Any]]:
        """
        Builds comparison operators.

        Args:
            operator (str): The operator to build.
            value (Any): The provided value for the operator.

        Returns:
            tuple[str, dict[str, Any]]: The generated query and parameters.
        """
        parameter_name = self._get_parameter_name()
        parameters = {}

        query = self.__comparison_operator[operator].format(
            property_name=self._get_variable_name(),
            value=f"${parameter_name}",
        )
        parameters[parameter_name] = value

        return query, parameters

    def _build_exists_operator(self, exists: bool) -> str:
        """
        Builds a `IS NOT NULL` or `IS NULL` query based on the defined value.

        Args:
            exists (bool): Whether the query should check if the property exists or not.

        Raises:
            InvalidOperator: If the operator value is not a bool.

        Returns:
            str: The generated query.
        """
        if not isinstance(exists, bool):
            raise InvalidOperator(f"$exists operator value must be a instance of bool, got {type(exists)}")

        query = "IS NULL" if exists is False else "IS NOT NULL"
        return query

    def _build_where_operator(self, expression: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """
        Applies a raw value as a query. The operator must contain a `$query` key with the query and a `$parameters`
        key with the required parameters for the query.

        Args:
            expression (dict[str, Any]): The expressions defined for the `$where` operator.

        Raises:
            InvalidOperator: If the operator value is not a dict, required keys are missing or the $parameters key
                is not a valid dict.

        Returns:
            tuple[str, dict[str, Any]]: The generated query and parameters.
        """
        if not isinstance(expression, dict) or "$query" not in expression or "$parameters" not in expression:
            raise InvalidOperator("$where operator value must be a dict with a $query and $parameters key")

        if not isinstance(expression["$parameters"], dict):
            raise InvalidOperator(f"$parameters operator must a dict, got {type(expression['$parameters'])}")

        complete_query: str = expression["$query"]
        complete_parameters = {}

        for parameter, value in expression["$parameters"].items():
            parameter_name = self._get_parameter_name()

            complete_query = complete_query.replace(f"${parameter}", f"${parameter_name}")
            complete_parameters[parameter_name] = value

        return complete_query, complete_parameters

    def _build_not_operator(self, expression: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """
        Builds a `NOT()` clause with the defined expressions.

        Args:
            expression (dict[str, Any]): The expressions defined for the `$not` operator.

        Returns:
            tuple[str, dict[str, Any]]: The generated query and parameters.
        """
        expression, complete_parameters = self._build_nested_expressions(expressions=expression, level=1)

        complete_query = f"NOT({expression})"
        return complete_query, complete_parameters

    def _build_size_operator(self, expression: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """
        Builds a `SIZE()` clause with the defined comparison operator.

        Args:
            expression (dict[str, Any]): The expression defined fot the `$size` operator.

        Returns:
            tuple[str, dict[str, Any]]: The generated query and parameters.
        """
        comparison_operator = next(iter(expression))
        self._variable_name_overwrite = f"SIZE({self._get_variable_name()})"

        query, parameters = self._build_comparison_operator(
            operator=comparison_operator, value=expression[comparison_operator]
        )

        self._variable_name_overwrite = None

        return query, parameters

    def _build_all_operator(self, expressions: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
        """
        Builds a `ALL()` clause with the defined expressions.

        Args:
            expressions (list[dict[str, Any]]): Expressions to apply inside the `$all` operator.

        Raises:
            InvalidOperator: If the operator value is not a list.

        Returns:
            tuple[str, dict[str, Any]]: The generated query and parameters.
        """
        self._variable_name_overwrite = "i"
        complete_parameters: dict[str, Any] = {}
        partial_queries: list[str] = []

        if not isinstance(expressions, list):
            raise InvalidOperator(f"Value of $all operator must be list, got {type(expressions)}")

        for expression in expressions:
            query, parameters = self._build_nested_expressions(expressions=expression, level=1)

            partial_queries.append(query)
            complete_parameters = {
                **complete_parameters,
                **parameters,
            }

        self._variable_name_overwrite = None

        complete_query = f"ALL(i IN {self._get_variable_name()} WHERE {' AND '.join(partial_queries)})"
        return complete_query, complete_parameters

    def _build_logical_operator(self, operator: str, expressions: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
        """
        Builds all expressions defined inside a logical operator.

        Args:
            operator (str): The logical operator.
            expressions (list[dict[str, Any]]): The expressions chained together by the operator.

        Raises:
            InvalidOperator: If the operator value is not a list.

        Returns:
            tuple[str, dict[str, Any]]: The query and parameters.
        """
        complete_parameters: dict[str, Any] = {}
        partial_queries: list[str] = []

        if not isinstance(expressions, list):
            raise InvalidOperator(f"Value of {operator} operator must be list, got {type(expressions)}")

        for expression in expressions:
            nested_query, parameters = self._build_nested_expressions(expressions=expression, level=1)

            partial_queries.append(nested_query)
            complete_parameters = {**complete_parameters, **parameters}

        complete_query = f"({f' {self.__logical_operator[operator]} '.join(partial_queries)})"
        return complete_query, complete_parameters

    def _build_neo4j_operator(self, operator: str, value: Any) -> tuple[str, dict[str, Any]]:
        """
        Builds operators for Neo4j-specific `elementId()` and `ID()`.

        Args:
            operator (str): The operator to build.
            value (Any): The value to use for building the operator.

        Returns:
            tuple[str, dict[str, Any]]: The generated query and parameters.
        """
        variable_name = self._get_parameter_name()

        query = self.__neo4j_operator[operator].format(ref=self.ref, value=variable_name)
        parameters = {f"{variable_name}": value}

        return query, parameters

    def _get_parameter_name(self) -> str:
        """
        Builds the parameter name and increment the parameter count by one.

        Returns:
            str: The generated parameter name.
        """
        parameter_name = f"{self.ref}_{self._parameter_count}"
        self._parameter_count += 1

        return parameter_name

    def _get_variable_name(self) -> str:
        """
        Builds the variable name used in the query.

        Returns:
            str: The generated variable name.
        """
        if self._variable_name_overwrite:
            return self._variable_name_overwrite

        return f"{self.ref}.{self.property_name}"

    def _normalize_expressions(self, expressions: dict[str, Any], level: int = 0) -> dict[str, Any]:
        """
        Normalizes and formats the provided expressions into usable expressions for the builder.

        Args:
            expressions (dict[str, Any]): The expressions to normalize
            level (int, optional): The recursion depth level. Should not be modified outside the function itself.
                Defaults to 0.

        Returns:
            dict[str, Any]: The normalized expressions.
        """
        normalized: dict[str, Any] = deepcopy(expressions)

        if isinstance(normalized, dict):
            # Transform values without a operator to a `$eq` operator
            for operator, value in normalized.items():
                if not isinstance(value, dict) and not isinstance(value, list):
                    # If the operator is a `$not` operator or just a property name, add a `$eq` operator
                    if operator in ["$not", "$size"] or not operator.startswith("$"):
                        normalized[operator] = {"$eq": value}

            if (
                len(normalized.keys()) > 1
                and level > 0
                and ("$query" not in normalized and "$parameters" not in normalized)
            ):
                # If more than one operator is defined in a dict, transform operators to `$and` operator
                normalized = {"$and": [{operator: expression} for operator, expression in normalized.items()]}

        # Normalize nested operators
        if isinstance(normalized, list):
            for index, expression in enumerate(normalized):
                normalized[index] = self._normalize_expressions(expression, level + 1)
        elif isinstance(normalized, dict) and ("$query" not in normalized and "$parameters" not in normalized):
            for operator, expression in normalized.items():
                normalized[operator] = self._normalize_expressions(expression, level + 1)

        return normalized
