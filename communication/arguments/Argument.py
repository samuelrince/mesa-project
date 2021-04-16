#!/usr/bin/env python3

from communication.arguments.Comparison import Comparison
from communication.arguments.CoupleValue import CoupleValue


class Argument:
    """Argument class.
    This class implements an argument used in the negotiation.

    attr:
        decision:
        item:
        comparison_list:
        couple_values_list:
    """

    def __init__(self, boolean_decision, item):
        """Creates a new Argument.
        """
        self.__decision = boolean_decision
        self.__item = item.get_name()
        self.__comparison_list = []
        self.__couple_values_list = []
        self.__used_couple_value_list = []

    def add_premiss_comparison(self, criterion_name_1, criterion_name_2):
        """Adds a premiss comparison in the comparison list.
        """
        self.__comparison_list.append(Comparison(criterion_name_1, criterion_name_2))

    def add_premiss_couple_values(self, criterion_name, value):
        """Add a premiss couple values in the couple values list.
        """
        self.__couple_values_list.append(CoupleValue(criterion_name, value))
        self.__couple_values_list = sorted(self.__couple_values_list,
                                           key=lambda x: x.value.value,
                                           reverse=self.__decision)

    def get_couple_value_list(self):
        return self.__couple_values_list

    def pick_best_couple_value(self):
        best = None
        if len(self.__couple_values_list) > 0:
            best = self.__couple_values_list.pop(0)
            self.__used_couple_value_list.append(best)
        return best

    def pick_best_comparison(self):
        pass

    def decision(self):
        return self.__decision
