import inspect
import traceback
from functools import wraps
from datetime import datetime


# ============================================================
# TEST FRAMEWORK
# ============================================================

class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = False
        self.error = None
        self.duration = 0


class TestRunner:
    def __init__(self):
        self.tests = []
        self.results = []

    def register(self, function):
        self.tests.append(function)

    def run(self):
        self.results = []

        print("\n" + "=" * 60)
        print("                 MINI TEST FRAMEWORK")
        print("=" * 60)

        for test in self.tests:
            result = TestResult(test.__name__)

            start = datetime.now()

            try:
                test()
                result.passed = True

            except AssertionError as error:
                result.error = str(error) or "Assertion failed"

            except Exception as error:
                result.error = f"{type(error).__name__}: {error}"

            end = datetime.now()

            result.duration = (end - start).total_seconds()
            self.results.append(result)

            if result.passed:
                print(
                    f"PASS  {result.name:<35} "
                    f"{result.duration:.4f}s"
                )
            else:
                print(
                    f"FAIL  {result.name:<35} "
                    f"{result.duration:.4f}s"
                )
                print(f"      → {result.error}")

        self.summary()

    def summary(self):
        total = len(self.results)
        passed = sum(r.passed for r in self.results)
        failed = total - passed

        print("\n" + "-" * 60)
        print("TEST SUMMARY")
        print("-" * 60)

        print(f"Total tests : {total}")
        print(f"Passed      : {passed}")
        print(f"Failed      : {failed}")

        if total:
            percentage = (passed / total) * 100
            print(f"Success rate: {percentage:.2f}%")

        print("-" * 60)


# ============================================================
# ASSERTION SYSTEM
# ============================================================

class Assert:

    @staticmethod
    def equal(actual, expected, message=None):
        if actual != expected:
            raise AssertionError(
                message or
                f"Expected {expected!r}, got {actual!r}"
            )

    @staticmethod
    def not_equal(actual, expected, message=None):
        if actual == expected:
            raise AssertionError(
                message or
                f"Expected values to be different"
            )

    @staticmethod
    def true(value, message=None):
        if not value:
            raise AssertionError(
                message or f"Expected True, got {value!r}"
            )

    @staticmethod
    def false(value, message=None):
        if value:
            raise AssertionError(
                message or f"Expected False, got {value!r}"
            )

    @staticmethod
    def greater(actual, expected, message=None):
        if actual <= expected:
            raise AssertionError(
                message or
                f"Expected {actual!r} > {expected!r}"
            )

    @staticmethod
    def less(actual, expected, message=None):
        if actual >= expected:
            raise AssertionError(
                message or
                f"Expected {actual!r} < {expected!r}"
            )

    @staticmethod
    def contains(container, item, message=None):
        if item not in container:
            raise AssertionError(
                message or
                f"{item!r} was not found"
            )

    @staticmethod
    def raises(exception_type, function, *args, **kwargs):
        try:
            function(*args, **kwargs)

        except exception_type:
            return

        except Exception as error:
            raise AssertionError(
                f"Expected {exception_type.__name__}, "
                f"got {type(error).__name__}"
            )

        raise AssertionError(
            f"Expected {exception_type.__name__} "
            f"but no exception was raised"
        )


# ============================================================
# DECORATOR
# ============================================================

runner = TestRunner()


def test(function):
    @wraps(function)
    def wrapper():
        return function()

    runner.register(wrapper)
    return wrapper


# ============================================================
# SAMPLE APPLICATION
# ============================================================

def add(a, b):
    return a + b


def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")

    return a / b


def is_even(number):
    return number % 2 == 0


def reverse_text(text):
    return text[::-1]


def calculate_average(numbers):
    if not numbers:
        raise ValueError("List cannot be empty")

    return sum(numbers) / len(numbers)


# ============================================================
# TESTS
# ============================================================

@test
def test_add():
    Assert.equal(add(2, 3), 5)


@test
def test_add_negative_numbers():
    Assert.equal(add(-10, -5), -15)


@test
def test_division():
    Assert.equal(divide(10, 2), 5)


@test
def test_division_decimal():
    Assert.equal(divide(5, 2), 2.5)


@test
def test_division_by_zero():
    Assert.raises(ValueError, divide, 10, 0)


@test
def test_even_number():
    Assert.true(is_even(10))


@test
def test_odd_number():
    Assert.false(is_even(7))


@test
def test_reverse_text():
    Assert.equal(reverse_text("hello"), "olleh")


@test
def test_reverse_empty_text():
    Assert.equal(reverse_text(""), "")


@test
def test_average():
    Assert.equal(
        calculate_average([10, 20, 30]),
        20
    )


@test
def test_average_decimal():
    Assert.equal(
        calculate_average([5, 10]),
        7.5
    )


@test
def test_empty_average():
    Assert.raises(
        ValueError,
        calculate_average,
        []
    )


@test
def test_contains():
    Assert.contains(
        ["Python", "Java", "C++"],
        "Python"
    )


@test
def test_greater():
    Assert.greater(10, 5)


@test
def test_less():
    Assert.less(5, 10)


# ============================================================
# INTROSPECTION
# ============================================================

def show_registered_tests():
    print("\n" + "=" * 60)
    print("REGISTERED TESTS")
    print("=" * 60)

    for index, test_function in enumerate(runner.tests, 1):
        signature = inspect.signature(test_function)

        print(
            f"{index}. "
            f"{test_function.__name__}"
            f"{signature}"
        )


# ============================================================
# MANUAL TEST
# ============================================================

def manual_test():
    print("\n" + "=" * 60)
    print("MANUAL ASSERTION")
    print("=" * 60)

    try:
        value = int(input("Enter a number: "))

        Assert.greater(
            value,
            0,
            "Number must be greater than zero"
        )

        print("✓ Assertion passed!")

    except AssertionError as error:
        print(f"✗ Assertion failed: {error}")

    except ValueError:
        print("Please enter a valid integer.")


# ============================================================
# MAIN
# ============================================================

def main():

    while True:

        print("\n" + "=" * 60)
        print("             MINI TESTING FRAMEWORK")
        print("=" * 60)

        print("1. Run all tests")
        print("2. Show registered tests")
        print("3. Manual assertion")
        print("4. Exit")

        choice = input("\nChoose: ").strip()

        if choice == "1":
            runner.run()

        elif choice == "2":
            show_registered_tests()

        elif choice == "3":
            manual_test()

        elif choice == "4":
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()