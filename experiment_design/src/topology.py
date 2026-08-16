"""Typed deterministic topology model for reversible LSI recombination."""

from __future__ import annotations

import hashlib
import itertools
from collections.abc import Iterable
from copy import deepcopy
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml

DNA_COMPLEMENT = str.maketrans("ACGT", "TGCA")
FORWARD_PROGRAM = ("A", "B", "C")
REVERSE_PROGRAM = ("C", "B", "A")


def reverse_complement(sequence: str) -> str:
    """Return the reverse complement of an unambiguous DNA sequence."""
    return sequence.translate(DNA_COMPLEMENT)[::-1]


class MoleculeType(StrEnum):
    """Supported molecule geometries."""

    LINEAR = "linear"
    CIRCULAR = "circular"


class SiteClass(StrEnum):
    """Large-serine-integrase substrate and product site classes."""

    B = "B"
    P = "P"
    L = "L"
    R = "R"
    INERT = "inert"


class Chemistry(StrEnum):
    """Idealized forward and reverse LSI chemistry."""

    INTEGRASE = "integrase"
    INTEGRASE_RDF = "integrase+rdf"


class Outcome(StrEnum):
    """Classified topological outcomes."""

    INVERSION = "inversion"
    DELETION = "deletion_excision"
    INTEGRATION = "integration_cointegrate"
    INVALID_CHEMISTRY = "invalid_chemistry"
    NO_SUBSTRATE = "no_substrate"
    AMBIGUOUS_SUBSTRATE = "ambiguous_substrate"


@dataclass(frozen=True)
class PairDefinition:
    """Exact attachment-site sequences and crossover decomposition."""

    channel: str
    system: str
    att_b: str
    att_p: str
    core: str
    b_core_index: int
    p_core_index: int
    source: str

    def __post_init__(self) -> None:
        for name, sequence, index in (
            ("att_b", self.att_b, self.b_core_index),
            ("att_p", self.att_p, self.p_core_index),
        ):
            if set(sequence) - set("ACGT"):
                raise ValueError(f"{self.channel} {name} contains ambiguous bases")
            if sequence[index : index + len(self.core)] != self.core:
                raise ValueError(f"{self.channel} {name} lacks core {self.core!r} at index {index}")

    @property
    def b_halves(self) -> tuple[str, str]:
        """Return B left and right recognition arms."""
        left = self.att_b[: self.b_core_index]
        right = self.att_b[self.b_core_index + len(self.core) :]
        return left, right

    @property
    def p_halves(self) -> tuple[str, str]:
        """Return P left and right recognition arms."""
        left = self.att_p[: self.p_core_index]
        right = self.att_p[self.p_core_index + len(self.core) :]
        return left, right

    def sequence_for(self, site_class: SiteClass) -> str:
        """Return the exact B, P, L, or R sequence."""
        b_left, b_right = self.b_halves
        p_left, p_right = self.p_halves
        arms = {
            SiteClass.B: (b_left, b_right),
            SiteClass.P: (p_left, p_right),
            SiteClass.L: (b_left, p_right),
            SiteClass.R: (p_left, b_right),
        }
        if site_class not in arms:
            raise ValueError(f"No active sequence for {site_class}")
        left, right = arms[site_class]
        return left + self.core + right


@dataclass
class Element:
    """One physically ordered DNA element."""

    identity: str
    kind: str
    canonical_sequence: str
    orientation: Literal[-1, 1] = 1
    channel: str | None = None
    site_origin: Literal["B", "P"] | None = None
    site_class: SiteClass | None = None
    accessible: bool = True
    note: str = ""

    @property
    def sequence(self) -> str:
        """Return sequence in its current physical orientation."""
        if self.orientation == 1:
            return self.canonical_sequence
        return reverse_complement(self.canonical_sequence)

    def label(self) -> str:
        """Return a stable human-readable state label."""
        sign = "+" if self.orientation == 1 else "-"
        if self.site_class is not None:
            return f"{self.identity}({self.site_class.value},{sign})"
        return f"{self.identity}{sign}"


@dataclass(frozen=True)
class Event:
    """One classified recombination attempt."""

    channel: str
    chemistry: Chemistry
    pair_state: str
    relative_orientation: str
    outcome: Outcome
    site_ids: tuple[str, ...]
    product_site_sequences: tuple[str, ...] = ()
    diagnostic: str = ""

    @property
    def intended(self) -> bool:
        """Return whether this event is an intended inversion."""
        return self.outcome == Outcome.INVERSION


@dataclass
class Molecule:
    """A complete typed DNA molecule."""

    name: str
    molecule_type: MoleculeType
    elements: list[Element]
    linearization_origin: str

    def __post_init__(self) -> None:
        if not self.elements:
            raise ValueError("A molecule must contain at least one element")
        if self.elements[0].identity != self.linearization_origin:
            raise ValueError("The first element must be the defined linearization origin")

    @property
    def sequence(self) -> str:
        """Return the complete sequence at the defined linearization point."""
        return "".join(element.sequence for element in self.elements)

    @property
    def sha256(self) -> str:
        """Return a stable SHA-256 sequence hash."""
        return hashlib.sha256(self.sequence.encode()).hexdigest()

    def element_offsets(self) -> dict[str, tuple[int, int]]:
        """Return physical half-open coordinates for all elements."""
        offsets: dict[str, tuple[int, int]] = {}
        cursor = 0
        for element in self.elements:
            end = cursor + len(element.sequence)
            offsets[element.identity] = (cursor, end)
            cursor = end
        return offsets

    def physical_labels(self) -> list[str]:
        """Return physical order and orientations."""
        return [element.label() for element in self.elements]

    def payload_order(self) -> list[str]:
        """Return payload order and orientation."""
        return [
            ("+" if element.orientation == 1 else "-") + element.identity
            for element in self.elements
            if element.kind == "payload"
        ]


def load_pair_definitions(config_path: Path) -> dict[str, PairDefinition]:
    """Load exact channel sites from channels.yaml."""
    raw = yaml.safe_load(config_path.read_text())
    definitions = {}
    for channel, item in raw["channels"].items():
        sites = item["sites"]
        definitions[channel] = PairDefinition(
            channel=channel,
            system=item["system"],
            att_b=sites["attB"].upper(),
            att_p=sites["attP"].upper(),
            core=sites["core"].upper(),
            b_core_index=sites["attB_core_index"],
            p_core_index=sites["attP_core_index"],
            source=sites["source"],
        )
    return definitions


def _deterministic_dna(label: str, length: int) -> str:
    """Create deterministic neutral fixture DNA from a label."""
    bases = "ACGT"
    output: list[str] = []
    counter = 0
    while len(output) < length:
        digest = hashlib.sha256(f"{label}:{counter}".encode()).digest()
        output.extend(bases[byte & 0b11] for byte in digest)
        counter += 1
    return "".join(output[:length])


def default_payloads(length: int = 96) -> dict[str, str]:
    """Return six deterministic, nonfunctional barcode candidates."""
    return {name: _deterministic_dna(f"payload:{name}:v1", length) for name in "ABCDEF"}


def build_initial_register(
    definitions: dict[str, PairDefinition],
    payloads: dict[str, str] | None = None,
) -> Molecule:
    """Build the required locus-independent State 0 register."""
    payloads = payloads or default_payloads()
    site_specs: dict[str, tuple[str, SiteClass, Literal[-1, 1], str]] = {
        "S1": ("A", SiteClass.B, 1, "B"),
        "S2": ("B", SiteClass.B, 1, "B"),
        "S3": ("C", SiteClass.B, 1, "B"),
        "S5": ("A", SiteClass.P, -1, "P"),
        "S6": ("C", SiteClass.P, -1, "P"),
        "S7": ("B", SiteClass.P, 1, "P"),
    }
    elements = [
        Element(
            "REGISTER_ORIGIN",
            "linearization_origin",
            _deterministic_dna("register-origin:v1", 48),
            note="Defined comparison and export origin; not a replication origin.",
        )
    ]
    for index, payload_name in enumerate("ABCDEF", start=1):
        site_id = f"S{index}"
        if site_id == "S4":
            elements.append(
                Element(
                    site_id,
                    "inert_boundary",
                    _deterministic_dna("inert-boundary:S4:v1", 48),
                    site_class=SiteClass.INERT,
                    accessible=False,
                    note="Inert logical boundary; not an attachment site.",
                )
            )
        else:
            channel, site_class, orientation, origin = site_specs[site_id]
            elements.append(
                Element(
                    identity=site_id,
                    kind="attachment_site",
                    canonical_sequence=definitions[channel].sequence_for(site_class),
                    orientation=orientation,
                    channel=channel,
                    site_origin=origin,  # type: ignore[arg-type]
                    site_class=site_class,
                )
            )
        elements.append(
            Element(
                payload_name,
                "payload",
                payloads[payload_name],
                note="Synthetic neutral barcode; no biological function claimed.",
            )
        )
    channel, site_class, orientation, origin = site_specs["S7"]
    elements.append(
        Element(
            identity="S7",
            kind="attachment_site",
            canonical_sequence=definitions[channel].sequence_for(site_class),
            orientation=orientation,
            channel=channel,
            site_origin=origin,  # type: ignore[arg-type]
            site_class=site_class,
        )
    )
    return Molecule(
        name="state_0",
        molecule_type=MoleculeType.LINEAR,
        elements=elements,
        linearization_origin="REGISTER_ORIGIN",
    )


def channel_sites(molecule: Molecule, channel: str) -> list[Element]:
    """Return every site assigned to one channel."""
    return [element for element in molecule.elements if element.channel == channel]


def pair_state(sites: Iterable[Element]) -> str:
    """Return BP, LR, or an explicit invalid state signature."""
    classes = sorted(
        element.site_class.value for element in sites if element.site_class is not None
    )
    if classes == ["B", "P"]:
        return "BP"
    if classes == ["L", "R"]:
        return "LR"
    return "".join(classes) or "none"


def relative_orientation(left: Element, right: Element) -> str:
    """Return antiparallel or parallel geometry."""
    return "antiparallel" if left.orientation != right.orientation else "parallel"


def classify_event(
    molecule: Molecule,
    channel: str,
    chemistry: Chemistry,
    definitions: dict[str, PairDefinition],
) -> Event:
    """Classify one idealized intramolecular recombination attempt."""
    sites = channel_sites(molecule, channel)
    site_ids = tuple(site.identity for site in sites)
    if len(sites) < 2:
        return Event(
            channel,
            chemistry,
            pair_state(sites),
            "undefined",
            Outcome.NO_SUBSTRATE,
            site_ids,
            diagnostic="Fewer than two cognate sites are present.",
        )
    if len(sites) > 2:
        return Event(
            channel,
            chemistry,
            pair_state(sites),
            "multiple",
            Outcome.AMBIGUOUS_SUBSTRATE,
            site_ids,
            diagnostic="More than two cognate sites create multiple possible pairings.",
        )
    state = pair_state(sites)
    geometry = relative_orientation(sites[0], sites[1])
    required = "BP" if chemistry == Chemistry.INTEGRASE else "LR"
    if state != required:
        return Event(
            channel,
            chemistry,
            state,
            geometry,
            Outcome.INVALID_CHEMISTRY,
            site_ids,
            diagnostic=f"{chemistry.value} requires {required}, observed {state}.",
        )
    outcome = Outcome.INVERSION if geometry == "antiparallel" else Outcome.DELETION
    definition = definitions[channel]
    product_classes = (
        (SiteClass.R, SiteClass.L)
        if chemistry == Chemistry.INTEGRASE
        else (SiteClass.B, SiteClass.P)
    )
    product_sequences = tuple(definition.sequence_for(site_class) for site_class in product_classes)
    return Event(
        channel,
        chemistry,
        state,
        geometry,
        outcome,
        site_ids,
        product_sequences,
        diagnostic=(
            "Antiparallel cognate sites invert the inclusive interval."
            if outcome == Outcome.INVERSION
            else "Parallel cognate sites form a deletion/excision substrate."
        ),
    )


def classify_intermolecular(
    left: Molecule,
    right: Molecule,
    channel: str,
    chemistry: Chemistry,
) -> Event:
    """Classify cognate sites on different molecules as integration risk."""
    sites = channel_sites(left, channel) + channel_sites(right, channel)
    state = pair_state(sites)
    return Event(
        channel=channel,
        chemistry=chemistry,
        pair_state=state,
        relative_orientation="intermolecular",
        outcome=Outcome.INTEGRATION,
        site_ids=tuple(site.identity for site in sites),
        diagnostic="Compatible sites on different molecules can form cointegrates.",
    )


def _update_products(
    molecule: Molecule,
    channel: str,
    chemistry: Chemistry,
    definition: PairDefinition,
) -> None:
    """Apply exact half-site product or substrate reconstruction."""
    for element in channel_sites(molecule, channel):
        if chemistry == Chemistry.INTEGRASE:
            next_class = SiteClass.R if element.site_origin == "B" else SiteClass.L
        else:
            next_class = SiteClass.B if element.site_origin == "B" else SiteClass.P
        element.site_class = next_class
        element.canonical_sequence = definition.sequence_for(next_class)


def apply_recombination(
    molecule: Molecule,
    channel: str,
    chemistry: Chemistry,
    definitions: dict[str, PairDefinition],
) -> Event:
    """Apply one inversion; non-inversion outcomes do not mutate the molecule."""
    event = classify_event(molecule, channel, chemistry, definitions)
    if event.outcome != Outcome.INVERSION:
        return event
    indices = [
        index for index, element in enumerate(molecule.elements) if element.channel == channel
    ]
    left, right = min(indices), max(indices)
    segment = deepcopy(molecule.elements[left : right + 1])
    segment.reverse()
    for element in segment:
        element.orientation *= -1
    molecule.elements[left : right + 1] = segment
    _update_products(molecule, channel, chemistry, definitions[channel])
    return event


def enumerate_cognate_pairs(
    molecule: Molecule,
    definitions: dict[str, PairDefinition],
) -> list[dict[str, object]]:
    """Enumerate all physical cognate site pairs and both chemistry modes."""
    rows = []
    for channel in sorted(definitions):
        sites = channel_sites(molecule, channel)
        for left, right in itertools.combinations(sites, 2):
            for chemistry in Chemistry:
                event = classify_event(molecule, channel, chemistry, definitions)
                rows.append(
                    {
                        "molecule": molecule.name,
                        "channel": channel,
                        "site_1": left.identity,
                        "site_2": right.identity,
                        "chemistry": chemistry.value,
                        "pair_state": event.pair_state,
                        "geometry": relative_orientation(left, right),
                        "outcome": event.outcome.value,
                    }
                )
    return rows


def run_round_trip(
    definitions: dict[str, PairDefinition],
    payloads: dict[str, str] | None = None,
) -> tuple[list[Molecule], list[Event]]:
    """Execute ABC followed by CBA and require exact restoration."""
    molecule = build_initial_register(definitions, payloads)
    start_sequence = molecule.sequence
    states = [deepcopy(molecule)]
    events: list[Event] = []
    for step, channel in enumerate(FORWARD_PROGRAM, start=1):
        event = apply_recombination(molecule, channel, Chemistry.INTEGRASE, definitions)
        if not event.intended:
            raise ValueError(f"Forward step {channel} failed: {event}")
        molecule.name = f"state_{step}"
        states.append(deepcopy(molecule))
        events.append(event)
    for name, channel in zip(
        ("reverse_state_2", "reverse_state_1", "restored_state_0"), REVERSE_PROGRAM, strict=False
    ):
        event = apply_recombination(molecule, channel, Chemistry.INTEGRASE_RDF, definitions)
        if not event.intended:
            raise ValueError(f"Reverse step {channel} failed: {event}")
        molecule.name = name
        states.append(deepcopy(molecule))
        events.append(event)
    if molecule.sequence != start_sequence:
        raise ValueError("Round trip did not restore the exact State 0 sequence")
    return states, events


def enumerate_orders(
    definitions: dict[str, PairDefinition],
    starting_molecule: Molecule,
    chemistry: Chemistry,
) -> list[dict[str, object]]:
    """Enumerate and classify all six input orders."""
    rows: list[dict[str, object]] = []
    for order in itertools.permutations(FORWARD_PROGRAM):
        molecule = deepcopy(starting_molecule)
        events = []
        for channel in order:
            event = apply_recombination(molecule, channel, chemistry, definitions)
            events.append(asdict(event))
            if event.outcome in {
                Outcome.DELETION,
                Outcome.AMBIGUOUS_SUBSTRATE,
                Outcome.NO_SUBSTRATE,
            }:
                break
        rows.append(
            {
                "order": "".join(order),
                "events": events,
                "completed": False,
                "terminal_outcome": events[-1]["outcome"].value if events else "none",
                "final_sha256": (
                    molecule.sha256
                    if events and all(event["outcome"] != Outcome.DELETION for event in events)
                    else None
                ),
            }
        )
    for row in rows:
        row["completed"] = len(row["events"]) == 3 and all(
            event["outcome"] == Outcome.INVERSION for event in row["events"]
        )
    return rows


def state_summary(molecule: Molecule) -> dict[str, object]:
    """Serialize a state without losing orientation or coordinates."""
    return {
        "name": molecule.name,
        "molecule_type": molecule.molecule_type.value,
        "linearization_origin": molecule.linearization_origin,
        "length_bp": len(molecule.sequence),
        "sha256": molecule.sha256,
        "physical_elements": molecule.physical_labels(),
        "payload_order": molecule.payload_order(),
        "coordinates": molecule.element_offsets(),
    }
