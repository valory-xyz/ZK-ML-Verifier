# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This package contains round behaviours of VerifierAbciApp."""

import json
from abc import ABC
from typing import Generator, Set, Type, cast

from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.verifier_abci.models import Params
from packages.valory.skills.verifier_abci.payloads import (
    SynchronizeVerificationsPayload, PerformVerificationsPayload,
)
from packages.valory.skills.verifier_abci.rounds import (
    VerifierAbciApp,
    SynchronizeVerificationsRound,
    SynchronizedData, PerformVerificationsRound,
)
from packages.valory.skills.verifier_abci.zkml import zkml_verify


class VerifierBaseBehaviour(BaseBehaviour, ABC):
    """Base behaviour for the verifier_abci skill."""

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, super().params)


class SynchronizeVerificationsBehaviour(VerifierBaseBehaviour):
    """
    Synchronizes verification requests across all agents.

    When there are multiple agents in the service not all agents have necessarily the same data before synchronizing.
    """

    matching_round: Type[AbstractRound] = SynchronizeVerificationsRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            new_verifications = json.dumps(
                self.context.state.new_verifications
            )  # no sorting needed here as there is no consensus over this data
            sender = self.context.agent_address
            payload = SynchronizeVerificationsPayload(
                sender=sender, new_verifications=new_verifications
            )
            self.context.logger.info(f"New verifications = {new_verifications}")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class PerformVerificationsBehaviour(VerifierBaseBehaviour):
    """Performs one of the received verification requests."""

    matching_round: Type[AbstractRound] = PerformVerificationsRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            request = self.synchronized_data.request_in_priority()
            result = zkml_verify(request)
            sender = self.context.agent_address
            payload = PerformVerificationsPayload(
                sender=sender, result=result
            )
            self.context.logger.info(f"Verification result for request {request}: {result}")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class VerifierRoundBehaviour(AbstractRoundBehaviour):
    """ProposalCollectorRoundBehaviour"""

    initial_behaviour_cls = SynchronizeVerificationsBehaviour
    abci_app_cls = VerifierAbciApp
    behaviours: Set[Type[BaseBehaviour]] = [
        SynchronizeVerificationsBehaviour,
        PerformVerificationsBehaviour,
    ]
