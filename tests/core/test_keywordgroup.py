import unittest
from AppiumLibrary.keywords.keywordgroup import KeywordGroup, ignore_on_fail

class MockKeywordGroup(KeywordGroup):
    def __init__(self):
        self._run_on_failure_count = 0
    
    def _run_on_failure(self):
        print('run_on_failure called')
        self._run_on_failure_count += 1
        
    def successful_keyword(self):
        return "Success"
        
    def failing_keyword(self):
        raise ValueError("Intentional Failure")
        
    @ignore_on_fail
    def ignored_keyword(self):
        raise ValueError("Ignored Failure")
        
    def _private_keyword(self):
        raise ValueError("Private Failure")

    def nested_failing_keyword(self):
        self.failing_keyword()

class TestKeywordGroup(unittest.TestCase):
    
    def setUp(self):
        self.kw_group = MockKeywordGroup()

    def test_successful_keyword_not_intercepted(self):
        """Verify successful keywords return normally without triggering run_on_failure"""
        result = self.kw_group.successful_keyword()
        self.assertEqual(result, "Success")
        self.assertEqual(self.kw_group._run_on_failure_count, 0)

    def test_failing_keyword_triggers_run_on_failure(self):
        """Verify failing keywords trigger _run_on_failure"""
        with self.assertRaises(ValueError):
            self.kw_group.failing_keyword()
        self.assertEqual(self.kw_group._run_on_failure_count, 1)

    def test_ignored_keyword_does_not_trigger(self):
        """Verify @ignore_on_fail prevents _run_on_failure execution"""
        with self.assertRaises(ValueError):
            self.kw_group.ignored_keyword()
        self.assertEqual(self.kw_group._run_on_failure_count, 0)

    def test_private_keyword_not_decorated(self):
        """Verify private methods (starting with _) are not decorated"""
        with self.assertRaises(ValueError):
            self.kw_group._private_keyword()
        self.assertEqual(self.kw_group._run_on_failure_count, 0)

    def test_nested_failure_runs_once(self):
        """Verify _run_on_failure is called only once for nested failing keywords"""
        with self.assertRaises(ValueError):
            self.kw_group.nested_failing_keyword()
        # Should be 1, not 2
        self.assertEqual(self.kw_group._run_on_failure_count, 1)

    def test_invoke_original(self):
        """Verify _invoke_original calls the undecorated method"""
        # We need a new instance to test this cleanly or reuse existing
        # failing_keyword is decorated. calling it directly runs failure logic.
        # calling it via invoke_original should simple raise without failure logic.
        
        with self.assertRaises(ValueError):
            self.kw_group._invoke_original("failing_keyword")
            
        # Since we invoked original, the wrapper wasn't executed, so no count increment
        self.assertEqual(self.kw_group._run_on_failure_count, 0)

if __name__ == '__main__':
    unittest.main()
