# -*- coding: utf-8 -*-
"""
Table/list handling keywords for Windows automation.

Provides keywords for interacting with tables/lists rendered as Windows UI
Automation elements, typically with Header/HeaderItem and ListItem/Text structure.
"""

from .keywordgroup import KeywordGroup


class _TableKeywords(KeywordGroup):
    """Keywords for table/list operations in Windows automation."""

    def __init__(self):
        pass

    # =============================================================================
    # Core Data Retrieval
    # =============================================================================

    def get_table_data(
        self,
        table_locator,
        header_locator,
        header_attribute,
        row_locator,
        cell_locator,
        cell_attribute,
        timeout=None,
    ):
        """Get complete table data including headers and all rows.

        Returns a list of lists: ``[headers_row, data_row1, data_row2, ...]``.
        Returns an empty list if the table is not found.

        Arguments:
        - ``table_locator``:    Locator for the table element.
        - ``header_locator``:   Locator for header items (relative to table).
        - ``header_attribute``: Attribute name to extract from headers.
        - ``row_locator``:      Locator for row items (relative to table).
        - ``cell_locator``:     Locator for cell items (relative to row).
        - ``cell_attribute``:   Attribute name to extract from cells.
        - ``timeout``:          Optional timeout in seconds.

        Examples:
        | ${table}= | Get Table Data | //Table[@Name='Files'] |
        | Log       | ${table}       |                        |
        """

        table_element = self.appium_get_element(
            table_locator, required=False, timeout=timeout
        )
        if not table_element:
            return []

        headers = self.appium_get_element_attributes_in_element(
            table_element, header_locator, header_attribute, timeout=timeout
        )
        if not headers:
            return []

        table = [headers]

        row_elements = self.appium_get_elements_in_element(
            table_element, row_locator, timeout=timeout
        )
        if not row_elements:
            return table

        for row_element in row_elements:
            cells = self.appium_get_element_attributes_in_element(
                row_element, cell_locator, cell_attribute, timeout=timeout
            )
            table.append(cells)


        return table

    def get_table_headers(
        self,
        table_locator,
        header_locator,
        header_attribute,
        timeout=None,
    ):
        """Get table headers only.

        Returns a list of header names, or an empty list if not found.

        Arguments:
        - ``table_locator``:    Locator for the table element.
        - ``header_locator``:   Locator for header items.
        - ``header_attribute``: Attribute name to extract.
        - ``timeout``:          Optional timeout in seconds.

        Examples:
        | ${headers}= | Get Table Headers | //Table[@Name='Files'] |
        """
        table_element = self.appium_get_element(
            table_locator, required=False, timeout=timeout
        )
        if not table_element:
            return []

        headers = self.appium_get_element_attributes_in_element(
            table_element, header_locator, header_attribute, timeout=timeout
        )
        return headers if headers else []

    def get_table_rows(
        self,
        table_locator,
        row_locator,
        cell_locator,
        cell_attribute,
        timeout=None,
    ):
        """Get table rows only (without headers).

        Returns a list of rows, where each row is a list of cell values.

        Arguments:
        - ``table_locator``:  Locator for the table element.
        - ``row_locator``:    Locator for row items.
        - ``cell_locator``:   Locator for cell items.
        - ``cell_attribute``: Attribute name to extract.
        - ``timeout``:        Optional timeout in seconds.

        Examples:
        | ${rows}= | Get Table Rows | //Table[@Name='Files'] |
        """
        table_element = self.appium_get_element(
            table_locator, required=False, timeout=timeout
        )
        if not table_element:
            return []

        row_elements = self.appium_get_elements_in_element(
            table_element, row_locator, timeout=timeout
        )
        if not row_elements:
            return []

        rows = []
        for row_element in row_elements:
            cells = self.appium_get_element_attributes_in_element(
                row_element, cell_locator, cell_attribute, timeout=timeout
            )
            rows.append(cells)

        return rows

    def get_table_cell(
        self,
        row_index,
        col_index,
        table_data=None,
        table_locator=None,
        **kwargs,
    ):
        """Get specific cell value by row and column index.

        ``row_index`` is 0-based and excludes the header row.
        ``col_index`` is 0-based.

        Returns the cell value as a string, or ``None`` if out of bounds.

        Arguments:
        - ``row_index``:     Row index (0-based, excluding headers).
        - ``col_index``:     Column index (0-based).
        - ``table_data``:    Pre-fetched table data (optional).
        - ``table_locator``: Locator for get_table_data if table_data not given.

        Examples:
        | ${value}= | Get Table Cell | 0 | 1 | table_locator=//Table |
        """
        row_index = int(row_index)
        col_index = int(col_index)

        if table_data is None:
            table_data = self.get_table_data(
                table_locator=table_locator, **kwargs
            )

        if not table_data or len(table_data) <= 1:
            return None

        actual_row_index = row_index + 1
        if actual_row_index >= len(table_data):
            return None

        row = table_data[actual_row_index]
        if col_index >= len(row):
            return None

        return row[col_index]

    def get_table_row(
        self,
        row_index,
        table_data=None,
        include_headers=False,
        table_locator=None,
        **kwargs,
    ):
        """Get specific row by index.

        ``row_index`` is 0-based. By default the header row is excluded
        from counting unless ``include_headers`` is ``True``.

        Returns a list of cell values, or ``None`` if out of bounds.

        Arguments:
        - ``row_index``:      Row index (0-based).
        - ``table_data``:     Pre-fetched table data (optional).
        - ``include_headers``: If True, row_index includes the header row.
        - ``table_locator``:  Locator for get_table_data if table_data not given.

        Examples:
        | ${row}= | Get Table Row | 0 | table_locator=//Table |
        """
        row_index = int(row_index)

        if table_data is None:
            table_data = self.get_table_data(
                table_locator=table_locator, **kwargs
            )

        if not table_data:
            return None

        actual_index = row_index if include_headers else row_index + 1

        if actual_index >= len(table_data):
            return None

        return table_data[actual_index]

    def get_table_column(
        self,
        col_name=None,
        col_index=None,
        table_data=None,
        table_locator=None,
        **kwargs,
    ):
        """Get all values from a specific column.

        Specify either ``col_name`` (header value) or ``col_index`` (0-based).

        Returns a list of column values (excluding the header).

        Arguments:
        - ``col_name``:      Column name (header value).
        - ``col_index``:     Column index (0-based).
        - ``table_data``:    Pre-fetched table data (optional).
        - ``table_locator``: Locator for get_table_data if table_data not given.

        Examples:
        | ${names}= | Get Table Column | col_name=Name          | table_locator=//Table |
        | ${sizes}= | Get Table Column | col_index=1            | table_locator=//Table |
        """
        if table_data is None:
            table_data = self.get_table_data(
                table_locator=table_locator, **kwargs
            )

        if not table_data or len(table_data) <= 1:
            return []

        headers = table_data[0]

        if col_name is not None:
            try:
                col_index = headers.index(col_name)
            except ValueError:
                return []
        elif col_index is not None:
            col_index = int(col_index)
        else:
            return []

        column_values = []
        for row in table_data[1:]:
            if col_index < len(row):
                column_values.append(row[col_index])

        return column_values

    def get_table_dimensions(
        self,
        table_data=None,
        table_locator=None,
        **kwargs,
    ):
        """Get table dimensions (rows, columns).

        Returns a tuple ``(row_count, column_count)`` excluding the header row.

        Arguments:
        - ``table_data``:    Pre-fetched table data (optional).
        - ``table_locator``: Locator for get_table_data if table_data not given.

        Examples:
        | ${rows} | ${cols}= | Get Table Dimensions | table_locator=//Table |
        """
        if table_data is None:
            table_data = self.get_table_data(
                table_locator=table_locator, **kwargs
            )

        if not table_data:
            return (0, 0)

        row_count = len(table_data) - 1
        col_count = len(table_data[0]) if table_data else 0

        return (row_count, col_count)

    # =============================================================================
    # Search & Filter
    # =============================================================================

    def find_table_row_by_value(
        self,
        col_name,
        value,
        table_data=None,
        exact_match=True,
        table_locator=None,
        **kwargs,
    ):
        """Find first row where specified column matches value.

        Returns the first matching row as a list, or ``None`` if not found.

        Arguments:
        - ``col_name``:      Column name to search in.
        - ``value``:         Value to search for.
        - ``table_data``:    Pre-fetched table data (optional).
        - ``exact_match``:   If True, use exact match; if False, use substring.
        - ``table_locator``: Locator for get_table_data if table_data not given.

        Examples:
        | ${row}= | Find Table Row By Value | Name | file1.txt | table_locator=//Table |
        """
        if table_data is None:
            table_data = self.get_table_data(
                table_locator=table_locator, **kwargs
            )

        if not table_data or len(table_data) <= 1:
            return None

        headers = table_data[0]
        try:
            col_idx = headers.index(col_name)
        except ValueError:
            return None

        for row in table_data[1:]:
            if col_idx < len(row):
                cell_value = row[col_idx]
                if exact_match:
                    if cell_value == value:
                        return row
                else:
                    if value in cell_value:
                        return row

        return None

    def find_table_rows_by_value(
        self,
        col_name,
        value,
        table_data=None,
        exact_match=True,
        table_locator=None,
        **kwargs,
    ):
        """Find all rows where specified column matches value.

        Returns a list of matching rows.

        Arguments:
        - ``col_name``:      Column name to search in.
        - ``value``:         Value to search for.
        - ``table_data``:    Pre-fetched table data (optional).
        - ``exact_match``:   If True, use exact match; if False, use substring.
        - ``table_locator``: Locator for get_table_data if table_data not given.

        Examples:
        | ${rows}= | Find Table Rows By Value | Status | Active | table_locator=//Table |
        """
        if table_data is None:
            table_data = self.get_table_data(
                table_locator=table_locator, **kwargs
            )

        if not table_data or len(table_data) <= 1:
            return []

        headers = table_data[0]
        try:
            col_idx = headers.index(col_name)
        except ValueError:
            return []

        matching = []
        for row in table_data[1:]:
            if col_idx < len(row):
                cell_value = row[col_idx]
                if exact_match:
                    if cell_value == value:
                        matching.append(row)
                else:
                    if value in cell_value:
                        matching.append(row)

        return matching

    def find_table_rows_by_multiple_values(
        self,
        criteria,
        table_data=None,
        exact_match=True,
        match_all=True,
        table_locator=None,
        **kwargs,
    ):
        """Find rows matching multiple column criteria.

        ``criteria`` is a dictionary of ``{column_name: value}`` pairs.

        Arguments:
        - ``criteria``:      Dict of {column_name: value} to match.
        - ``table_data``:    Pre-fetched table data (optional).
        - ``exact_match``:   If True, use exact match; if False, use substring.
        - ``match_all``:     If True, all criteria must match (AND); if False, any (OR).
        - ``table_locator``: Locator for get_table_data if table_data not given.

        Examples:
        | &{criteria}= | Create Dictionary | Status=Active | Type=File |
        | ${rows}=      | Find Table Rows By Multiple Values | ${criteria} | table_locator=//Table |
        """
        if table_data is None:
            table_data = self.get_table_data(
                table_locator=table_locator, **kwargs
            )

        if not table_data or len(table_data) <= 1:
            return []

        headers = table_data[0]

        col_indices = {}
        for col_name in criteria.keys():
            try:
                col_indices[col_name] = headers.index(col_name)
            except ValueError:
                if match_all:
                    return []
                continue

        matching = []
        for row in table_data[1:]:
            matches = []
            for col_name, expected_value in criteria.items():
                if col_name not in col_indices:
                    matches.append(False)
                    continue

                col_idx = col_indices[col_name]
                if col_idx >= len(row):
                    matches.append(False)
                    continue

                cell_value = row[col_idx]
                if exact_match:
                    matches.append(cell_value == expected_value)
                else:
                    matches.append(expected_value in cell_value)

            if match_all:
                if all(matches):
                    matching.append(row)
            else:
                if any(matches):
                    matching.append(row)

        return matching

    def search_table(
        self,
        search_term,
        table_data=None,
        case_sensitive=False,
        table_locator=None,
        **kwargs,
    ):
        """Search entire table for a term.

        Returns a list of tuples: ``(row_index, col_index, cell_value)``.

        Arguments:
        - ``search_term``:   Term to search for.
        - ``table_data``:    Pre-fetched table data (optional).
        - ``case_sensitive``: Whether search is case-sensitive.
        - ``table_locator``: Locator for get_table_data if table_data not given.

        Examples:
        | ${results}= | Search Table | error | table_locator=//Table |
        """
        if table_data is None:
            table_data = self.get_table_data(
                table_locator=table_locator, **kwargs
            )

        if not table_data or len(table_data) <= 1:
            return []

        if not case_sensitive:
            search_term = search_term.lower()

        results = []
        for row_idx, row in enumerate(table_data[1:]):
            for col_idx, cell in enumerate(row):
                cell_to_search = cell if case_sensitive else cell.lower()
                if search_term in cell_to_search:
                    results.append((row_idx, col_idx, cell))

        return results

    # =============================================================================
    # Validation
    # =============================================================================

    def verify_table_cell_value(
        self,
        row_index,
        col_index,
        expected_value,
        table_data=None,
        exact_match=True,
        table_locator=None,
        **kwargs,
    ):
        """Verify that a cell contains the expected value.

        Returns True if the cell matches, False otherwise.

        Arguments:
        - ``row_index``:      Row index (0-based, excluding header).
        - ``col_index``:      Column index (0-based).
        - ``expected_value``: Expected cell value.
        - ``table_data``:     Pre-fetched table data (optional).
        - ``exact_match``:    If True, use exact match; if False, use substring.
        - ``table_locator``:  Locator for get_table_data if table_data not given.

        Examples:
        | ${result}= | Verify Table Cell Value | 0 | 1 | file1.txt | table_locator=//Table |
        """
        cell_value = self.get_table_cell(
            row_index, col_index, table_data,
            table_locator=table_locator, **kwargs
        )

        if cell_value is None:
            return False

        if exact_match:
            return cell_value == expected_value
        else:
            return expected_value in cell_value

    def verify_table_row_exists(
        self,
        col_name,
        value,
        table_data=None,
        exact_match=True,
        table_locator=None,
        **kwargs,
    ):
        """Verify that a row exists with specified value in column.

        Returns True if such a row exists, False otherwise.

        Arguments:
        - ``col_name``:      Column name to check.
        - ``value``:         Value to look for.
        - ``table_data``:    Pre-fetched table data (optional).
        - ``exact_match``:   If True, use exact match; if False, use substring.
        - ``table_locator``: Locator for get_table_data if table_data not given.

        Examples:
        | ${exists}= | Verify Table Row Exists | Name | file1.txt | table_locator=//Table |
        """
        row = self.find_table_row_by_value(
            col_name, value, table_data, exact_match,
            table_locator=table_locator, **kwargs
        )
        return row is not None

    def verify_table_column_values(
        self,
        col_name,
        expected_values,
        table_data=None,
        exact_match=True,
        ordered=False,
        table_locator=None,
        **kwargs,
    ):
        """Verify column contains expected values.

        Arguments:
        - ``col_name``:        Column name to verify.
        - ``expected_values``: List of expected values.
        - ``table_data``:      Pre-fetched table data (optional).
        - ``exact_match``:     If True, values must match exactly.
        - ``ordered``:         If True, order must match as well.
        - ``table_locator``:   Locator for get_table_data if table_data not given.

        Examples:
        | @{expected}= | Create List   | file1.txt | file2.txt |
        | ${result}=   | Verify Table Column Values | Name | ${expected} | table_locator=//Table |
        """
        actual_values = self.get_table_column(
            col_name=col_name, table_data=table_data,
            table_locator=table_locator, **kwargs
        )

        if ordered:
            if len(actual_values) != len(expected_values):
                return False
            return actual_values == expected_values
        else:
            if exact_match:
                return set(expected_values).issubset(set(actual_values))
            else:
                for expected in expected_values:
                    if not any(expected in actual for actual in actual_values):
                        return False
                return True

    def verify_table_sort_order(
        self,
        col_name=None,
        col_index=None,
        order="ASC",
        table_data=None,
        case_sensitive=False,
        table_locator=None,
        **kwargs,
    ):
        """Verify that a column is sorted in the specified order.

        Arguments:
        - ``col_name``:       Column name to check.
        - ``col_index``:      Column index (if col_name not provided).
        - ``order``:          ``ASC`` or ``DESC``.
        - ``table_data``:     Pre-fetched table data (optional).
        - ``case_sensitive``: Whether to consider case in sorting.
        - ``table_locator``:  Locator for get_table_data if table_data not given.

        Examples:
        | ${sorted}= | Verify Table Sort Order | col_name=Name | order=ASC | table_locator=//Table |
        """
        column_values = self.get_table_column(
            col_name=col_name, col_index=col_index,
            table_data=table_data, table_locator=table_locator, **kwargs
        )

        if not column_values:
            return True

        if case_sensitive:
            sorted_values = sorted(column_values)
        else:
            sorted_values = sorted(column_values, key=str.lower)

        if order.upper() == "DESC":
            sorted_values.reverse()

        return column_values == sorted_values

    # =============================================================================
    # Conversion
    # =============================================================================

    def table_to_dict_list(
        self,
        table_data=None,
        table_locator=None,
        **kwargs,
    ):
        """Convert table data to list of dictionaries.

        Each dictionary uses column headers as keys.

        Arguments:
        - ``table_data``:    Pre-fetched table data (optional).
        - ``table_locator``: Locator for get_table_data if table_data not given.

        Examples:
        | ${dicts}= | Table To Dict List | table_locator=//Table |
        | Log       | ${dicts}[0][Name]  |                       |
        """
        if table_data is None:
            table_data = self.get_table_data(
                table_locator=table_locator, **kwargs
            )

        if not table_data or len(table_data) <= 1:
            return []

        headers = table_data[0]
        result = []

        for row in table_data[1:]:
            row_dict = {}
            for idx, header in enumerate(headers):
                value = row[idx] if idx < len(row) else ""
                row_dict[header] = value
            result.append(row_dict)

        return result

    def get_table_value_from_row(
        self,
        base_col_name,
        base_value,
        target_col_name,
        table_data=None,
        exact_match=True,
        table_locator=None,
        **kwargs,
    ):
        """Get value from target column in row where base column matches.

        Common pattern: find row where Column A = X, return value from Column B.

        Arguments:
        - ``base_col_name``:   Column to search in.
        - ``base_value``:      Value to match.
        - ``target_col_name``: Column to get value from.
        - ``table_data``:      Pre-fetched table data (optional).
        - ``exact_match``:     If True, use exact match.
        - ``table_locator``:   Locator for get_table_data if table_data not given.

        Examples:
        | ${size}= | Get Table Value From Row | Name | file1.txt | Size | table_locator=//Table |
        """
        if table_data is None:
            table_data = self.get_table_data(
                table_locator=table_locator, **kwargs
            )

        if not table_data or len(table_data) <= 1:
            return None

        headers = table_data[0]

        try:
            base_col_idx = headers.index(base_col_name)
            target_col_idx = headers.index(target_col_name)
        except ValueError:
            return None

        for row in table_data[1:]:
            if base_col_idx < len(row):
                cell_value = row[base_col_idx]
                matches = (
                    cell_value == base_value
                    if exact_match
                    else base_value in cell_value
                )
                if matches and target_col_idx < len(row):
                    return row[target_col_idx]

        return None



    # =============================================================================
    # Interaction
    # =============================================================================

    def get_table_row_element(
        self,
        row_index=None,
        col_name=None,
        col_value=None,
        table_locator=None,
        header_locator=None,
        header_attribute=None,
        row_locator=None,
        cell_locator=None,
        cell_attribute=None,
        timeout=None,
    ):
        """Get the actual UI element for a table row.

        Specify either ``row_index`` (0-based) or a ``col_name``/``col_value``
        pair to locate the row by matching value.

        When using ``col_name``/``col_value``, the header and cell locator
        arguments are required so that the table data can be read.

        Arguments:
        - ``row_index``:        Row index (0-based), or None to search by value.
        - ``col_name``:         Column name to search (used with col_value).
        - ``col_value``:        Value to search for in column.
        - ``table_locator``:    Locator for the table element.
        - ``header_locator``:   Locator for header items (required for col_name search).
        - ``header_attribute``: Attribute for headers (required for col_name search).
        - ``row_locator``:      Locator for row items.
        - ``cell_locator``:     Locator for cell items (required for col_name search).
        - ``cell_attribute``:   Attribute for cells (required for col_name search).
        - ``timeout``:          Optional timeout in seconds.

        Examples:
        | ${el}= | Get Table Row Element | row_index=0      | table_locator=//Table |
        | ${el}= | Get Table Row Element | col_name=Name    | col_value=file1.txt | table_locator=//Table |
        """
        if row_index is not None:
            row_index = int(row_index)
            table_element = self.appium_get_element(
                table_locator, required=False, timeout=timeout
            )
            if not table_element:
                return None

            row_elements = self.appium_get_elements_in_element(
                table_element, row_locator, timeout=timeout
            )
            if not row_elements or row_index >= len(row_elements):
                return None

            return row_elements[row_index]

        elif col_name and col_value:
            table_data = self.get_table_data(
                table_locator=table_locator,
                header_locator=header_locator,
                header_attribute=header_attribute,
                row_locator=row_locator,
                cell_locator=cell_locator,
                cell_attribute=cell_attribute,
                timeout=timeout,
            )

            if not table_data or len(table_data) <= 1:
                return None

            headers = table_data[0]
            try:
                col_idx = headers.index(col_name)
            except ValueError:
                return None

            matching_index = None
            for idx, row in enumerate(table_data[1:]):
                if col_idx < len(row) and row[col_idx] == col_value:
                    matching_index = idx
                    break

            if matching_index is None:
                return None

            return self.get_table_row_element(
                row_index=matching_index,
                table_locator=table_locator,
                row_locator=row_locator,
                timeout=timeout,
            )

        return None

    def click_table_row(
        self,
        row_index=None,
        col_name=None,
        col_value=None,
        table_locator=None,
        row_locator=None,
        button="left",
        timeout=None,
    ):
        """Click on a table row.

        Specify either ``row_index`` or ``col_name``/``col_value`` to identify the row.
        ``button`` can be ``left``, ``right``, or ``double``.

        Arguments:
        - ``row_index``:     Row index (0-based), or None to search by value.
        - ``col_name``:      Column name to search (used with col_value).
        - ``col_value``:     Value to search for in column.
        - ``table_locator``: Locator for the table element.
        - ``row_locator``:   Locator for row items.
        - ``button``:        Click type: ``left``, ``right``, or ``double``.
        - ``timeout``:       Optional timeout in seconds.

        Examples:
        | Click Table Row | row_index=0 | table_locator=//Table |
        | Click Table Row | col_name=Name | col_value=file1.txt | button=double | table_locator=//Table |
        """
        if button not in ("left", "right", "double"):
            raise ValueError(
                f"Invalid button type: {button}. Must be 'left', 'right', or 'double'"
            )

        row_element = self.get_table_row_element(
            row_index=row_index,
            col_name=col_name,
            col_value=col_value,
            table_locator=table_locator,
            row_locator=row_locator,
            timeout=timeout,
        )

        if not row_element:
            return None

        self._perform_click(row_element, button)
        return row_element

    def click_table_cell(
        self,
        row_index,
        col_index,
        table_locator=None,
        row_locator=None,
        cell_locator=None,
        button="left",
        timeout=None,
    ):
        """Click on a specific cell in the table.

        Arguments:
        - ``row_index``:     Row index (0-based).
        - ``col_index``:     Column index (0-based).
        - ``table_locator``: Locator for the table element.
        - ``row_locator``:   Locator for row items.
        - ``cell_locator``:  Locator for cell items.
        - ``button``:        Click type: ``left``, ``right``, or ``double``.
        - ``timeout``:       Optional timeout in seconds.

        Examples:
        | Click Table Cell | 0 | 1 | table_locator=//Table |
        """
        row_index = int(row_index)
        col_index = int(col_index)

        if button not in ("left", "right", "double"):
            raise ValueError(
                f"Invalid button type: {button}. Must be 'left', 'right', or 'double'"
            )

        row_element = self.get_table_row_element(
            row_index=row_index,
            table_locator=table_locator,
            row_locator=row_locator,
            timeout=timeout,
        )
        if not row_element:
            return None

        cell_elements = self.appium_get_elements_in_element(
            row_element, cell_locator, timeout=timeout
        )
        if not cell_elements or col_index >= len(cell_elements):
            return None

        cell_element = cell_elements[col_index]
        self._perform_click(cell_element, button)
        return cell_element

    def get_table_cell_element(
        self,
        row_index,
        col_index,
        table_locator=None,
        row_locator=None,
        cell_locator=None,
        timeout=None,
    ):
        """Get the actual UI element for a specific cell.

        Arguments:
        - ``row_index``:     Row index (0-based).
        - ``col_index``:     Column index (0-based).
        - ``table_locator``: Locator for the table element.
        - ``row_locator``:   Locator for row items.
        - ``cell_locator``:  Locator for cell items.
        - ``timeout``:       Optional timeout in seconds.

        Examples:
        | ${cell}= | Get Table Cell Element | 0 | 1 | table_locator=//Table |
        """
        row_index = int(row_index)
        col_index = int(col_index)

        row_element = self.get_table_row_element(
            row_index=row_index,
            table_locator=table_locator,
            row_locator=row_locator,
            timeout=timeout,
        )
        if not row_element:
            return None

        cell_elements = self.appium_get_elements_in_element(
            row_element, cell_locator, timeout=timeout
        )
        if not cell_elements or col_index >= len(cell_elements):
            return None

        return cell_elements[col_index]

    def select_table_rows(
        self,
        row_indices,
        table_locator=None,
        row_locator=None,
        use_ctrl=True,
        timeout=None,
    ):
        """Select multiple rows using Ctrl+Click for multi-select.

        Arguments:
        - ``row_indices``:   List of row indices to select.
        - ``table_locator``: Locator for the table element.
        - ``row_locator``:   Locator for row items.
        - ``use_ctrl``:      If True, use Ctrl+Click for multi-select.
        - ``timeout``:       Optional timeout in seconds.

        Examples:
        | @{indices}= | Create List       | 0 | 2 | 3 |
        | Select Table Rows | ${indices}  | table_locator=//Table |
        """
        selected = []

        for idx_pos, row_index in enumerate(row_indices):
            row_element = self.get_table_row_element(
                row_index=int(row_index),
                table_locator=table_locator,
                row_locator=row_locator,
                timeout=timeout,
            )
            if not row_element:
                continue

            if idx_pos == 0 or not use_ctrl:
                self.appium_click(row_element)
            else:
                self.appium_begin_action_chain()
                self.appium_chain_key_down("CONTROL")
                self.appium_chain_click(row_element)
                self.appium_chain_key_up("CONTROL")
                self.appium_chain_perform()

            selected.append(row_element)

        return selected

    # =============================================================================
    # Private helpers
    # =============================================================================

    def _perform_click(self, element, button="left"):
        """Perform a click on element using the specified button type."""
        if button == "left":
            self.appium_click(element)
        elif button == "right":
            self.appium_action_context_click(element)
        elif button == "double":
            self.appium_action_double_click(element)
