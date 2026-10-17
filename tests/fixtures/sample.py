from dataclasses import dataclass


@dataclass
class Greeter:
    name: str

    def greet(self) -> str:
        return f"Hello, {self.name}!"


def build_greeter(name: str) -> Greeter:
    return Greeter(name)


message = build_greeter("world").greet()
broken: int = "not an int"
