"""Controller Boolean logic and adversarial-condition tests."""

from __future__ import annotations

import itertools

from controller_logic import (
    ControllerInput,
    DNAState,
    Mode,
    base_truth_table,
    evaluate_controller,
    validate_direction_factor_assignment,
)


def condition(mode: Mode, state: DNAState, channel: str) -> ControllerInput:
    """Create one one-hot input condition."""
    return ControllerInput(
        mode,
        state,
        channel == "A",
        channel == "B",
        channel == "C",
    )


def test_forward_truth_table() -> None:
    """Forward outputs require the exact state and one chemical input."""
    for state, channel in (
        (DNAState.STATE_0, "A"),
        (DNAState.STATE_1, "B"),
        (DNAState.STATE_2, "C"),
    ):
        output = evaluate_controller(condition(Mode.FORWARD, state, channel))
        assert output.integrases == (channel,)
        assert output.rdfs == ()
        assert not output.blocked


def test_reverse_truth_table() -> None:
    """Reverse outputs coexpress only the cognate integrase and RDF."""
    for state, channel in (
        (DNAState.STATE_3, "C"),
        (DNAState.STATE_2, "B"),
        (DNAState.STATE_1, "A"),
    ):
        output = evaluate_controller(condition(Mode.REVERSE, state, channel))
        assert output.integrases == (channel,)
        assert output.rdfs == (channel,)
        assert not output.blocked


def test_no_input_and_simultaneous_inputs_fail_closed() -> None:
    """No-input and multi-input cases command no new enzyme."""
    for mode, state in itertools.product(Mode, DNAState):
        assert evaluate_controller(ControllerInput(mode, state, False, False, False)).blocked
        assert evaluate_controller(ControllerInput(mode, state, True, True, False)).blocked
        assert evaluate_controller(ControllerInput(mode, state, True, True, True)).blocked


def test_premature_channel_is_blocked() -> None:
    """The next channel cannot fire before the required state."""
    assert evaluate_controller(condition(Mode.FORWARD, DNAState.STATE_0, "B")).blocked
    assert evaluate_controller(condition(Mode.FORWARD, DNAState.STATE_1, "C")).blocked


def test_lost_state_signal_fails_closed() -> None:
    """State-signal loss produces no commanded output in the Boolean model."""
    output = evaluate_controller(
        ControllerInput(
            Mode.FORWARD,
            DNAState.STATE_0,
            True,
            False,
            False,
            lost_state_signal=True,
        )
    )
    assert output.blocked
    assert output.integrases == ()


def test_residual_and_leak_are_not_silently_solved() -> None:
    """Residual protein and leak are preserved as experimental unknowns."""
    output = evaluate_controller(
        ControllerInput(
            Mode.FORWARD,
            DNAState.STATE_0,
            False,
            False,
            False,
            residual_integrase="A",
            residual_rdf="A",
            promoter_leak="B",
        )
    )
    assert output.blocked
    assert len(output.experimental_unknowns) == 3


def test_wrong_rdf_assignment_rejected() -> None:
    """Only cognate channel-to-RDF assignments pass."""
    assert validate_direction_factor_assignment("A", "A")
    assert not validate_direction_factor_assignment("A", "B")


def test_complete_truth_table_size() -> None:
    """Two modes by four states by eight drug combinations are present."""
    assert len(base_truth_table()) == 64
