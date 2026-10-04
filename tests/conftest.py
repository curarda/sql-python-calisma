"""Test ortamı: varsayılan olarak kullanıcı kodu süreç içinde çalışır (hızlı testler).

Gerçek alt süreç izolasyonu `gercek_sandbox` işaretli testlerde (test_sandbox.py) doğrulanır.
"""

import pytest

import sandbox


@pytest.fixture(autouse=True)
def surec_ici_sandbox(request, monkeypatch):
    if request.node.get_closest_marker("gercek_sandbox"):
        return
    monkeypatch.setattr(sandbox, "calistir", sandbox.calistir_surec_ici)
