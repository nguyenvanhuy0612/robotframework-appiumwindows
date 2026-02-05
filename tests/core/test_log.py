import inspect

class TestLog:
    def _log_activation(self):
        """Auto-log the calling method's name and arguments."""
        frame = inspect.currentframe().f_back
        method_name = frame.f_code.co_name.replace('_', ' ').title()
        arg_names, varargs_name, keywords_name, local_vars = inspect.getargvalues(frame)
        
        args_list = []
        
        # explicit args
        for arg in arg_names:
            if arg != 'self':
                args_list.append(f"{arg}='{local_vars[arg]}'")
        
        # *args
        if varargs_name:
            varargs = local_vars[varargs_name]
            for arg in varargs:
                args_list.append(f"'{arg}'")
        
        # **kwargs
        if keywords_name:
            keywords = local_vars[keywords_name]
            for key, value in keywords.items():
                args_list.append(f"{key}='{value}'")

        arg_str = ", ".join(args_list)
        print(f"{method_name} {arg_str}")

    def test_log(self, locator, timeout=None, reference=None, *args, **kwargs):
        self._log_activation()

if __name__ == "__main__":
    test_log = TestLog()
    test_log.test_log("locator", "timeout", "reference", "arg1", "arg2", key1="value1", key2="value2")
    test_log.test_log(locator="//Button", timeout="10", reference="reference", arg1="arg1", arg2="arg2", key1="value1", key2="value2", key3="value3")
    test_log.test_log(locator="//Button", reference="reference")
    test_log.test_log("//Button", reference="reference")
    
    # Additional tests
    print("-" * 20)
    print("Testing positional args only:")
    test_log.test_log("param1", "10s", "ref1")
    
    print("Testing mixed positional and kwargs:")
    test_log.test_log("param1", timeout="20s", extra_param="extra")
    
    print("Testing varargs:")
    test_log.test_log("param1", None, None, "vararg1", "vararg2")
    
    print("Testing structure with special chars:")
    test_log.test_log("xpath=//div[@id='foo']", handle_error=True)

