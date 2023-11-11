from typing import Any, Tuple, Optional

from stimpl.expression import *
from stimpl.types import *
from stimpl.errors import *

"""
Interpreter State
"""


class State(object):
    def __init__(self, variable_name: str, variable_value: Expr, variable_type: Type, next_state: 'State') -> None:
        self.variable_name = variable_name
        self.value = (variable_value, variable_type)
        self.next_state = next_state

    def copy(self) -> 'State':
        variable_value, variable_type = self.value
        return State(self.variable_name, variable_value, variable_type, self.next_state)

    def set_value(self, variable_name, variable_value, variable_type):
        return State(variable_name, variable_value, variable_type, self)

    def get_value(self, variable_name) -> Any:
        # recursively check for values
        if self.variable_name == variable_name:
            return self.value
        else:
            return self.next_state.get_value(variable_name)
    
    def __repr__(self) -> str:
        return f"{self.variable_name}: {self.value}, " + repr(self.next_state)


class EmptyState(State):
    def __init__(self):
        pass

    def copy(self) -> 'EmptyState':
        return EmptyState()

    def get_value(self, variable_name) -> None:
        return None

    def __repr__(self) -> str:
        return ""


"""
Main evaluation logic!
"""


def evaluate(expression: Expr, state: State) -> Tuple[Optional[Any], Type, State]:
    match expression:
        case Ren():
            return (None, Unit(), state)

        case IntLiteral(literal=l):
            return (l, Integer(), state)

        case FloatingPointLiteral(literal=l):
            return (l, FloatingPoint(), state)

        case StringLiteral(literal=l):
            return (l, String(), state)

        case BooleanLiteral(literal=l):
            return (l, Boolean(), state)

        case Print(to_print=to_print):
            printable_value, printable_type, new_state = evaluate(
                to_print, state)

            match printable_type:
                case Unit():
                    print("Unit")
                case _:
                    print(f"{printable_value}")

            return (printable_value, printable_type, new_state)

        case Sequence(exprs=exprs) | Program(exprs=exprs):
            # got help from Mitch Koski regarding Sequence() implementation (in class review session on 11/8)
            new_value, new_type, new_state = None, Unit(), state

            # iterates through every expr and passes it through evaluate()
            # to get new_state, and then returns new_value, new_type, and new_state
            for expr in exprs:
                new_value, new_type, new_state = evaluate(expr, new_state)
            
            return(new_value, new_type, new_state)

        case Variable(variable_name=variable_name):
            value = state.get_value(variable_name)
            if value == None:
                raise InterpSyntaxError(
                    f"Cannot read from {variable_name} before assignment.")
            variable_value, variable_type = value
            return (variable_value, variable_type, state)

        case Assign(variable=variable, value=value):

            value_result, value_type, new_state = evaluate(value, state)

            variable_from_state = new_state.get_value(variable.variable_name)
            _, variable_type = variable_from_state if variable_from_state else (
                None, None)

            if value_type != variable_type and variable_type != None:
                raise InterpTypeError(f"""Mismatched types for Assignment:
            Cannot assign {value_type} to {variable_type}""")

            new_state = new_state.set_value(
                variable.variable_name, value_result, value_type)
            return (value_result, value_type, new_state)

        case Add(left=left, right=right):
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Add:
            Cannot add {left_type} to {right_type}""")

            match left_type:
                case Integer() | String() | FloatingPoint():
                    result = left_result + right_result
                case _:
                    raise InterpTypeError(f"""Cannot add {left_type}s""")

            return (result, left_type, new_state)

        case Subtract(left=left, right=right):
            # copy and paste of Add case with several things changed
            # evaluates both the left and right results/types/states
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            # if both left_type and right_type aren't the same type,
            # we have an InterpTypeError since we have mismatched types
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Subtract:
            Cannot subtract {left_type} to {right_type}""")

            match left_type:
                # strings cannot be used in subtraction, this happens for addition only
                # string addition is concatenation, we cannot subtract/multiply/divide strings though
                # but we can have Integers and FloatingPoints
                case Integer() | FloatingPoint():
                    result = left_result - right_result
                case _:
                    raise InterpTypeError(f"""Cannot subtract {left_type}s""")

            return (result, left_type, new_state)

        case Multiply(left=left, right=right):
            # copy and paste of Subtract case with several things changed
            # evaluates both the left and right results/types/states
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            # if both left_type and right_type aren't the same type,
            # we have an InterpTypeError since we have mismatched types
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Multiply:
            Cannot multiply {left_type} to {right_type}""")

            match left_type:
                # strings cannot be used in multiplication, this happens for addition only
                # string addition is concatenation, we cannot subtract/multiply/divide strings though
                # but we can have Integers and FloatingPoints
                case Integer() | FloatingPoint():
                    result = left_result * right_result
                case _:
                    raise InterpTypeError(f"""Cannot multiply {left_type}s""")

            return (result, left_type, new_state)

        case Divide(left=left, right=right):
            # copy and paste of Multiply case with several things changed
            # evaluates both the left and right results/types/states
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            # needs to check for divide by zero by checking if right_result
            # is 0, since all operands are evaluated left-to-right
            # raises InterpMathError if a divide by zero occurs
            if right_result == 0:
                raise InterpMathError("Attempted to divide by zero.")
            
            # if both left_type and right_type aren't the same type,
            # we have an InterpTypeError since we have mismatched types
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Divide:
            Cannot divide {left_type} to {right_type}""")

            match left_type:
                # strings cannot be used in division, this happens for addition only
                # string addition is concatenation, we cannot subtract/multiply/divide strings though
                # need separate cases for FloatingPoint and Integer division as they evaluate differently!
                case FloatingPoint():
                    # single slash is for floating point division
                    result = left_result / right_result
                case Integer():
                    # double slashes are for integer division
                    result = left_result // right_result
                case _:
                    raise InterpTypeError(f"""Cannot divide {left_type}s""")

            return (result, left_type, new_state)

        case And(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for And:
            Cannot evaluate {left_type} and {right_type}""")
            match left_type:
                case Boolean():
                    result = left_value and right_value
                case _:
                    raise InterpTypeError(
                        "Cannot perform logical and on non-boolean operands.")

            return (result, left_type, new_state)

        case Or(left=left, right=right):
            # copy and paste of And case with several things changed
            # evaluates both the left and right results/types/states
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            # if both left_type and right_type aren't the same type,
            # we have an InterpTypeError since we have mismatched types
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Or:
            Cannot evaluate {left_type} or {right_type}""")

            match left_type:
                # this is a Boolean operation and cannot be performed on other types
                case Boolean():
                    result = left_value or right_value
                case _:
                    raise InterpTypeError(
                        "Cannot perform logical or on non-boolean operands.")

            return (result, left_type, new_state)

        case Not(expr=expr):
            # copy and paste of Or case with several things changed
            # no need to compare left/right as logical not works on the whole expression
            # so there will be no need to check for mismatched types

            # evaluates new_value, new_type, and new_state
            # this is similar to the Sequence() implementation
            new_value, new_type, new_state = evaluate(expr, state)
            match new_type:
                # this is a Boolean operation and cannot be performed on other types
                case Boolean():
                    result = not new_value
                case _:
                    raise InterpTypeError(
                        "Cannot perform logical not on non-boolean operands.")

            return (result, new_type, new_state)

        case If(condition=condition, true=true, false=false):
            # evaluates the condition value, type, and state
            condition_value, condition_type, new_state = evaluate(condition, state)
            match condition_type:
                case Boolean():
                    # copy and pasted from Or case and changed left/right to true/false
                    # must be a Boolean or this will not work
                    # evaluates both the true and false results/types/states
                    true_value, true_type, new_state = evaluate(true, new_state)
                    false_value, false_type, new_state = evaluate(false, new_state)
                    
                    # if the condition is met, execute the "then" part of the if
                    # statement and return the true value/type/state
                    if condition_value == True:
                        return (true_value, true_type, new_state)
                    
                    # however, if the condition is not met, execute the "else" part of the
                    # if statement and return false value/type/state
                    return (false_value, false_type, new_state)
                case _:
                    raise InterpTypeError("Cannot perform if on non-boolean operands.")


        case Lt(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lt:
            Cannot compare {left_type} and {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value < right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform < on {left_type} type.")

            return (result, Boolean(), new_state)

        case Lte(left=left, right=right):
            # copy and paste of Lt case with several things changed
            # evaluates both the left and right results/types/states
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            # if both left_type and right_type aren't the same type,
            # we have an InterpTypeError since we have mismatched types
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lte:
            Cannot compare {left_type} and {right_type}""")

            # can be done with Integers, Booleans, Strings, FloatingPoints, and Units
            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value <= right_value
                case Unit():
                    # this needs to be true as two Ren units are equivalent
                    result = True
                case _:
                    raise InterpTypeError(
                        f"Cannot perform <= on {left_type} type.")

            return (result, Boolean(), new_state)

        case Gt(left=left, right=right):
            # copy and paste of the Lt case with several things changed
            # evaluates both the left and right results/types/states
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            # if both left_type and right_type aren't the same type,
            # we have an InterpTypeError since we have mismatched types
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Gt:
            Cannot compare {left_type} and {right_type}""")

            # can be done with Integers, Booleans, Strings, FloatingPoints, and Units
            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value > right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform > on {left_type} type.")

            return (result, Boolean(), new_state)

        case Gte(left=left, right=right):
            # copy and paste of Lte case with several things changed
            # evaluates both the left and right results/types/states
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            # if both left_type and right_type aren't the same type,
            # we have an InterpTypeError since we have mismatched types
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Gte:
            Cannot compare {left_type} and {right_type}""")

            # can be done with Integers, Booleans, Strings, FloatingPoints, and Units
            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value >= right_value
                case Unit():
                    # this needs to be true as two Ren units are equivalent
                    result = True
                case _:
                    raise InterpTypeError(
                        f"Cannot perform >= on {left_type} type.")

            return (result, Boolean(), new_state)

        case Eq(left=left, right=right):
            # copy and paste of Gte case with several things changed
            # evaluates both the left and right results/types/states
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            # if both left_type and right_type aren't the same type,
            # we have an InterpTypeError since we have mismatched types
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Eq:
            Cannot compare {left_type} and {right_type}""")

            # can be done with Integers, Booleans, Strings, FloatingPoints, and Units
            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value == right_value
                case Unit():
                    # this needs to be true as two Ren units are equivalent
                    result = True
                case _:
                    raise InterpTypeError(
                        f"Cannot perform == on {left_type} type.")

            return (result, Boolean(), new_state)

        case Ne(left=left, right=right):
            # copy and paste of Eq case with several things changed
            # evaluates both the left and right results/types/states
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            # if both left_type and right_type aren't the same type,
            # we have an InterpTypeError since we have mismatched types
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Ne:
            Cannot compare {left_type} and {right_type}""")

            # can be done with Integers, Booleans, Strings, FloatingPoints, and Units
            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value != right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform != on {left_type} type.")

            return (result, Boolean(), new_state)

        case While(condition=condition, body=body):
            # copy pasted from If case with several things changed
            # evaluates the condition value, type, and state
            condition_value, condition_type, new_state = evaluate(condition, state)
            match condition_type:
                case Boolean():
                    # needs to be a Boolean, otherwise this will not work
                    while condition_value:
                        # evaluates the new_value, new_type, and new_state using the body
                        # then evaluates the condition_value, type, and new_state using the condition
                        # this performs the body, then checks to see if the condition is met or not
                        new_value, new_type, new_state = evaluate(body, new_state)
                        condition_value, condition_type, new_state = evaluate(condition, new_state)
                case _:
                    raise InterpTypeError("Cannot perform while on non-boolean operands.")
            
            # value and type of a while loop are false and Boolean
            return (False, Boolean(), new_state)

        case _:
            raise InterpSyntaxError("Unhandled!")
    pass


def run_stimpl(program, debug=False):
    state = EmptyState()
    program_value, program_type, program_state = evaluate(program, state)

    if debug:
        print(f"program: {program}")
        print(f"final_value: ({program_value}, {program_type})")
        print(f"final_state: {program_state}")

    return program_value, program_type, program_state
