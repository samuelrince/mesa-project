#!/usr/bin/env python3


class CoupleValue:
    """CoupleValue class.
    This class implements a couple value used in argument object.

    attr:
        criterion_name:
        value:
    """

    def __init__(self, criterion_name, value):
        """Creates a new couple value.
        """
        self.__criterion_name = criterion_name
        self.__value = value

    def __repr__(self):
        return f'CoupleValue({self.__criterion_name}: {self.__value})'

    @property
    def criterion_name(self):
        return self.__criterion_name

    @property
    def value(self):
        return self.__value
