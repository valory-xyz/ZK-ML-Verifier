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

"""This package contains the rounds of VerifierAbciApp."""

import json
from enum import Enum
from typing import Dict, Optional, Set, Tuple, cast, List

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AppState,
    BaseSynchronizedData,
    CollectDifferentUntilAllRound,
    DegenerateRound,
    EventToTimeout,
    TransactionNotValidError,
    get_name,
    VotingRound,
    DeserializedCollection,
    CollectionRound,
)
from packages.valory.skills.verifier_abci.payloads import (
    SynchronizeVerificationsPayload,
    PerformVerificationsPayload,
)


class Event(Enum):
    """VerifierAbciApp Events"""

    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    DONE = "done"
    NEGATIVE = "negative"
    NONE = "None"


class SynchronizedData(BaseSynchronizedData):
    """
    Class to represent the synchronized data.

    This data is replicated by the tendermint application.
    """

    @property
    def verification_requests(self) -> List[VerificationRequestType]:
        """Get the verification requests."""
        return cast(list, self.db.get("verification_requests", []))

    @property
    def request_in_priority(self) -> VerificationRequestType:
        """Get the next verification request in priority."""
        return self.verification_requests.pop()

    @property
    def done_requests(self) -> List[VerificationRequestType]:
        """Get the done verification requests."""
        return cast(list, self.db.get("done_requests", []))

    @property
    def participant_to_verification_vote(self) -> DeserializedCollection:
        """Get the participant to verification vote mapping."""
        serialized = self.db.get_strict("participant_to_verification_vote")
        deserialized = CollectionRound.deserialize_collection(serialized)
        return cast(DeserializedCollection, deserialized)


class SynchronizeVerificationsRound(CollectDifferentUntilAllRound):
    """SynchronizeDelegations"""

    payload_class = SynchronizeVerificationsPayload
    synchronized_data_class = SynchronizedData

    def check_payload(self, payload: SynchronizeVerificationsPayload) -> None:
        """Check Payload"""
        new = payload.values
        existing = [
            collection_payload.values
            for collection_payload in self.collection.values()
            # do not consider empty verification requests
            if json.loads(collection_payload.json["new_verifications"])
        ]

        if payload.sender not in self.collection and new in existing:
            raise TransactionNotValidError(
                f"`CollectDifferentUntilAllRound` encountered a value {new!r} that already exists. "
                f"All values: {existing}"
            )

        if payload.round_count != self.synchronized_data.round_count:
            raise TransactionNotValidError(
                f"Expected round count {self.synchronized_data.round_count} and got {payload.round_count}."
            )

        if payload.sender in self.collection:
            raise TransactionNotValidError(
                f"sender {payload.sender} has already sent value for round: {self.round_id}"
            )

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.collection_threshold_reached:
            verification_requests = cast(
                SynchronizedData, self.synchronized_data
            ).verification_requests

            for payload in self.collection.values():
                # Add this agent's new verifications
                new_verifications = json.loads(payload.json["new_verifications"])
                verification_requests.extend(new_verifications)

            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                **{
                    get_name(
                        SynchronizedData.verification_requests
                    ): verification_requests,
                },
            )
            return synchronized_data, Event.DONE

        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY

        return None


class PerformVerificationsRound(VotingRound):
    """PerformVerificationsRound"""

    payload_class = PerformVerificationsPayload
    done_event = Event.DONE
    negative_event = Event.NEGATIVE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = get_name(SynchronizedData.participant_to_verification_vote)
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        res = super().end_block()
        if res is None:
            return
        _, event = res

        if event == Event.DONE:
            synchronized_data = cast(SynchronizedData, self.synchronized_data)
            verification_requests = synchronized_data.verification_requests
            done_request = verification_requests.pop()
            done_requests = synchronized_data.done_requests
            done_requests.append(done_request)
            synchronized_data = self.synchronized_data.update(
                synchronized_data_class=self.synchronized_data_class,
                **{
                    get_name(
                        SynchronizedData.verification_requests
                    ): verification_requests,
                    get_name(SynchronizedData.done_requests): done_requests,
                },
            )
            return synchronized_data, self.done_event


class FinishedVerificationRound(DegenerateRound):
    """FinishedProposalRound"""


class VerifierAbciApp(AbciApp[Event]):
    """VerifierAbciApp"""

    initial_round_cls: AppState = SynchronizeVerificationsRound
    initial_states: Set[AppState] = {SynchronizeVerificationsRound}
    transition_function: AbciAppTransitionFunction = {
        SynchronizeVerificationsRound: {
            Event.DONE: PerformVerificationsRound,
            Event.NO_MAJORITY: SynchronizeVerificationsRound,
            Event.ROUND_TIMEOUT: SynchronizeVerificationsRound,
        },
        PerformVerificationsRound: {
            Event.DONE: FinishedVerificationRound,
            Event.NO_MAJORITY: PerformVerificationsRound,
            Event.ROUND_TIMEOUT: PerformVerificationsRound,
        },
        FinishedVerificationRound: {},
    }
    final_states: Set[AppState] = {
        FinishedVerificationRound,
    }
    event_to_timeout: EventToTimeout = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    cross_period_persisted_keys: Set[str] = {
        get_name(SynchronizedData.verification_requests),
        get_name(SynchronizedData.done_requests),
    }
    db_pre_conditions: Dict[AppState, Set[str]] = {
        SynchronizeVerificationsRound: set(),
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinishedVerificationRound: {
            get_name(SynchronizedData.verification_requests),
            get_name(SynchronizedData.done_requests),
            get_name(SynchronizedData.participant_to_verification_vote),
        },
    }
