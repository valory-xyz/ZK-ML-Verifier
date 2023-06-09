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

"""This module contains the shared state for the abci skill of ZKML."""

from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.zkml_abci.composition import ZKMLAbciApp
from packages.valory.skills.verifier_abci.models import (
    Params as VerifierAbciParams,
)
from packages.valory.skills.verifier_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.verifier_abci.rounds import (
    Event as ProposalCollectorEvent,
)
from packages.valory.skills.reset_pause_abci.rounds import Event as ResetPauseEvent
from packages.valory.skills.termination_abci.models import TerminationParams


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool

MARGIN = 5


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = ZKMLAbciApp

    def setup(self) -> None:
        """Set up."""
        super().setup()
        ZKMLAbciApp.event_to_timeout[
            ProposalCollectorEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        ZKMLAbciApp.event_to_timeout[
            ResetPauseEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        ZKMLAbciApp.event_to_timeout[
            ResetPauseEvent.RESET_AND_PAUSE_TIMEOUT
        ] = (self.context.params.reset_pause_duration + MARGIN)


class Params(VerifierAbciParams, VerifierAbciParams, TerminationParams):
    """A model to represent params for multiple abci apps."""
