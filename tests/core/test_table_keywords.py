
import unittest
import sys
import os
sys.path.append(os.getcwd())
from unittest.mock import MagicMock, patch, call
from AppiumLibrary.keywords._table import _TableKeywords
from selenium.webdriver.remote.webelement import WebElement
import appium.webdriver


class TestTableKeywords(unittest.TestCase):
    """Unit tests for _TableKeywords."""

    def setUp(self):
        self.builtin_patcher = patch('AppiumLibrary.keywords._element.BuiltIn')
        self.mock_builtin_class = self.builtin_patcher.start()
        self.mock_builtin_instance = self.mock_builtin_class.return_value
        self.mock_builtin_instance.get_variable_value.return_value = "5"

        self.tk = _TableKeywords()
        self.tk._timeout_in_secs = 5
        self.tk._poll_sleep_between_wait = 0.1

        # Mock mixin methods
        self.tk._get_platform = MagicMock(return_value='windows')
        self.tk.log_source = MagicMock()
        self.tk.get_source = MagicMock(return_value="<html></html>")
        self.tk._info = MagicMock()
        self.tk._debug = MagicMock()
        self.tk._warn = MagicMock()

        # Mock driver
        self.mock_driver = MagicMock(spec=appium.webdriver.Remote)
        self.tk._current_application = MagicMock(return_value=self.mock_driver)

        # Build mock table structure
        self._build_mock_table()

    def _build_mock_table(self):
        """Create mock elements simulating a table with headers and rows."""
        # Table element
        self.mock_table = MagicMock(spec=WebElement)

        # Header items
        self.mock_header1 = MagicMock(spec=WebElement)
        self.mock_header1.get_attribute.return_value = "Name"
        self.mock_header2 = MagicMock(spec=WebElement)
        self.mock_header2.get_attribute.return_value = "Size"
        self.mock_header3 = MagicMock(spec=WebElement)
        self.mock_header3.get_attribute.return_value = "Status"

        # Row elements
        self.mock_row1 = MagicMock(spec=WebElement)
        self.mock_row2 = MagicMock(spec=WebElement)
        self.mock_row3 = MagicMock(spec=WebElement)

        # Cell elements for rows
        self.mock_cell1_1 = MagicMock(spec=WebElement)
        self.mock_cell1_1.get_attribute.return_value = "file1.txt"
        self.mock_cell1_2 = MagicMock(spec=WebElement)
        self.mock_cell1_2.get_attribute.return_value = "1KB"
        self.mock_cell1_3 = MagicMock(spec=WebElement)
        self.mock_cell1_3.get_attribute.return_value = "Active"

        self.mock_cell2_1 = MagicMock(spec=WebElement)
        self.mock_cell2_1.get_attribute.return_value = "file2.txt"
        self.mock_cell2_2 = MagicMock(spec=WebElement)
        self.mock_cell2_2.get_attribute.return_value = "2KB"
        self.mock_cell2_3 = MagicMock(spec=WebElement)
        self.mock_cell2_3.get_attribute.return_value = "Inactive"

        self.mock_cell3_1 = MagicMock(spec=WebElement)
        self.mock_cell3_1.get_attribute.return_value = "file3.txt"
        self.mock_cell3_2 = MagicMock(spec=WebElement)
        self.mock_cell3_2.get_attribute.return_value = "3KB"
        self.mock_cell3_3 = MagicMock(spec=WebElement)
        self.mock_cell3_3.get_attribute.return_value = "Active"

        # Pre-built table data for methods that accept table_data
        self.sample_table_data = [
            ["Name", "Size", "Status"],
            ["file1.txt", "1KB", "Active"],
            ["file2.txt", "2KB", "Inactive"],
            ["file3.txt", "3KB", "Active"],
        ]

    def _setup_table_finding(self):
        """Configure mocks so get_table_data returns the sample table."""
        self.tk.appium_get_element = MagicMock(return_value=self.mock_table)
        self.tk.appium_get_element_attributes_in_element = MagicMock(
            side_effect=[
                ["Name", "Size", "Status"],       # headers
                ["file1.txt", "1KB", "Active"],    # row 1
                ["file2.txt", "2KB", "Inactive"],  # row 2
                ["file3.txt", "3KB", "Active"],    # row 3
            ]
        )
        self.tk.appium_get_elements_in_element = MagicMock(
            return_value=[self.mock_row1, self.mock_row2, self.mock_row3]
        )

    def tearDown(self):
        self.builtin_patcher.stop()

    # =================================================================
    # Core Data Retrieval
    # =================================================================

    def test_get_table_data(self):
        self._setup_table_finding()
        result = self.tk.get_table_data("//Table", "//Header/HeaderItem", "Name", "//ListItem", "//Text", "Name")
        self.assertEqual(len(result), 4)  # 1 header + 3 data rows
        self.assertEqual(result[0], ["Name", "Size", "Status"])
        self.assertEqual(result[1], ["file1.txt", "1KB", "Active"])

    def test_get_table_data_table_not_found(self):
        self.tk.appium_get_element = MagicMock(return_value=None)
        result = self.tk.get_table_data("//NonExistent", "//Header/HeaderItem", "Name", "//ListItem", "//Text", "Name")
        self.assertEqual(result, [])

    def test_get_table_data_no_headers(self):
        self.tk.appium_get_element = MagicMock(return_value=self.mock_table)
        self.tk.appium_get_element_attributes_in_element = MagicMock(return_value=[])
        result = self.tk.get_table_data("//Table", "//Header/HeaderItem", "Name", "//ListItem", "//Text", "Name")
        self.assertEqual(result, [])

    def test_get_table_headers(self):
        self.tk.appium_get_element = MagicMock(return_value=self.mock_table)
        self.tk.appium_get_element_attributes_in_element = MagicMock(
            return_value=["Name", "Size", "Status"]
        )
        result = self.tk.get_table_headers("//Table", "//Header/HeaderItem", "Name")
        self.assertEqual(result, ["Name", "Size", "Status"])

    def test_get_table_rows(self):
        self.tk.appium_get_element = MagicMock(return_value=self.mock_table)
        self.tk.appium_get_elements_in_element = MagicMock(
            return_value=[self.mock_row1, self.mock_row2]
        )
        self.tk.appium_get_element_attributes_in_element = MagicMock(
            side_effect=[
                ["file1.txt", "1KB", "Active"],
                ["file2.txt", "2KB", "Inactive"],
            ]
        )
        result = self.tk.get_table_rows("//Table", "//ListItem", "//Text", "Name")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ["file1.txt", "1KB", "Active"])

    def test_get_table_cell(self):
        result = self.tk.get_table_cell(0, 0, table_data=self.sample_table_data)
        self.assertEqual(result, "file1.txt")

    def test_get_table_cell_second_row(self):
        result = self.tk.get_table_cell(1, 1, table_data=self.sample_table_data)
        self.assertEqual(result, "2KB")

    def test_get_table_cell_out_of_bounds(self):
        result = self.tk.get_table_cell(10, 0, table_data=self.sample_table_data)
        self.assertIsNone(result)

    def test_get_table_row(self):
        result = self.tk.get_table_row(0, table_data=self.sample_table_data)
        self.assertEqual(result, ["file1.txt", "1KB", "Active"])

    def test_get_table_row_include_headers(self):
        result = self.tk.get_table_row(0, table_data=self.sample_table_data, include_headers=True)
        self.assertEqual(result, ["Name", "Size", "Status"])

    def test_get_table_column_by_name(self):
        result = self.tk.get_table_column(col_name="Name", table_data=self.sample_table_data)
        self.assertEqual(result, ["file1.txt", "file2.txt", "file3.txt"])

    def test_get_table_column_by_index(self):
        result = self.tk.get_table_column(col_index=1, table_data=self.sample_table_data)
        self.assertEqual(result, ["1KB", "2KB", "3KB"])

    def test_get_table_column_not_found(self):
        result = self.tk.get_table_column(col_name="Nonexistent", table_data=self.sample_table_data)
        self.assertEqual(result, [])

    def test_get_table_dimensions(self):
        result = self.tk.get_table_dimensions(table_data=self.sample_table_data)
        self.assertEqual(result, (3, 3))

    def test_get_table_dimensions_empty(self):
        result = self.tk.get_table_dimensions(table_data=[])
        self.assertEqual(result, (0, 0))

    # =================================================================
    # Search & Filter
    # =================================================================

    def test_find_table_row_by_value_exact(self):
        result = self.tk.find_table_row_by_value(
            "Name", "file2.txt", table_data=self.sample_table_data
        )
        self.assertEqual(result, ["file2.txt", "2KB", "Inactive"])

    def test_find_table_row_by_value_not_found(self):
        result = self.tk.find_table_row_by_value(
            "Name", "nonexistent.txt", table_data=self.sample_table_data
        )
        self.assertIsNone(result)

    def test_find_table_row_by_value_substring(self):
        result = self.tk.find_table_row_by_value(
            "Name", "file2", table_data=self.sample_table_data, exact_match=False
        )
        self.assertEqual(result, ["file2.txt", "2KB", "Inactive"])

    def test_find_table_rows_by_value(self):
        result = self.tk.find_table_rows_by_value(
            "Status", "Active", table_data=self.sample_table_data
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ["file1.txt", "1KB", "Active"])
        self.assertEqual(result[1], ["file3.txt", "3KB", "Active"])

    def test_find_table_rows_by_multiple_values_and(self):
        result = self.tk.find_table_rows_by_multiple_values(
            {"Status": "Active", "Name": "file3.txt"},
            table_data=self.sample_table_data,
            match_all=True,
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ["file3.txt", "3KB", "Active"])

    def test_find_table_rows_by_multiple_values_or(self):
        result = self.tk.find_table_rows_by_multiple_values(
            {"Status": "Inactive", "Name": "file1.txt"},
            table_data=self.sample_table_data,
            match_all=False,
        )
        self.assertEqual(len(result), 2)

    def test_search_table(self):
        result = self.tk.search_table("file", table_data=self.sample_table_data)
        self.assertEqual(len(result), 3)

    def test_search_table_case_insensitive(self):
        result = self.tk.search_table(
            "ACTIVE", table_data=self.sample_table_data, case_sensitive=False
        )
        # "Active" appears in 2 rows, "Inactive" contains "active" too
        self.assertEqual(len(result), 3)

    # =================================================================
    # Validation
    # =================================================================

    def test_verify_table_cell_value(self):
        result = self.tk.verify_table_cell_value(
            0, 0, "file1.txt", table_data=self.sample_table_data
        )
        self.assertTrue(result)

    def test_verify_table_cell_value_mismatch(self):
        result = self.tk.verify_table_cell_value(
            0, 0, "wrong.txt", table_data=self.sample_table_data
        )
        self.assertFalse(result)

    def test_verify_table_row_exists(self):
        result = self.tk.verify_table_row_exists(
            "Name", "file1.txt", table_data=self.sample_table_data
        )
        self.assertTrue(result)

    def test_verify_table_row_exists_not(self):
        result = self.tk.verify_table_row_exists(
            "Name", "missing.txt", table_data=self.sample_table_data
        )
        self.assertFalse(result)

    def test_verify_table_column_values(self):
        result = self.tk.verify_table_column_values(
            "Name", ["file1.txt", "file3.txt"], table_data=self.sample_table_data
        )
        self.assertTrue(result)

    def test_verify_table_column_values_ordered(self):
        result = self.tk.verify_table_column_values(
            "Name",
            ["file1.txt", "file2.txt", "file3.txt"],
            table_data=self.sample_table_data,
            ordered=True,
        )
        self.assertTrue(result)

    def test_verify_table_sort_order_asc(self):
        result = self.tk.verify_table_sort_order(
            col_name="Name", order="ASC", table_data=self.sample_table_data
        )
        self.assertTrue(result)

    def test_verify_table_sort_order_desc_false(self):
        result = self.tk.verify_table_sort_order(
            col_name="Name", order="DESC", table_data=self.sample_table_data
        )
        self.assertFalse(result)

    # =================================================================
    # Conversion
    # =================================================================

    def test_table_to_dict_list(self):
        result = self.tk.table_to_dict_list(table_data=self.sample_table_data)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["Name"], "file1.txt")
        self.assertEqual(result[0]["Size"], "1KB")
        self.assertEqual(result[1]["Status"], "Inactive")

    def test_table_to_dict_list_empty(self):
        result = self.tk.table_to_dict_list(table_data=[["Name"]])
        self.assertEqual(result, [])

    def test_get_table_value_from_row(self):
        result = self.tk.get_table_value_from_row(
            "Name", "file1.txt", "Size", table_data=self.sample_table_data
        )
        self.assertEqual(result, "1KB")

    def test_get_table_value_from_row_not_found(self):
        result = self.tk.get_table_value_from_row(
            "Name", "missing.txt", "Size", table_data=self.sample_table_data
        )
        self.assertIsNone(result)


    # =================================================================
    # Interaction
    # =================================================================

    def test_get_table_row_element_by_index(self):
        self.tk.appium_get_element = MagicMock(return_value=self.mock_table)
        self.tk.appium_get_elements_in_element = MagicMock(
            return_value=[self.mock_row1, self.mock_row2, self.mock_row3]
        )
        result = self.tk.get_table_row_element(row_index=1, table_locator="//Table")
        self.assertEqual(result, self.mock_row2)

    def test_get_table_row_element_by_index_out_of_bounds(self):
        self.tk.appium_get_element = MagicMock(return_value=self.mock_table)
        self.tk.appium_get_elements_in_element = MagicMock(
            return_value=[self.mock_row1]
        )
        result = self.tk.get_table_row_element(row_index=5, table_locator="//Table")
        self.assertIsNone(result)

    def test_click_table_row(self):
        self.tk.get_table_row_element = MagicMock(return_value=self.mock_row1)
        self.tk.appium_click = MagicMock()
        result = self.tk.click_table_row(row_index=0, table_locator="//Table")
        self.assertEqual(result, self.mock_row1)
        self.tk.appium_click.assert_called_once_with(self.mock_row1)

    def test_click_table_row_invalid_button(self):
        with self.assertRaises(ValueError):
            self.tk.click_table_row(row_index=0, button="middle", table_locator="//Table")

    def test_click_table_row_right(self):
        self.tk.get_table_row_element = MagicMock(return_value=self.mock_row1)
        self.tk.appium_action_context_click = MagicMock()
        result = self.tk.click_table_row(row_index=0, button="right", table_locator="//Table")
        self.assertEqual(result, self.mock_row1)
        self.tk.appium_action_context_click.assert_called_once_with(self.mock_row1)

    def test_click_table_row_double(self):
        self.tk.get_table_row_element = MagicMock(return_value=self.mock_row1)
        self.tk.appium_action_double_click = MagicMock()
        result = self.tk.click_table_row(row_index=0, button="double", table_locator="//Table")
        self.assertEqual(result, self.mock_row1)
        self.tk.appium_action_double_click.assert_called_once_with(self.mock_row1)

    def test_click_table_cell(self):
        self.tk.get_table_row_element = MagicMock(return_value=self.mock_row1)
        self.tk.appium_get_elements_in_element = MagicMock(
            return_value=[self.mock_cell1_1, self.mock_cell1_2, self.mock_cell1_3]
        )
        self.tk.appium_click = MagicMock()
        result = self.tk.click_table_cell(0, 1, table_locator="//Table")
        self.assertEqual(result, self.mock_cell1_2)
        self.tk.appium_click.assert_called_once_with(self.mock_cell1_2)

    def test_get_table_cell_element(self):
        self.tk.get_table_row_element = MagicMock(return_value=self.mock_row1)
        self.tk.appium_get_elements_in_element = MagicMock(
            return_value=[self.mock_cell1_1, self.mock_cell1_2]
        )
        result = self.tk.get_table_cell_element(0, 1, table_locator="//Table")
        self.assertEqual(result, self.mock_cell1_2)

    def test_select_table_rows(self):
        self.tk.get_table_row_element = MagicMock(
            side_effect=[self.mock_row1, self.mock_row2]
        )
        self.tk.appium_click = MagicMock()
        self.tk.appium_begin_action_chain = MagicMock()
        self.tk.appium_chain_key_down = MagicMock()
        self.tk.appium_chain_click = MagicMock()
        self.tk.appium_chain_key_up = MagicMock()
        self.tk.appium_chain_perform = MagicMock()
        result = self.tk.select_table_rows([0, 1], table_locator="//Table")
        self.assertEqual(len(result), 2)
        # First row: regular click
        self.tk.appium_click.assert_called_once_with(self.mock_row1)
        # Second row: Ctrl+Click via chain builder
        self.tk.appium_begin_action_chain.assert_called_once()
        self.tk.appium_chain_key_down.assert_called_once_with("CONTROL")
        self.tk.appium_chain_click.assert_called_once_with(self.mock_row2)
        self.tk.appium_chain_key_up.assert_called_once_with("CONTROL")
        self.tk.appium_chain_perform.assert_called_once()


if __name__ == "__main__":
    unittest.main()
