class OverriddenCommandError(Exception):
    def __init__(self, message):
        super(OverriddenCommandError, self).__init__(message)


class OverriddenParserError(Exception):
    def __init__(self, message):
        super(OverriddenParserError, self).__init__(message)

