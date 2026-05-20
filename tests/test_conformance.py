"""QBL Test Suite — Conformance Tests for the Qubit Language Standard"""
import sys
sys.path.insert(0, 'src')

import numpy as np
import pytest


class TestQRNGPricing:
    """Chapter 12 §12.2 — Quantum Random Number Generation"""

    def setup_method(self):
        from qbl.commerce import QRNGPricingEngine
        self.engine = QRNGPricingEngine(dimension=13)

    def test_signal_range(self):
        """All signals must be in {0, ..., 12}"""
        for _ in range(100):
            signal = self.engine.generate_price_signal()
            assert 0 <= signal <= 12

    def test_uniformity_chi_squared(self):
        """QRNG passes chi-squared (df=12, α=0.05)"""
        result = self.engine.verify_randomness(2000)
        assert result['passes_uniformity'], f"Chi-squared {result['chi_squared']} > {result['chi_squared_critical_95']}"

    def test_entropy(self):
        """QRNG entropy > 3.5 bits/measurement"""
        result = self.engine.verify_randomness(2000)
        assert result['entropy_bits'] > 3.5

    def test_independence(self):
        """Sequential measurements are uncorrelated"""
        result = self.engine.verify_randomness(2000)
        assert result['passes_independence']

    def test_quantum_price_bounds(self):
        """Prices stay within volatility bounds"""
        for _ in range(50):
            p = self.engine.quantum_price(100.0, 0.06)
            assert 94.0 <= p['final_price'] <= 106.0


class TestGroverSearch:
    """Chapter 12 §12.3 — Quantum Market Search"""

    def setup_method(self):
        from qbl.commerce import QuantumMarketSearch
        self.searcher = QuantumMarketSearch(dimension=13)
        np.random.seed(42)
        self.catalog = []
        for i in range(100):
            retail = np.random.uniform(200, 5000)
            if np.random.random() < 0.1:
                price = retail * np.random.uniform(0.15, 0.40)
            else:
                price = retail * np.random.uniform(0.6, 0.95)
            self.catalog.append({
                "id": i, "title": f"Item_{i}",
                "retail_value": round(retail, 2),
                "price": round(price, 2),
            })
        self.searcher.load_catalog(self.catalog)

    def test_finds_matching_item(self):
        """Grover search finds items matching condition"""
        condition = lambda item: item["price"] < 500 and item["retail_value"] / item["price"] > 2.0
        result = self.searcher.quantum_search(condition)
        assert result['found']
        item = result['result_item']
        assert item['price'] < 500
        assert item['retail_value'] / item['price'] > 2.0

    def test_speedup_over_classical(self):
        """Achieves quadratic speedup"""
        condition = lambda item: item["price"] < 500
        result = self.searcher.quantum_search(condition)
        assert result['speedup_factor'] > 1.0


class TestQuantumCorrelation:
    """Chapter 12 §12.4 — Quantum Portfolio Correlation"""

    def setup_method(self):
        from qbl.commerce import QuantumPortfolio
        self.portfolio = QuantumPortfolio(dimension=13)

    def test_self_correlation_is_high(self):
        """Asset correlated with itself → high correlation"""
        returns = [0.01, -0.02, 0.03, 0.01, -0.01, 0.02, -0.03, 0.01, 0.02, -0.01, 0.03, -0.02, 0.01]
        self.portfolio.add_asset("A", returns)
        result = self.portfolio.quantum_correlation("A", "A")
        # Quantum correlation uses entanglement entropy — self-correlation should be highest
        assert result['quantum_correlation'] > 0.5

    def test_correlation_range(self):
        """Correlation must be in [0, 1]"""
        np.random.seed(7)
        a = np.random.normal(0, 0.1, 13).tolist()
        b = np.random.normal(0, 0.1, 13).tolist()
        self.portfolio.add_asset("X", a)
        self.portfolio.add_asset("Y", b)
        result = self.portfolio.quantum_correlation("X", "Y")
        assert 0.0 <= result['quantum_correlation'] <= 1.0


class TestQuditSimulator:
    """Chapters 1-4 — Core qudit operations"""

    def setup_method(self):
        from qbl.qudit import QuditSimulator
        self.sim = QuditSimulator(13)

    def test_dimension(self):
        assert self.sim.d == 13

    def test_shift_gate_cyclic(self):
        """SHIFT^13 = Identity"""
        from qbl.qudit import shift_gate
        S = shift_gate(13)
        result = np.linalg.matrix_power(S, 13)
        assert np.allclose(result, np.eye(13))

    def test_clock_gate_cyclic(self):
        """CLOCK^13 = Identity"""
        from qbl.qudit import clock_gate
        Z = clock_gate(13)
        result = np.linalg.matrix_power(Z, 13)
        assert np.allclose(result, np.eye(13))


class TestAgenticFramework:
    """Chapter 11 — Agentic Constructs"""

    def test_agent_creation(self):
        from qbl.agentic import QuantumAgent
        agent = QuantumAgent("test-1", "TestAgent", dimension=13)
        status = agent.status()
        assert status['name'] == "TestAgent"
        assert status['dimension'] == 13

    def test_agent_has_tools(self):
        from qbl.agentic import QuantumAgent
        agent = QuantumAgent("tool-1", "ToolAgent", dimension=13)
        status = agent.status()
        assert len(status['tools']) > 0

    def test_swarm_creation(self):
        from qbl.agentic import AgentSwarm
        swarm = AgentSwarm("TestSwarm", dimension=13)
        for i in range(3):
            swarm.add_agent(f"a{i}", f"Agent_{i}")
        status = swarm.status()
        assert status['num_agents'] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
