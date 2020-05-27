from enum import Enum

class Error(Exception):
    pass


class Runner(Enum):
    SGX         = 1
    NoSGX       = 2

    @staticmethod
    def from_str(str):
        lower_str = str.lower()

        if lower_str == "sgx":
            return Runner.SGX
        if lower_str == "nosgx":
            return Runner.NoSGX

        raise Error("No matching runner for {}".format(str))


    def to_str(self):
        if self == Runner.SGX:
            return "runner_sgx"
        if self == Runner.NoSGX:
            return "runner_nosgx"


    def has_hardcoded_key(self):
        if self == Runner.NoSGX:
            return True

        return False
