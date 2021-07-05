from distutils.util import strtobool


class PythonToSQLConverter:
    @staticmethod
    def convert(arg=None):
        if arg is None:
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
