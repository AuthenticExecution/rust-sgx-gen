from enum import Enum

class Error(Exception):
    pass


class Runner(Enum):
    SGX             = 1
    NATIVE          = 2

    @staticmethod
    def from_str(str):
        lower_str = str.lower()

        if lower_str == "sgx":
            return Runner.SGX
        if lower_str == "native":
            return Runner.NATIVE

        raise Error("No matching runner for {}".format(str))


    def to_str(self):
        if self == Runner.SGX:
            return "runner_sgx"
        if self == Runner.NATIVE:
            return "runner_native"


    def has_hardcoded_key(self):
        if self == Runner.NATIVE:
            return True

        return False
