# MIT License
#
# Copyright (c) 2022 Quandela
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# As a special exception, the copyright holders of exqalibur library give you
# permission to combine exqalibur with code included in the standard release of
# Perceval under the MIT license (or modified versions of such code). You may
# copy and distribute such a combined system following the terms of the MIT
# license for both exqalibur and Perceval. This exception for the usage of
# exqalibur is limited to the python bindings used by Perceval.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from abc import ABC, abstractmethod
from enum import Enum

from perceval.utils import BasicState, Encoding, LogicalState
from .abstract_component import AComponent


class PortLocation(Enum):
    INPUT = 0
    OUTPUT = 1
    IN_OUT = 2


class APort(AComponent):
    def __init__(self, size, name):
        super().__init__(size, name)

    @staticmethod
    def supports_location(loc: PortLocation) -> bool:
        return True

    @abstractmethod
    def is_output_photonic_mode_closed(self):
        """
        Returns True if the photonic mode is closed by the port
        """

    @property
    def encoding(self):
        return None


class Port(APort):
    def __init__(self, encoding: Encoding, name: str):
        super().__init__(encoding.fock_length, name)
        self._encoding = encoding

    @property
    def encoding(self):
        return self._encoding

    def is_output_photonic_mode_closed(self):
        return False


class Herald(APort):
    def __init__(self, value: int, name=None):
        assert value == 0 or value == 1, "Herald value should be 0 or 1"
        self._autogenerated_name = isinstance(name, int)
        if self._autogenerated_name:
            name = f'herald{name}'
        super().__init__(1, name)
        self._value = value

    def is_output_photonic_mode_closed(self):
        return True

    @property
    def user_given_name(self):
        if self._autogenerated_name:
            return None
        return self._name

    @property
    def expected(self):
        return self._value


def get_basic_state_from_ports(ports: list[APort], state: LogicalState, add_herald_and_ancillary: bool = False) -> BasicState:
    """Convert a LogicalState to a BasicState by taking in account a port list

    :param ports: port list.
    :param state: LogicalState to convert to BasicState.
    :param add_herald_and_ancillary: add the herald and ancillary port to the basic state. Default to False.
    :return: converted BasicState.
    """
    encodings = []
    for port in ports:
        if isinstance(port, Herald):
            if add_herald_and_ancillary:
                encodings.append(port.expected)
        else:
            encodings.append(port.encoding)
    return get_basic_state_from_encoding(encodings, state)


def _to_fock(encoding: Encoding, qubit_state: list[int]) -> list[int]:
    """Return the equivalent BasicState from the qubit state, as a list of integers

    :param encoding: a qubit encoding
    :param qubit_state: logical state for the required number of qubits (only 0 or 1 values are accepted)
    :raises NotImplementedError: QUBIT and POLARIZATION encoding not currently supported
    :return: The corresponding Fock state
    """
    if encoding.logical_length != len(qubit_state):
        raise ValueError("Encoding / logical state size mismatch")
    if any(q not in [0, 1] for q in qubit_state):
        raise ValueError("Qubit value should be 0 or 1")

    if encoding == Encoding.RAW or encoding == Encoding.TIME:
        return [int(qubit_state[0])]
    elif encoding == Encoding.DUAL_RAIL:
        return [0, 1] if qubit_state[0] else [1, 0]
    elif encoding.name.startswith("QUDIT"):
        fock = [0]*encoding.fock_length
        photon_pos = sum(val*(2**idx) for idx, val in enumerate(reversed(qubit_state)))
        fock[photon_pos] = 1
        return fock
    else:
        raise NotImplementedError


def get_basic_state_from_encoding(encoding: list[Encoding | int], logical: LogicalState) -> BasicState:
    fock = []
    i = 0
    for e in encoding:
        if isinstance(e, int):
            fock.append(e)
        elif isinstance(e, Encoding):
            lsz = e.logical_length
            ls = logical[i:i+lsz]
            i += lsz
            fock += _to_fock(e, ls)
        else:
            raise TypeError(f"Unsupported type {type(e)}")
    if i != len(logical):
        raise ValueError("Encoding / logical state size mismatch")
    return BasicState(fock)
