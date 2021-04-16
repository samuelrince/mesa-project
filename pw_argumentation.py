import random

from mesa import Model
from mesa.time import RandomActivation
from typing import Dict, Optional

from communication.agent.CommunicatingAgent import CommunicatingAgent
from communication.message.MessageService import MessageService
from communication.message.Message import Message
from communication.message.MessagePerformative import MessagePerformative
from communication.preferences.Preferences import Preferences
from communication.preferences.CriterionName import CriterionName
from communication.preferences.CriterionValue import CriterionValue
from communication.preferences.Item import Item
from communication.preferences.Value import Value
from communication.arguments.Argument import Argument
from communication.arguments.CoupleValue import CoupleValue


class ArgumentAgent(CommunicatingAgent):
    """ ArgumentAgent which inherit from CommunicatingAgent.
    """
    def __init__(self, unique_id, model, name, arg_mode='classic'):
        super().__init__(unique_id, model, name)
        self.preference = None
        self.arguments: Dict[str, Argument] = dict()
        self.arg_mode = arg_mode

    def step(self):
        super().step()

        # Get last messages
        messages = self.get_new_messages()

        # Process all message in order
        if len(messages) > 0:
            for msg in messages:
                self._process_message(msg)

    def _process_message(self, message: Message):
        performative = message.get_performative()
        other_id = message.get_exp()

        # The agent receives a proposition
        if performative == MessagePerformative.PROPOSE:
            item = message.get_content()

            # If the agent likes the item
            if self.get_preference().is_item_among_top_10_percent(item, self.model.items):
                self.send_message(Message(self.get_name(), other_id, MessagePerformative.ACCEPT, item))

            # If the agent dislikes the item -> Create an argument
            else:
                self.arguments[item.get_name()] = self._generate_argument(boolean_decision=False, item=item)
                self.send_message(Message(self.get_name(), other_id, MessagePerformative.ASK_WHY, item))

        # The other agent asked why this item -> Create an argument
        elif performative == MessagePerformative.ASK_WHY:
            item = message.get_content()
            self.arguments[item.get_name()] = self._generate_argument(boolean_decision=True, item=item)
            premise = self.arguments[item.get_name()].pick_best_couple_value()
            self.send_message(Message(self.get_name(), other_id, MessagePerformative.ARGUE, (item, premise)))

        # The agent respond to an argue message
        elif performative == MessagePerformative.ARGUE:
            content = message.get_content()
            item = content[0]
            premise = self.arguments[item.get_name()].pick_best_couple_value()

            if premise is not None:
                if self.arg_mode == 'classic':
                    # Classic mode and one premise => the agent argues the item
                    self.send_message(Message(self.get_name(), other_id, MessagePerformative.ARGUE, (item, premise)))

                elif self.arg_mode == 'short':
                    # Short mode and one premise => the agent checks if his premise is at an equivalent level
                    if self._check_premise_level(premise.value, content[1].value):
                        # If the premise is better or equal => argue
                        self.send_message(Message(self.get_name(), other_id, MessagePerformative.ARGUE, (item,
                                                                                                         premise)))
                    elif self.arguments[item.get_name()].decision():
                        # The proposing agent argue again
                        self.send_message(
                            Message(self.get_name(), other_id, MessagePerformative.ARGUE, (item, premise)))
                    else:
                        if not self.arguments[item.get_name()].decision():
                            # The receiving agent "give up" and accepts the item
                            self.send_message(Message(self.get_name(), other_id, MessagePerformative.ACCEPT, item))
                        else:
                            # Refuses item
                            pass
            else:
                if not self.arguments[item.get_name()].decision():
                    # Classic mode and no premise => the agent accepts the item
                    self.send_message(Message(self.get_name(), other_id, MessagePerformative.ACCEPT, item))
                else:
                    # Refuses item
                    pass

        # The other agent has accepted the proposition -> commit
        elif performative == MessagePerformative.ACCEPT:
            item = message.get_content()
            self.send_message(Message(self.get_name(), other_id, MessagePerformative.COMMIT, item))

        elif performative == MessagePerformative.COMMIT:
            pass

    def _generate_argument(self, boolean_decision: bool, item: Item):
        """
        Generate an argument. An argument is stored in each opposing agent (one in favor, the other against). This
        distinctions is done with the boolean decision.
        """
        argument = Argument(boolean_decision, item)

        # Add CoupleValue
        if boolean_decision:
            for couple_value_premise in self.listing_supporting_proposal(item):
                argument.add_premiss_couple_values(couple_value_premise.criterion_name, couple_value_premise.value)
        else:
            for couple_value_premise in self.listing_attacking_proposal(item):
                argument.add_premiss_couple_values(couple_value_premise.criterion_name, couple_value_premise.value)

        return argument

    def _check_premise_level(self, me, other):
        """
        Check if the agent can answer with better or equal argument in terms of value
        """
        me = str(me)
        other = str(other)
        if 'VERY' in other:
            if 'VERY' in me:
                return True
            else:
                return False
        return False

    def get_preference(self) -> Preferences:
        return self.preference

    def generate_preferences(self, item):
        """
        Generate random preferences over an item on all criteria.
        """
        # If preferences object is not set, we instantiate it.
        if self.preference is None:
            self.preference = Preferences()
            self.preference.set_criterion_name_list([*CriterionName])

        # Generate random value over all criteria
        for criterion in CriterionName:
            self.preference.add_criterion_value(CriterionValue(item, criterion, random.choice([*Value])))

    def listing_supporting_proposal(self, item: Item):
        """
        List supporting arguments in favor of an item. Outputs GOOD and VERY_GOOD value criterion.
        """
        criterion_list = list()
        for criterion_name in self.preference.get_criterion_name_list():
            criterion_value = self.preference.get_value(item, criterion_name)
            if criterion_value in [Value.VERY_GOOD, Value.GOOD]:
                criterion_list.append(CoupleValue(criterion_name, criterion_value))
        return criterion_list

    def listing_attacking_proposal(self, item: Item):
        """
        List attacking arguments against an item. Outputs BAD and VERY_BAD value criterion.
        """
        criterion_list = list()
        for criterion_name in self.preference.get_criterion_name_list():
            criterion_value = self.preference.get_value(item, criterion_name)
            if criterion_value in [Value.VERY_BAD, Value.BAD]:
                criterion_list.append(CoupleValue(criterion_name, criterion_value))
        return criterion_list


class ArgumentModel(Model):
    """ ArgumentModel which inherit from Model.
    """
    def __init__(self, n_agent: int = 2, argument_mode: Optional[str] = None):
        super(ArgumentModel, self).__init__()
        self.schedule = RandomActivation(self)
        self.__messages_service = MessageService(self.schedule)
        if argument_mode is None:
            argument_mode = 'classic'
        self.__arg_mode = argument_mode

        # Creating items
        diesel_engine = Item("Diesel Engine", "A super cool diesel engine")
        electric_engine = Item("Electric Engine", "A very quiet engine")
        hydrogen_engine = Item("Hydrogen Engine", "An engine that produces water")
        self.items = [diesel_engine, electric_engine, hydrogen_engine]

        # Create agents
        for i in range(n_agent):
            agent = ArgumentAgent(i+1, self, f"agent_{i+1}", arg_mode=argument_mode)
            agent.generate_preferences(diesel_engine)
            agent.generate_preferences(electric_engine)
            agent.generate_preferences(hydrogen_engine)
            self.schedule.add(agent)

        self.running = True

    def step(self):
        self.__messages_service.dispatch_messages()
        self.schedule.step()


if __name__ == "__main__":
    # Fixing seed this will change the preferences of agents
    # Please change the seed to observe other argumentation patterns
    seed = 1
    random.seed(seed)

    n_steps = 15    # Number of steps to run the model
    argument_model = ArgumentModel(n_agent=2, argument_mode='classic')

    agent_1: ArgumentAgent = argument_model.schedule.agents[0]
    agent_2: ArgumentAgent = argument_model.schedule.agents[1]

    # Give agent 1 item 1
    agent_1.send_message(Message(agent_1.get_name(), agent_2.get_name(), MessagePerformative.PROPOSE,
                                 argument_model.items[1]))

    # Run n_steps in the model
    for i in range(n_steps):
        argument_model.step()
