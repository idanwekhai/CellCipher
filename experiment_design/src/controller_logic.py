"""Explicit controller truth tables for forward and reverse modes."""

from __future__ import annotations

import csv
import itertools
from dataclasses import asdict, dataclass
from enum import IntEnum, StrEnum
from pathlib import Path


class Mode(StrEnum):
    """Mutually exclusive controller records."""

    FORWARD = "forward"
    REVERSE = "reverse"


class DNAState(IntEnum):
    """Logical message states used by controller gates."""

    STATE_0 = 0
    STATE_1 = 1
    STATE_2 = 2
    STATE_3 = 3


FORWARD_EXPECTED = {
    DNAState.STATE_0: "A",
    DNAState.STATE_1: "B",
    DNAState.STATE_2: "C",
}
REVERSE_EXPECTED = {
    DNAState.STATE_3: "C",
    DNAState.STATE_2: "B",
    DNAState.STATE_1: "A",
}


@dataclass(frozen=True)
class ControllerInput:
    """One controller condition."""

    mode: Mode
    state: DNAState
    drug_a: bool
    drug_b: bool
    drug_c: bool
    residual_integrase: str | None = None
    residual_rdf: str | None = None
    incomplete_previous_transition: bool = False
    lost_state_signal: bool = False
    noncognate_state_signal: bool = False
    promoter_leak: str | None = None

    @property
    def active_drugs(self) -> set[str]:
        """Return the selected chemical channels."""
        return {
            channel
            for channel, active in zip(
                ("A", "B", "C"),
                (self.drug_a, self.drug_b, self.drug_c),
                strict=False,
            )
            if active
        }


@dataclass(frozen=True)
class ControllerOutput:
    """Boolean output plus explicitly separated uncertainty."""

    integrases: tuple[str, ...]
    rdfs: tuple[str, ...]
    blocked: bool
    boolean_logic_valid: bool
    regulatory_plausibility: str
    experimental_unknowns: tuple[str, ...]
    diagnostic: str


def evaluate_controller(condition: ControllerInput) -> ControllerOutput:
    """Evaluate one-hot drug AND exact-state logic."""
    expected = (FORWARD_EXPECTED if condition.mode == Mode.FORWARD else REVERSE_EXPECTED).get(
        condition.state
    )
    active = condition.active_drugs
    unknowns: list[str] = []
    if condition.residual_integrase:
        unknowns.append(f"residual integrase {condition.residual_integrase}")
    if condition.residual_rdf:
        unknowns.append(f"residual RDF {condition.residual_rdf}")
    if condition.promoter_leak:
        unknowns.append(f"promoter leak {condition.promoter_leak}")
    if condition.incomplete_previous_transition:
        unknowns.append("incomplete prior transition")
    if condition.noncognate_state_signal:
        unknowns.append("noncognate state signal")

    if condition.lost_state_signal:
        return ControllerOutput(
            (),
            (),
            True,
            True,
            "fail-closed Boolean abstraction; sequence implementation unresolved",
            (*unknowns, "state-signal loss"),
            "No state signal permits no commanded output.",
        )
    if len(active) != 1:
        return ControllerOutput(
            (),
            (),
            True,
            True,
            "one-hot input guard is a required, unresolved sequence interface",
            tuple(unknowns),
            "No input or simultaneous inputs are blocked.",
        )
    selected = next(iter(active))
    if expected is None or selected != expected:
        return ControllerOutput(
            (),
            (),
            True,
            True,
            "exact-state gate is a required, unresolved sequence interface",
            tuple(unknowns),
            f"Channel {selected} is not enabled in State {condition.state.value}.",
        )

    integrases = (selected,)
    rdfs = (selected,) if condition.mode == Mode.REVERSE else ()
    return ControllerOutput(
        integrases,
        rdfs,
        False,
        True,
        "sensor choices have E. coli precedent; composite state AND gates are unvalidated",
        tuple(unknowns),
        (
            f"Command Int{selected}."
            if condition.mode == Mode.FORWARD
            else f"Command Int{selected}+RDF{selected}."
        ),
    )


def validate_direction_factor_assignment(channel: str, rdf_channel: str) -> bool:
    """Return whether an RDF is assigned to its cognate integrase channel."""
    if channel not in {"A", "B", "C"} or rdf_channel not in {"A", "B", "C"}:
        return False
    return channel == rdf_channel


def base_truth_table() -> list[dict[str, object]]:
    """Enumerate every drug combination, mode, and logical state."""
    rows: list[dict[str, object]] = []
    for mode, state, drugs in itertools.product(
        Mode, DNAState, itertools.product((False, True), repeat=3)
    ):
        condition = ControllerInput(mode, state, *drugs)
        output = evaluate_controller(condition)
        rows.append(
            {
                **asdict(condition),
                "active_drugs": "".join(sorted(condition.active_drugs)) or "none",
                **asdict(output),
            }
        )
    return rows


def adversarial_truth_table() -> list[dict[str, object]]:
    """Enumerate required residual, leak, and state-signal perturbations."""
    rows = []
    scenarios = (
        {"residual_integrase": "A"},
        {"residual_rdf": "B"},
        {"incomplete_previous_transition": True},
        {"lost_state_signal": True},
        {"noncognate_state_signal": True},
        {"promoter_leak": "C"},
    )
    for mode in Mode:
        for state in DNAState:
            for scenario in scenarios:
                condition = ControllerInput(
                    mode,
                    state,
                    drug_a=False,
                    drug_b=False,
                    drug_c=False,
                    **scenario,
                )
                output = evaluate_controller(condition)
                rows.append(
                    {
                        "scenario": next(iter(scenario)),
                        **asdict(condition),
                        **asdict(output),
                    }
                )
    return rows


def export_truth_table(path: Path) -> None:
    """Write the complete controller truth table as TSV."""
    rows = base_truth_table() + adversarial_truth_table()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), delimiter="\t", extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)
