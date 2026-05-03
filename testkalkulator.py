# test_kalkulator.py

# Impor fungsi yang akan dites dari file mahasiswa
from kalkulator import tambah, kurang, kali, bagi

# Tes untuk fungsi tambah
def test_tambah():
    assert tambah(5, 3) == 8
    assert tambah(-1, 1) == 0
    assert tambah(-5, -5) == -10
    assert tambah(10, 0) == 10

# Tes untuk fungsi kurang
def test_kurang():
    assert kurang(10, 5) == 5
    assert kurang(-1, 1) == -2
    assert kurang(5, 10) == -5
    assert kurang(0, 5) == -5

# Tes untuk fungsi kali
def test_kali():
    assert kali(3, 4) == 12
    assert kali(-2, 5) == -10
    assert kali(7, 0) == 0
    assert kali(-3, -3) == 9

# Tes untuk fungsi bagi
def test_bagi():
    assert bagi(10, 2) == 5
    assert bagi(-8, 4) == -2
    assert bagi(9, 2) == 4.5

# Tes untuk kasus khusus pembagian dengan nol
def test_bagi_dengan_nol():
    assert bagi(10, 0) == "Error: Pembagian dengan nol"
    assert bagi(0, 0) == "Error: Pembagian dengan nol"
