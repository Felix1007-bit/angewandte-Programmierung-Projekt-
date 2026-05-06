"""
Day 6 – Klassenbasierter Decorator
Zeigt, wie Decorators als Klassen implementiert werden können.
"""

import time
import functools


# ─────────────────────────────────────────
# Einfachster klassenbasierter Decorator
# ─────────────────────────────────────────

class repeat:
    """
    Decorator, der eine Funktion n-mal ausführt.

    Verwendung:
        @repeat(3)
        def say_hello():
            print("Hallo!")
    """

    def __init__(self, times: int):
        self.times = times

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = None
            for _ in range(self.times):
                result = func(*args, **kwargs)
            return result
        return wrapper


# ─────────────────────────────────────────
# Timer-Decorator als Klasse
# ─────────────────────────────────────────

class timer:
    """
    Decorator, der die Ausführungszeit einer Funktion misst und ausgibt.

    Verwendung:
        @timer()
        def slow_function():
            time.sleep(1)
    """

    def __init__(self, label: str = ""):
        self.label = label

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = self.label or func.__name__
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            print(f"[timer] {name} dauerte {elapsed:.4f}s")
            return result
        return wrapper


# ─────────────────────────────────────────
# Logger-Decorator als Klasse
# ─────────────────────────────────────────

class log_calls:
    """
    Decorator, der jeden Aufruf einer Funktion protokolliert
    (Name, Argumente, Rückgabewert).

    Verwendung:
        @log_calls()
        def add(a, b):
            return a + b
    """

    def __init__(self, show_result: bool = True):
        self.show_result = show_result

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            arg_str = ", ".join(
                [repr(a) for a in args] +
                [f"{k}={repr(v)}" for k, v in kwargs.items()]
            )
            print(f"[log] {func.__name__}({arg_str}) aufgerufen")
            result = func(*args, **kwargs)
            if self.show_result:
                print(f"[log] {func.__name__} → {repr(result)}")
            return result
        return wrapper


# ─────────────────────────────────────────
# Demo – alle Decorators ausprobieren
# ─────────────────────────────────────────

@repeat(3)
def say_hello(name: str = "Welt"):
    print(f"Hallo, {name}!")


@timer(label="addiere")
def add(a: int, b: int) -> int:
    return a + b


@log_calls(show_result=True)
def multiply(a: int, b: int) -> int:
    return a * b


# Kombinierte Decorators (von unten nach oben ausgeführt)
@log_calls()
@timer()
def slow_add(a: int, b: int) -> int:
    time.sleep(0.05)
    return a + b


if __name__ == "__main__":
    print("=" * 40)
    print("  @repeat(3)")
    print("=" * 40)
    say_hello("Felix")

    print("\n" + "=" * 40)
    print("  @timer()")
    print("=" * 40)
    result = add(10, 32)
    print(f"Ergebnis: {result}")

    print("\n" + "=" * 40)
    print("  @log_calls()")
    print("=" * 40)
    multiply(6, 7)

    print("\n" + "=" * 40)
    print("  @log_calls + @timer kombiniert")
    print("=" * 40)
    slow_add(3, 4)
