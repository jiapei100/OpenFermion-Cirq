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

from typing import Optional, Sequence, Tuple

import numpy

import cirq
from openfermion import DiagonalCoulombHamiltonian

from openfermioncirq import CCZ, CXXYY, CYXXY, XXYY, YXXY, swap_network

from openfermioncirq.trotter.trotter_step_algorithm import (
        Hamiltonian,
        TrotterStep,
        TrotterStepAlgorithm)


class SymmetricLinearSwapNetworkTrotterStep(TrotterStep):
    """A Trotter step using two consecutive fermionic swap networks.

    This algorithm is described in arXiv:1711.04789.
    """

    def trotter_step(
            self,
            qubits: Sequence[cirq.QubitId],
            time: float,
            control_qubit: Optional[cirq.QubitId]=None
            ) -> cirq.OP_TREE:

        n_qubits = len(qubits)

        # Apply one- and two-body interactions for half of the full time
        def one_and_two_body_interaction(p, q, a, b) -> cirq.OP_TREE:
            yield XXYY(a, b)**(
                    self.hamiltonian.one_body[p, q].real * time / numpy.pi)
            yield YXXY(a, b)**(
                    self.hamiltonian.one_body[p, q].imag * time / numpy.pi)
            yield cirq.CZ(a, b)**(
                    -self.hamiltonian.two_body[p, q] * time / numpy.pi)
        yield swap_network(qubits, one_and_two_body_interaction, fermionic=True)
        qubits = qubits[::-1]

        # Apply one-body potential for the full time
        yield (cirq.Z(qubits[i])**(
                    -self.hamiltonian.one_body[i, i].real * time / numpy.pi)
               for i in range(n_qubits))

        # Apply one- and two-body interactions for half of the full time
        # This time, reorder the operations so that the entire Trotter step is
        # symmetric
        def one_and_two_body_interaction_reverse_order(p, q, a, b
                ) -> cirq.OP_TREE:
            yield cirq.CZ(a, b)**(
                    -self.hamiltonian.two_body[p, q] * time / numpy.pi)
            yield YXXY(a, b)**(
                    self.hamiltonian.one_body[p, q].imag * time / numpy.pi)
            yield XXYY(a, b)**(
                    self.hamiltonian.one_body[p, q].real * time / numpy.pi)
        yield swap_network(qubits, one_and_two_body_interaction_reverse_order,
                fermionic=True, offset=True)


class ControlledSymmetricLinearSwapNetworkTrotterStep(TrotterStep):

    def trotter_step(
            self,
            qubits: Sequence[cirq.QubitId],
            time: float,
            control_qubit: Optional[cirq.QubitId]=None
            ) -> cirq.OP_TREE:

        n_qubits = len(qubits)

        # Apply one- and two-body interactions for half of the full time
        def one_and_two_body_interaction(p, q, a, b) -> cirq.OP_TREE:
            yield CXXYY(control_qubit, a, b)**(
                    self.hamiltonian.one_body[p, q].real * time / numpy.pi)
            yield CYXXY(control_qubit, a, b)**(
                    self.hamiltonian.one_body[p, q].imag * time / numpy.pi)
            yield CCZ(control_qubit, a, b)**(
                    -self.hamiltonian.two_body[p, q] * time / numpy.pi)
        yield swap_network(
                qubits, one_and_two_body_interaction, fermionic=True)
        qubits = qubits[::-1]

        # Apply one-body potential for the full time
        yield (cirq.CZ(control_qubit, qubits[i])**(
                    -self.hamiltonian.one_body[i, i].real * time / numpy.pi)
               for i in range(n_qubits))

        # Apply one- and two-body interactions for half of the full time
        # This time, reorder the operations so that the entire Trotter step is
        # symmetric
        def one_and_two_body_interaction_reverse_order(p, q, a, b
                ) -> cirq.OP_TREE:
            yield CCZ(control_qubit, a, b)**(
                    -self.hamiltonian.two_body[p, q] * time / numpy.pi)
            yield CYXXY(control_qubit, a, b)**(
                    self.hamiltonian.one_body[p, q].imag * time / numpy.pi)
            yield CXXYY(control_qubit, a, b)**(
                    self.hamiltonian.one_body[p, q].real * time / numpy.pi)
        yield swap_network(qubits, one_and_two_body_interaction_reverse_order,
                fermionic=True, offset=True)


class AsymmetricLinearSwapNetworkTrotterStep(TrotterStep):
    """A Trotter step using one fermionic swap network.

    This algorithm is described in arXiv:1711.04789.
    """

    def trotter_step(
            self,
            qubits: Sequence[cirq.QubitId],
            time: float,
            control_qubit: Optional[cirq.QubitId]=None
            ) -> cirq.OP_TREE:

        n_qubits = len(qubits)

        # Apply one- and two-body interactions for the full time
        def one_and_two_body_interaction(p, q, a, b) -> cirq.OP_TREE:
            yield XXYY(a, b)**(
                    2 * self.hamiltonian.one_body[p, q].real * time / numpy.pi)
            yield YXXY(a, b)**(
                    2 * self.hamiltonian.one_body[p, q].imag * time / numpy.pi)
            yield cirq.CZ(a, b)**(
                    -2 * self.hamiltonian.two_body[p, q] * time / numpy.pi)
        yield swap_network(qubits, one_and_two_body_interaction, fermionic=True)
        qubits = qubits[::-1]

        # Apply one-body potential for the full time
        yield (cirq.Z(qubits[i])**(
                    -self.hamiltonian.one_body[i, i].real * time / numpy.pi)
               for i in range(n_qubits))

    def step_qubit_permutation(self,
                               qubits: Sequence[cirq.QubitId],
                               control_qubit: Optional[cirq.QubitId]=None
                               ) -> Tuple[Sequence[cirq.QubitId],
                                          Optional[cirq.QubitId]]:
        # A Trotter step reverses the qubit ordering
        return qubits[::-1], None

    def finish(self,
               qubits: Sequence[cirq.QubitId],
               n_steps: int,
               control_qubit: Optional[cirq.QubitId]=None,
               omit_final_swaps: bool=False
               ) -> cirq.OP_TREE:
        # If the number of Trotter steps is odd, possibly swap qubits back
        if n_steps & 1 and not omit_final_swaps:
            yield swap_network(qubits, fermionic=True)


class ControlledAsymmetricLinearSwapNetworkTrotterStep(TrotterStep):

    def trotter_step(
            self,
            qubits: Sequence[cirq.QubitId],
            time: float,
            control_qubit: Optional[cirq.QubitId]=None
            ) -> cirq.OP_TREE:

        n_qubits = len(qubits)

        # Apply one- and two-body interactions for the full time
        def one_and_two_body_interaction(p, q, a, b) -> cirq.OP_TREE:
            yield CXXYY(control_qubit, a, b)**(
                    2 * self.hamiltonian.one_body[p, q].real * time / numpy.pi)
            yield CYXXY(control_qubit, a, b)**(
                    2 * self.hamiltonian.one_body[p, q].imag * time / numpy.pi)
            yield CCZ(control_qubit, a, b)**(
                    -2 * self.hamiltonian.two_body[p, q] * time / numpy.pi)
        yield swap_network(qubits, one_and_two_body_interaction, fermionic=True)
        qubits = qubits[::-1]

        # Apply one-body potential for the full time
        yield (cirq.CZ(control_qubit, qubits[i])**(
                    -self.hamiltonian.one_body[i, i].real * time / numpy.pi)
               for i in range(n_qubits))

    def step_qubit_permutation(self,
                               qubits: Sequence[cirq.QubitId],
                               control_qubit: Optional[cirq.QubitId]=None
                               ) -> Tuple[Sequence[cirq.QubitId],
                                          Optional[cirq.QubitId]]:
        # A Trotter step reverses the qubit ordering
        return qubits[::-1], control_qubit

    def finish(self,
               qubits: Sequence[cirq.QubitId],
               n_steps: int,
               control_qubit: Optional[cirq.QubitId]=None,
               omit_final_swaps: bool=False
               ) -> cirq.OP_TREE:
        # If the number of Trotter steps is odd, possibly swap qubits back
        if n_steps & 1 and not omit_final_swaps:
            yield swap_network(qubits, fermionic=True)


class LinearSwapNetworkTrotterStepAlgorithm(TrotterStepAlgorithm):

    supported_types = {DiagonalCoulombHamiltonian}

    def symmetric(self, hamiltonian: Hamiltonian) -> Optional[TrotterStep]:
        return SymmetricLinearSwapNetworkTrotterStep(hamiltonian)

    def asymmetric(self, hamiltonian: Hamiltonian) -> Optional[TrotterStep]:
        return AsymmetricLinearSwapNetworkTrotterStep(hamiltonian)

    def controlled_symmetric(self, hamiltonian: Hamiltonian
                             ) -> Optional[TrotterStep]:
        return ControlledSymmetricLinearSwapNetworkTrotterStep(hamiltonian)

    def controlled_asymmetric(self, hamiltonian: Hamiltonian
                              ) -> Optional[TrotterStep]:
        return ControlledAsymmetricLinearSwapNetworkTrotterStep(hamiltonian)


LINEAR_SWAP_NETWORK = LinearSwapNetworkTrotterStepAlgorithm()