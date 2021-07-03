from distutils.util import strtobool


class PythonToSQLConverter:
    @staticmethod
    def convert(arg=None):
        if not arg:
            return ""
        arg = str(arg)
        try:
            return int(arg)
        except:
            try:
                return float(arg)
            except:
                try:
                    return bool(strtobool(arg))
                except:
                    return f"'{arg}'"
